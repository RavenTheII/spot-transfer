import os
import json
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from ytmusicapi import YTMusic
from flask import session
import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CLIENT_SECRET_JSON_ENV_VAR = "GOOGLE_CLIENT_SECRET_JSON"
GOOGLE_REDIRECT_URI_ENV_VAR = "GOOGLE_REDIRECT_URI"

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Define the SCOPES needed for YouTube Music API
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

# File where the credentials will be saved
CREDENTIALS_FILE = 'token.json'


def load_google_client_config():
    """Loads Google client secrets from env var or file."""
    client_config_json = os.getenv(GOOGLE_CLIENT_SECRET_JSON_ENV_VAR)
    if client_config_json:
        try:
            return json.loads(client_config_json)
        except json.JSONDecodeError:
            # Log this error appropriately
            print("Error: Could not parse GOOGLE_CLIENT_SECRET_JSON.")
            # Fallback to file if env var is malformed
            pass  # Will try loading from file next

    try:
        with open('client_secret.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Log this error appropriately
        print("Error: client_secret.json not found.")
        raise Exception("Google client configuration not found.")
    except json.JSONDecodeError:
        # Log this error appropriately
        print("Error: Could not parse client_secret.json.")
        raise Exception("Error parsing Google client configuration.")


def authenticate_youtube():
    """Loads existing Google credentials from session or token.json."""
    creds_json_str = session.get('google_creds')
    creds = None

    if creds_json_str:
        try:
            creds_data = json.loads(creds_json_str)
            creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
        except json.JSONDecodeError:
            print("Error decoding credentials from session.")
            session.pop('google_creds', None) # Clear invalid data

    if not creds and os.path.exists(CREDENTIALS_FILE):
        try:
            creds = Credentials.from_authorized_user_file(CREDENTIALS_FILE, SCOPES)
        except Exception as e: # Broad exception for file corruption issues
            print(f"Error loading credentials from {CREDENTIALS_FILE}: {e}")
            # Optionally, delete or rename the corrupted token file here

    if creds:
        if creds.valid:
            # Save to session if loaded from file for next time
            if not creds_json_str:
                session['google_creds'] = creds.to_json()
            return creds
        elif creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                session['google_creds'] = creds.to_json()
                # Also update token.json if it was the source or for fallback
                with open(CREDENTIALS_FILE, 'w') as token:
                    token.write(creds.to_json())
                return creds
            except Exception as e:
                print(f"Error refreshing token: {e}")
                # Clear potentially invalid credentials from session and file
                session.pop('google_creds', None)
                if os.path.exists(CREDENTIALS_FILE):
                    try:
                        os.remove(CREDENTIALS_FILE)
                    except OSError as ose:
                        print(f"Error removing corrupted token file: {ose}")
                return None
    return None


def generate_google_auth_url():
    """Generates Google OAuth2 authorization URL and state."""
    client_config = load_google_client_config()
    redirect_uri = os.getenv(GOOGLE_REDIRECT_URI_ENV_VAR, 'http://localhost:8080/callback')
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent'  # Or 'select_account' if you want to allow account switching
    )
    session['oauth_state'] = state
    return authorization_url, state


def exchange_code_for_credentials(authorization_code):
    """Exchanges authorization code for credentials and stores them.
    Assumes 'oauth_state' has been verified by the caller and removed from session."""
    # The 'oauth_state' should have been verified by the caller (main.py's /callback route)
    # and removed from the session before this function is called.

    client_config = load_google_client_config()
    redirect_uri = os.getenv(GOOGLE_REDIRECT_URI_ENV_VAR, 'http://localhost:8080/callback')
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    flow.fetch_token(code=authorization_code)
    creds = flow.credentials

    session['google_creds'] = creds.to_json()
    with open(CREDENTIALS_FILE, 'w') as token_file:
        token_file.write(creds.to_json())

    return creds
    

