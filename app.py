#import libraries
from flask import Flask, redirect, request, session, url_for
import spotipy
from spotipy.oauth2 import SpotifyOAuth

#initialise Flask app and encrypt
app = Flask(__name__)
app.secret_key = "hakunamatata"

#Spotify API credentials
SPOTIPY_CLIENT_ID = "371b6e2df4a940e38fd01fa99a5b34e8"
SPOTIPY_CLIENT_SECRET = "bf816dae18e14f1289af17218c05fc52"
SPOTIPY_REDIRECT_URI = "http://localhost:5000/callback"

#handles authentication flow and access to data
sp_oauth = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                        client_secret=SPOTIPY_CLIENT_SECRET,
                        redirect_uri=SPOTIPY_REDIRECT_URI,
                        scope="user-library-read user-top-read playlist-read-private")

#defines the root route of the app (login)
@app.route('/')
def login():
    #generate the URL for the user to login
    auth_url = sp_oauth.get_authorize_url()
    #redirect user to the login page
    return redirect(auth_url)

#redirect user after they log in
@app.route('/callback')
def callback():
    #spotify sends back a temporary code to exchange for an access token
    token_info = sp_oauth.get_access_token(request.args['code'])
    #store the token in the session
    session['token_info'] = token_info
    #redirect user to their profile
    return redirect(url_for('profile'))

#displays user info once they are logged in
@app.route('/profile')
def profile():
    #retrieve access token from session
    token_info = session.get('token_info', None)
    #if token is not found, redirect to login
    if not token_info:
        return redirect('/')
    #create a spotify object to make reequests on behalf od the user
    sp = spotipy.Spotify(auth=token_info['access_token'])
    #get current user data like name
    user_data = sp.current_user()
    #display username so user knows they are logged in
    return f'Logged in as {user_data["display_name"]}'

if __name__ == "__main__":
    app.run(debug=True)





