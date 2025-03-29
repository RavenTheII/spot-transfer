import os
import json
import time
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from ytmusicapi import YTMusic
from google_auth_oauthlib.flow import InstalledAppFlow
import requests
from dotenv import load_dotenv

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Define the SCOPES needed for YouTube Music API
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

# File where the credentials will be saved
CREDENTIALS_FILE = 'token.json'

# Set your redirect URI
REDIRECT_URI = "http://localhost:5000/callback"

def authenticate_youtube():
    """Automates the OAuth flow to authenticate and get access headers"""
    creds = None
    if os.path.exists(CREDENTIALS_FILE):
        creds = Credentials.from_authorized_user_file(CREDENTIALS_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            creds = flow.run_local_server(port=8081, redirect_uri_trailing_slash=False)

        with open(CREDENTIALS_FILE, 'w') as token:
            token.write(creds.to_json())

    headers = {"Authorization": f"Bearer {creds.token}"}
    return headers

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
    
    # 1. Authenticate with YouTube Music and get the credentials (this handles OAuth)
    headers = authenticate_youtube()
    print("Authenticated with YouTube Music")

    # 2. Initialize YTMusic properly (without passing headers directly)
    ytmusic = YTMusic("headers.json")  # YTMusic accepts a file path to the headers file
    
    # You might need to create a "headers.json" file using the headers you got from the OAuth process.
    # Save the headers to "headers.json"
    with open("headers.json", "w") as f:
        json.dump(headers, f)
    
    # 3. Get all the tracks from the Spotify playlist (this is just a simulation)
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
