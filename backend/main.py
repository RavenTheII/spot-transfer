from flask import Flask, request, jsonify, session, redirect
from flask import send_from_directory
from flask_cors import CORS
from ytm import create_ytm_playlist, generate_google_auth_url, exchange_code_for_credentials, authenticate_youtube
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="dist")

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, "index.html")

#CORS(app, resources={r"/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"] + os.getenv("FRONTEND_URL", "").split(","), "methods": ["POST", "GET", "OPTIONS"], "supports_credentials": True}})
CORS(app,
     resources={r"/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"] + os.getenv("FRONTEND_URL", "").split(","), "methods": ["POST", "GET", "OPTIONS"]}},
     supports_credentials=True)

app.secret_key = os.getenv("FLASK_SECRET_KEY")
if not app.secret_key:
    raise ValueError("No FLASK_SECRET_KEY set for Flask application. Please set it in .env")

#Configure session cookie settings for security and cross-site compatibility stuff
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='None',
)


@app.route('/login/google', methods=['GET'])
def login_google():
    try:
        authorization_url, state = generate_google_auth_url()
        return redirect(authorization_url)
    except Exception as e:
        print(f"Error during Google login initiation: {e}")
        return jsonify({"error": "Failed to initiate Google login."}), 500


@app.route('/callback', methods=['GET'])
def callback():
    state_from_google = request.args.get('state')
    code = request.args.get('code')
    error = request.args.get('error')

    if error:
        return jsonify({"error": f"OAuth error: {error}"}), 400

    expected_state = session.get('oauth_state')

    if not code:
        return jsonify({"error": "Authorization code not found in callback."}), 400

    if not expected_state:
        return jsonify({"error": "OAuth state not found in session. Please try logging in again."}), 400

    if state_from_google != expected_state:
        return jsonify({"error": "OAuth state mismatch. CSRF attack suspected or session issue."}), 400

    session.pop('oauth_state', None)

    try:
        exchange_code_for_credentials(code)
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
        return redirect(frontend_url + '/#auth_success')
    except Exception as e:
        print(f"Error exchanging code for credentials: {e}")
        session.pop('google_creds', None)
        session.pop('oauth_state', None)
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
        return redirect(frontend_url + '/#auth_failure')


@app.route('/create', methods=['POST'])
def create_playlist():
    creds = authenticate_youtube()
    if not creds:
        return jsonify({"error": "Authentication required", "login_url": "/login/google"}), 401

    data = request.get_json()
    playlist_link = data.get('playlist_link')

    if not playlist_link:
        return jsonify({"error": "No playlist link provided"}), 400

    try:
        missed_tracks = create_ytm_playlist(playlist_link)
        if missed_tracks["count"] > 0:
            return jsonify({
                "message": f"Playlist created, but {missed_tracks['count']} tracks were not found on YouTube Music.",
                "missed_tracks": missed_tracks["tracks"]
            }), 200
        return jsonify({"message": "Playlist successfully created on YouTube Music!"}), 200
    except Exception as e:
        print(f"Error in /create endpoint: {e}")
        if "Authentication required" in str(e): 
             return jsonify({"error": "Authentication required", "login_url": "/login/google"}), 401
        return jsonify({"error": "Something went wrong with the playlist transfer."}), 500


@app.route('/', methods=['GET'])
def home():
    return {"message": "Server Online"}, 200

@app.route('/logout', methods=['POST'])
def logout():
    #remove Google credententials
    session.pop('google_creds', None)
    session.pop('oauth_state', None)

    #clear entire session
    # session.clear()

    if os.path.exists('token.json'):
        try:
            os.remove('token.json')
        except OSError as e:
            print(f"Error removing token.json: {e}")
  
    return jsonify({"message": "Logged out successfully"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)), debug=os.getenv('FLASK_ENV') == 'development')