def get_spotify_access_token():
    """Fetches a fresh Spotify access token"""
    url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET
    }
    
    response = requests.post(url, data=data)
    response_json = response.json()

    print(f"Spotify Access Token Response: {response_json}")  # Print the response for debugging
    
    if "access_token" not in response_json:
        raise Exception("Failed to get Spotify access token")
    
    return response_json["access_token"]

def get_all_tracks(playlist_link):
    """Fetches all tracks from the given Spotify playlist URL"""
    access_token = get_spotify_access_token()
    
    # Extract the playlist ID from the URL
    playlist_id = playlist_link.split("/")[-1].split("?")[0]
    
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    tracks = []
    while url:
        response = requests.get(url, headers=headers)
        response_json = response.json()

        # Check for errors in the response
        if response.status_code != 200:
            print(f"Failed to fetch tracks: {response_json}")
            raise Exception("Failed to fetch tracks from Spotify.")
        
        # Add tracks from the current response page
        for item in response_json["items"]:
            track = item["track"]
            track_name = track["name"]
            artist_name = track["artists"][0]["name"]  # Get the first artist
            
            tracks.append({"name": track_name, "artists": [artist_name]})
        
        # Check if there's a next page of results
        url = response_json.get("next")  # Get the URL for the next page, if available
    
    return tracks

def get_playlist_name(playlist_link):
    """Fetches the name of the playlist from the Spotify link"""
    access_token = get_spotify_access_token()

    # Extract the playlist ID from the URL
    playlist_id = playlist_link.split("/")[-1].split("?")[0]

    url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, headers=headers)
    response_json = response.json()

    # Extract playlist name from the response
    playlist_name = response_json.get("name", "Untitled Playlist")

    return playlist_name

def get_video_ids(ytmusic, tracks):
    video_ids = []
    missed_tracks = {
        "count": 0,
        "tracks": []
    }
    for track in tracks:
        try:
            search_string = f"{track['name']} {track['artists'][0]}"
            video_id = ytmusic.search(search_string, filter="songs")[0]["videoId"]
            video_ids.append(video_id)
        except Exception:
            print(f"{track['name']} {track['artists'][0]} not found on YouTube Music")
            missed_tracks["count"] += 1
            missed_tracks["tracks"].append(f"{track['name']} {track['artists'][0]}")
    print(f"Found {len(video_ids)} songs on YouTube Music")
    if len(video_ids) == 0:
        raise Exception("No songs found on YouTube Music")
    return video_ids, missed_tracks

def create_ytm_playlist(playlist_link):
    print("Starting YouTube Music playlist creation")
    creds = authenticate_youtube()

    if not creds:
        raise Exception("Authentication required. Please login via the web interface.")

    # Construct auth headers from credentials
    auth_headers = {"Authorization": f"Bearer {creds.token}"}
    
    # Initialize YTMusic by passing authentication headers directly
    # YTMusic constructor accepts 'auth' parameter with headers as a JSON string or dict
    # Based on ytmusicapi docs, it can take headers string. Let's ensure it's a string.
    ytmusic = YTMusic(auth=json.dumps(auth_headers))
    
    # Get all the tracks from the Spotify playlist (this is just a simulation)
    tracks = get_all_tracks(playlist_link)
    name = get_playlist_name(playlist_link)  # Extract the name of the playlist
    
    print(f"Got {len(tracks)} tracks from the Spotify playlist")
    
    # 4. Search for each track on YouTube Music and get the video IDs
    video_ids, missed_tracks = get_video_ids(ytmusic, tracks)
    print(f"Found {len(video_ids)} tracks on YouTube Music")
    
    # 5. Create the playlist on YouTube Music with the found video IDs
    ytmusic.create_playlist(name, "", "PRIVATE", video_ids)
    print(f"Playlist '{name}' created with {len(video_ids)} tracks.")
    
    # 6. Return the missed tracks (if any)
    return missed_tracks
