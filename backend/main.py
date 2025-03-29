from flask import Flask, request, jsonify
from flask_cors import CORS
from ytm import create_ytm_playlist
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "methods": ["POST", "GET"]}})

@app.route('/create', methods=['POST'])
def create_playlist():
    # 1. Get the playlist link from the incoming POST request
    data = request.get_json()  # Get JSON data from the request
    playlist_link = data.get('playlist_link')  # Extract the playlist link

    if not playlist_link:
        return jsonify({"error": "No playlist link provided"}), 400  # Return an error if no link was provided

    try:
        # 2. Call the function to create the YouTube Music playlist
        # This function will handle authentication and transferring the playlist
        missed_tracks = create_ytm_playlist(playlist_link)

        # 3. After the playlist is created, check for missed tracks (if any)
        if missed_tracks["count"] > 0:
            # If some tracks were missed, return a message with the missed tracks
            return jsonify({
                "message": f"Playlist created, but {missed_tracks['count']} tracks were not found on YouTube Music.",
                "missed_tracks": missed_tracks["tracks"]
            }), 200

        # 4. If all tracks were transferred successfully, return a success message
        return jsonify({"message": "Playlist successfully created on YouTube Music!"}), 200

    except Exception as e:
        print(e)  # Log the error (optional)
        return jsonify({"error": "Something went wrong with the playlist transfer."}), 500


@app.route('/', methods=['GET'])
def home():
    # Render health check endpoint
    return {"message": "Server Online"}, 200

if __name__ == '__main__':
    app.run(port=8080)
