# SpotTransfer

## Overview

A tool to transfer Spotify playlists to YouTube Music.

## Usage

Follow the instructions at https://spot-transfer.vercel.app

### Self Host

1. Clone the repository
2. Navigate to the `backend` directory in the terminal
    ```bash
    cd backend/
    ```
3. Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4. Create an `.env` file in the `backend` directory and add the following: (you can get the client id and secret from the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/))
    ```env
    SPOTIPY_CLIENT_ID=your_spotify_client_id
    SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
    ```
5. Go to `selfhost.py`
6. Replace the playlist name and link with the `playlist_name` and `spotify_playlist_link` variables in the `SETUP` section at the top. **Ignore the headers for now**

    ```python
    #### SETUP
     playlist_name = "Replace this with the playlist name you wish to create"

     spotify_playlist_link = "Replace this with the spotify playlist link"

     headers = '''
     delete this line and paste the headers here
     '''

     ####
    ```

7. Run the file:

    ```bash
    python selfhost.py
    ```

8. Follow the instructions at [spot-transfer.vercel.app/create-playlist](https://spot-transfer.vercel.app/create-playlist) to get the headers and paste them in the `headers` variable in the `SETUP` section (refer step 5).
9. In the `selfhost.py` file, comment the `selfhost_get_vids()` function call and uncomment the `selfhost_create_playlist()` function call.
    ```python
     # selfhost_get_vids() # comment this out after running once
     selfhost_make_playlist() # uncomment this when running the second time
    ```
