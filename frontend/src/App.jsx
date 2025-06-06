import React, { useState, useEffect } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

function App() {
  const [playlistLink, setPlaylistLink] = useState('');
  const [status, setStatus] = useState('idle');
  const [message, setMessage] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const hash = window.location.hash;
    if (hash.includes('#auth_success')) {
      setMessage('✅ Successfully logged in with Google!');
      setIsLoggedIn(true);
      setStatus('success');
      window.location.hash = ''; //clear the hash
    } else if (hash.includes('#auth_failure')) {
      setMessage('❌ Google login failed. Please try again.');
      setIsLoggedIn(false);
      setStatus('error'); 
      window.location.hash = ''; 
    }
  }, []);

  const handleTransfer = async () => {
    if (!playlistLink.trim()) {
      setMessage("Please enter a playlist link.");
      setStatus("error");
      return;
    }

    setStatus('loading');
    setMessage('');

    try {
      const response = await fetch(`${API_BASE_URL}/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ playlist_link: playlistLink }),
        credentials: 'include',
      });

      const data = await response.json();

      if (response.ok) {
        setStatus('success');
        setMessage(`✅ ${data.message || 'Playlist transferred successfully!'}`);
        if (data.missed_tracks && data.missed_tracks.length > 0) {
          setMessage(prevMessage => `${prevMessage} Some tracks were not found: ${data.missed_tracks.join(', ')}`);
        }
      } else {
        setStatus('error');
        setMessage(`❌ Error: ${data.error || "Something went wrong."}`);
        if (response.status === 401) {
          setIsLoggedIn(false);
          setMessage("❌ Authentication required. Please log in.");
        }
      }
    } catch (err) {
      setStatus('error');
      setMessage('❌ Failed to connect to the server.');
    }
  };

  const handleLogin = () => {
    window.location.href = `${API_BASE_URL}/login/google`;
  };

  const handleLogout = async () => {
    setStatus('loading');
    setMessage('');
    try {
      const res = await fetch(`${API_BASE_URL}/logout`, {
        method: 'POST',
        credentials: 'include',
      });
      const data = await res.json();
  
      if (res.ok) {
        setStatus("success");
        setMessage("✅ Logged out successfully!");
        setPlaylistLink('');
        setIsLoggedIn(false);
      } else {
        setStatus("error");
        setMessage(`❌ Logout failed: ${data.error || "Unknown error"}`);
      }
    } catch (err) {
      setStatus("error");
      setMessage("❌ Could not contact the server to log out.");
    }
  };

  return (
    <div style={{
      position: 'relative',
      minHeight: '100vh',
      minWidth: '100vw',
      backgroundColor: '#f0f0f0', 
      fontFamily: 'Arial, sans-serif',
      color: '#333',
      padding: '20px', 
      boxSizing: 'border-box',
    }}>
      <div style={{
        position: 'absolute',
        top: '20px',
        right: '20px',
      }}>
        {isLoggedIn ? (
          <button
            onClick={handleLogout}
            style={{
              backgroundColor: '#d9534f', 
              color: '#fff',
              border: 'none',
              borderRadius: '5px',
              padding: '10px 18px',
              fontSize: '1rem',
              cursor: 'pointer',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            }}
          >
            Log Out
          </button>
        ) : (
          <button
            onClick={handleLogin}
            style={{
              backgroundColor: '#4285F4',
              color: '#fff',
              border: 'none',
              borderRadius: '5px',
              padding: '10px 18px',
              fontSize: '1rem',
              cursor: 'pointer',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            }}
          >
            Login with Google
          </button>
        )}
      </div>

      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        flexDirection: 'column',
        paddingTop: isLoggedIn ? '80px' : '120px',
        textAlign: 'center',
      }}>
        <h1 style={{ fontSize: '2.2rem', marginBottom: '1.5rem' }}>
          <span style={{ color: '#1DB954' }}>Spotify</span> to <span style={{ color: '#FF0000' }}>YouTube Music</span> Transfer
        </h1>

        {message && ( 
          <p style={{
            fontSize: '1.1rem',
            margin: '20px 0',
            padding: '10px',
            borderRadius: '5px',
            backgroundColor: status === 'success' ? '#dff0d8' : (status === 'error' ? '#f2dede' : '#f0f0f0'),
            color: status === 'success' ? '#3c763d' : (status === 'error' ? '#a94442' : '#333'),
            border: `1px solid ${status === 'success' ? '#d6e9c6' : (status === 'error' ? '#ebccd1' : '#ccc')}`,
            maxWidth: '80%',
            wordBreak: 'break-word',
          }}>
            {message}
          </p>
        )}

        {!isLoggedIn && (
          <p style={{ fontSize: '1.2rem', marginTop: '50px', color: '#555' }}>
            Please log in with your Google account to transfer playlists.
          </p>
        )}

        {isLoggedIn && (
          <>
            <p style={{ fontSize: '1.2rem', marginBottom: '1rem' }}>
              Paste your Spotify playlist link below and click transfer:
            </p>

            <input
              type="text"
              value={playlistLink}
              onChange={(e) => setPlaylistLink(e.target.value)}
              placeholder="Paste Spotify Playlist Link"
              style={{
                width: '70%', 
                maxWidth: '500px', 
                padding: '12px', 
                borderRadius: '5px',
                border: '1px solid #ccc',
                marginBottom: '1.5rem',
                fontSize: '1rem',
                boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.1)',
              }}
            />

            <button
              onClick={handleTransfer}
              disabled={status === 'loading'}
              style={{
                backgroundColor: '#1DB954',
                color: '#fff',
                border: 'none',
                borderRadius: '5px',
                padding: '12px 24px', 
                fontSize: '1.1rem', 
                cursor: status === 'loading' ? 'not-allowed' : 'pointer',
                opacity: status === 'loading' ? 0.7 : 1,
                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
              }}
            >
              {status === 'loading' ? 'Transferring...' : 'Transfer Playlist'}
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export default App;
