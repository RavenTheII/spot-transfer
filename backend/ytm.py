import os
import json
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from ytmusicapi import YTMusic
from flask import session
import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CLIENT_SECRET_JSON_ENV_VAR = "GOOGLE_CLIENT_SECRET_JSON"
GOOGLE_REDIRECT_URI_ENV_VAR = "GOOGLE_REDIRECT_URI"

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# YouTube Data API requires 'youtube' scope for creating/managing playlists
SCOPES = ['https://www.googleapis.com/auth/youtube']
# Limit how many tracks we process per run to stay under daily quota
MAX_TRACKS_PER_TRANSFER = int(os.getenv("MAX_TRACKS_PER_TRANSFER", "180"))

#file where credentials are stored
CREDENTIALS_FILE = 'token.json'


def load_google_client_config():
    """Loads Google client secrets from environment or file.
    Supports either:
      - GOOGLE_CLIENT_SECRET_JSON (full JSON string)
      - GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET (+ GOOGLE_REDIRECT_URI/REDIRECT_URI)
      - client_secret.json file fallback
    """
    # 1) Full JSON in env
    client_config_json = os.getenv("GOOGLE_CLIENT_SECRET_JSON")
    if client_config_json:
        try:
            return json.loads(client_config_json)
        except json.JSONDecodeError:
            print("Error: Could not parse GOOGLE_CLIENT_SECRET_JSON; falling back to ID/SECRET or file.")

    # 2) Build from ID/SECRET in env
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI") or os.getenv("REDIRECT_URI") or "http://localhost:8080/callback"
    if client_id and client_secret:
        return {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
                "javascript_origins": []
            }
        }

    # 3) Fallback to file
    try:
        with open('client_secret.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: client_secret.json not found and GOOGLE_CLIENT_* envs not set.")
        raise Exception("Google client configuration not found. Set GOOGLE_CLIENT_SECRET_JSON or GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET.")
    except json.JSONDecodeError:
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
            session.pop('google_creds', None) #clear invalid data

    if not creds and os.path.exists(CREDENTIALS_FILE):
        try:
            creds = Credentials.from_authorized_user_file(CREDENTIALS_FILE, SCOPES)
        except Exception as e: 
            print(f"Error loading credentials from {CREDENTIALS_FILE}: {e}")
            
    if creds:
        if creds.valid:
            if not creds_json_str:
                session['google_creds'] = creds.to_json()
            return creds
        elif creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                session['google_creds'] = creds.to_json()
                with open(CREDENTIALS_FILE, 'w') as token:
                    token.write(creds.to_json())
                return creds
            except Exception as e:
                print(f"Error refreshing token: {e}")
                #clear invalid credentials from session + file
                session.pop('google_creds', None)
                if os.path.exists(CREDENTIALS_FILE):
                    try:
                        os.remove(CREDENTIALS_FILE)
                    except OSError as ose:
                        print(f"Error removing corrupted token file: {ose}")
                return None
    return None


def generate_google_auth_url():
    client_config = load_google_client_config()
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI") or os.getenv("REDIRECT_URI") or 'http://localhost:8080/callback'
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent' 
    )
    session['oauth_state'] = state
    return authorization_url, state


def exchange_code_for_credentials(authorization_code):
 
    client_config = load_google_client_config()
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI") or os.getenv("REDIRECT_URI") or 'http://localhost:8080/callback'
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

    print(f"Spotify Access Token Response: {response_json}")
    
    if "access_token" not in response_json:
        raise Exception("Failed to get Spotify access token")
    
    return response_json["access_token"]

def get_all_tracks(playlist_link):
    """Fetches all tracks from the given Spotify playlist URL"""
    access_token = get_spotify_access_token()
    
    #get the playlist ID from the URL
    playlist_id = playlist_link.split("/")[-1].split("?")[0]
    
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    tracks = []
    while url:
        response = requests.get(url, headers=headers)
        response_json = response.json()

        if response.status_code != 200:
            print(f"Failed to fetch tracks: {response_json}")
            raise Exception("Failed to fetch tracks from Spotify.")

        for item in response_json["items"]:
            track = item["track"]
            track_name = track["name"]
            artist_name = track["artists"][0]["name"] #get the first artist
            
            tracks.append({"name": track_name, "artists": [artist_name]})

        url = response_json.get("next") 
    
    return tracks

