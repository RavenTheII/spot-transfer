from ytmusicapi import YTMusic
import ytmusicapi
from spotify import get_all_tracks, get_playlist_name
import time


#### SETUP
playlist_name = "Replace this with the playlist name you wish to create"

spotify_playlist_link = "Replace this with the spotify playlist link"

headers = '''
delete this line and paste the headers here
'''

####

def get_video_ids(ytmusic,tracks):
    video_ids = []
    missed_tracks = []
    index = 1
    start_time = time.time()
    print(f"Searching for {len(tracks)} songs on YouTube Music")
    
    for track in tracks:
        try :
            print(f"Searching for song {index}/{len(tracks)}")
            index += 1
            search_string = f"{track['name']} {track['artists'][0]}"
            video_id = ytmusic.search(search_string, filter="songs")[0]["videoId"]
            video_ids.append(video_id)
        except :
            print(f"{track['name']} {track['artists'][0]} not found on YouTube Music")
            missed_tracks.append(f"{track['name']} {track['artists'][0]}")
    
    total_time = time.time() - start_time
    print(f"Found {len(video_ids)}/{len(tracks)} songs on YouTube Music in {total_time:.2f} seconds. {len(tracks) - len(video_ids)} songs not found.")
    
    if len(video_ids) == 0:
        raise Exception("No songs found on YouTube Music")
    return video_ids


def create_ytm_playlist(playlist_link, headers):
    ytmusicapi.setup(filepath="header_auth.json", headers_raw=headers)
    ytmusic = YTMusic("header_auth.json")
    tracks = get_all_tracks(playlist_link, "IN")
    name = get_playlist_name(playlist_link)
    video_ids = get_video_ids(ytmusic, tracks)
    
    ytmusic.create_playlist(name, "", "PRIVATE", video_ids)

def selfhost_make_playlist():
    ytmusicapi.setup(filepath="browser.json", headers_raw=headers)
    ytmusic = YTMusic("browser.json")
    # tracks = get_all_tracks(spotify_playlist_link, "IN")
    name = playlist_name
    # video_ids = get_video_ids(ytmusic, tracks)
    # with open('video_ids.txt', 'w') as f:
    #     for video_id in video_ids:
    #         f.write(video_id + '\n')
    with open('video_ids.txt', 'r') as f:
        video_ids = [line.strip() for line in f.readlines()]
        ytmusic.create_playlist(name, "", "PRIVATE", video_ids)
    
def selfhost_get_vids():
    ytmusic = YTMusic()
    tracks = get_all_tracks(spotify_playlist_link, "IN")
    video_ids = get_video_ids(ytmusic, tracks)
    with open('video_ids.txt', 'w') as f:
        for video_id in video_ids:
            f.write(video_id + '\n')
    
    
selfhost_get_vids() # comment this out after running once
# selfhost_make_playlist() # uncomment this when running the second time