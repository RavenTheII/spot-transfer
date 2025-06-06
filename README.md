# Spotify to YouTube Music Playlist Transfer

This application allows users to transfer their Spotify playlists to YouTube Music. It uses the Spotify API to fetch playlist data and the YouTube Music API (via `ytmusicapi`) to create new playlists. Authentication with Google is handled via an OAuth 2.0 web server flow to authorize access to the user's YouTube Music account.

## Features

-   Transfer Spotify playlists to YouTube Music.
-   Secure Google Account login/logout for YouTube Music authorization using OAuth 2.0.
-   Frontend built with React
-   Backend built with Flask (Python)

## Prerequisites

-   Python 3.9+
-   Node.js (e.g., v18+) and npm (or yarn)
-   A Google Cloud Platform account (for YouTube Data API v3 credentials).
-   A Spotify Developer account (for Spotify Web API credentials).

## Setup & Local Development

### Backend Setup

Navigate to the `backend` directory: `cd backend`

1.  **Create and activate a Python virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Google OAuth Credentials:**
    -   Go to the [Google Cloud Console](https://console.cloud.google.com/).
    -   Create a new project or select an existing one.
    -   In the navigation menu, go to "APIs & Services" > "Enabled APIs & services".
    -   Click "+ ENABLE APIS AND SERVICES", search for "YouTube Data API v3", and enable it.
    -   Go to "APIs & Services" > "Credentials".
    -   Click "+ CREATE CREDENTIALS", then choose "OAuth client ID".
    -   Select "Web application" as the application type.
    -   Give it a name (e.g., "Spotify to YTM Transfer App - Local").
    -   **Authorized redirect URIs**: Add the following (adjust port if necessary):
        -   `http://localhost:8080/callback` (for local development)
        -   `https://your-app-name.onrender.com/callback` or `https://your-app-name.vercel.app/callback`
    -   Click "CREATE". You will see a client ID and client secret. Click "DOWNLOAD JSON" to get the    client secret file.
    -   Move the downloaded `client_secret.json` file to the `backend` directory.

4.  **Environment Variables (Backend):**
    -   Create a `.env` file in the `backend` directory (i.e., `backend/.env`).
    -   Add the following, replacing placeholders with your actual values:

    ```env
    FLASK_SECRET_KEY=your_strong_random_secret_key_for_flask_sessions

    # --- Google OAuth ---
    # If using client_secret.json file, you might not need GOOGLE_CLIENT_SECRET_JSON.
    # If NOT using the file, paste the entire JSON content here:
    # GOOGLE_CLIENT_SECRET_JSON='{"web":{"client_id":"YOUR_CLIENT_ID.apps.googleusercontent.com","project_id":"YOUR_PROJECT_ID",...}}'

    # This MUST match one of the URIs you registered in the Google Cloud Console for your OAuth client.
    GOOGLE_REDIRECT_URI=http://localhost:8080/callback

    # --- Spotify API Credentials ---
    SPOTIFY_CLIENT_ID=your_spotify_client_id
    SPOTIFY_CLIENT_SECRET=your_spotify_client_secret

    # --- Frontend URL ---
    # Used by the backend to redirect back to the frontend after OAuth.
    FRONTEND_URL=http://localhost:5173
    ```

5.  **Running the Backend:**
    From the `backend` directory:
    ```bash
    python main.py
    ```
    The backend will typically run on `http://localhost:8080`.

### 4.3. Frontend Setup

Navigate to the `frontend` directory: `cd ../frontend` 

1.  **Install dependencies:**
    ```bash
    npm install
    ```

2.  **Environment Variables (Frontend):**
    -   Create a `.env` file in the `frontend` directory (i.e., `frontend/.env`).
    -   Add the following:
    ```env
    VITE_API_URL=http://localhost:8080
    ```
    This tells your frontend where the backend API is running.

3.  **Running the Frontend:**
    ```bash
    npm run dev
    ```
    Or if you use yarn:
    ```bash
    yarn dev
    ```
    The frontend development server will typically run on `http://localhost:5173`. Open this URL in your browser.