def get_playlist_name(playlist_link):
    """Fetches the name of the playlist from the Spotify link"""
    access_token = get_spotify_access_token()

    #extract the playlist ID from the URL
    playlist_id = playlist_link.split("/")[-1].split("?")[0]

    url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(url, headers=headers)
    response_json = response.json()

    #extract playlist name from the response
    playlist_name = response_json.get("name", "Untitled Playlist")

    return playlist_name

def get_video_ids(tracks):
    video_ids = []
    missed_tracks = {"count": 0, "tracks": []}
    ytmusic = YTMusic()
    for track in tracks:
        query = f"{track['name']} {track['artists'][0]}"
        try:
            results = ytmusic.search(query, filter="songs")
            if not results:
                results = ytmusic.search(query, filter="videos")
            if results:
                video_id = results[0].get("videoId")
                if video_id:
                    video_ids.append(video_id)
                    continue
            print(f"{query} not found on YouTube Music")
            missed_tracks["count"] += 1
            missed_tracks["tracks"].append(query)
        except Exception as e:
            print(f"Error searching for '{query}': {e}")
            missed_tracks["count"] += 1
            missed_tracks["tracks"].append(query)
    print(f"Found {len(video_ids)} videos via ytmusicapi")
    if len(video_ids) == 0:
        raise Exception("No songs found on YouTube")
    return video_ids, missed_tracks

def create_ytm_playlist(playlist_link):
    print("Starting YouTube playlist creation via Data API")
    creds = authenticate_youtube()

    if not creds:
        raise Exception("Authentication required. Please login via the web interface.")

    # Initialize YouTube Data API client
    youtube = build('youtube', 'v3', credentials=creds)

    # Get tracks and playlist name
    tracks = get_all_tracks(playlist_link)
    name = get_playlist_name(playlist_link)
    print(f"Got {len(tracks)} tracks from the Spotify playlist")

    # Determine how many tracks to process this run (quota-friendly)
    max_per_run = MAX_TRACKS_PER_TRANSFER
    selected_tracks = tracks[:max_per_run]
    remaining = max(0, len(tracks) - len(selected_tracks))
    if remaining > 0:
        print(f"Limiting transfer to first {len(selected_tracks)} tracks due to MAX_TRACKS_PER_TRANSFER={max_per_run}; {remaining} remaining.")

    # Create the playlist first to fail fast on permission issues
    playlist_response = youtube.playlists().insert(
        part='snippet,status',
        body={
            'snippet': {
                'title': name,
                'description': ''
            },
            'status': {
                'privacyStatus': 'private'
            }
        }
    ).execute()
    playlist_id = playlist_response['id']
    print(f"Created playlist '{name}' with ID {playlist_id}")

    # Find video IDs via ytmusicapi (quota-friendly)
    video_ids, missed_tracks = get_video_ids(selected_tracks)
    print(f"Found {len(video_ids)} tracks via ytmusicapi")

    # Add each video to the playlist
    for vid in video_ids:
        try:
            youtube.playlistItems().insert(
                part='snippet',
                body={
                    'snippet': {
                        'playlistId': playlist_id,
                        'resourceId': {
                            'kind': 'youtube#video',
                            'videoId': vid
                        }
                    }
                }
            ).execute()
        except Exception as e:
            print(f"Failed to add video {vid} to playlist {playlist_id}: {e}")

    print(f"Playlist '{name}' populated with {len(video_ids)} videos.")

    # Include partial transfer info if we limited tracks
    if remaining > 0:
        missed_tracks["skipped_due_to_limit"] = remaining
        missed_tracks["processed_count"] = len(selected_tracks)
        missed_tracks["total_count"] = len(tracks)

    # Return missed tracks (if any)
    return missed_tracks
