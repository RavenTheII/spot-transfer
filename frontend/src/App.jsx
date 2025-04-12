import React, { useState } from 'react';

function App() {
  const [playlistLink, setPlaylistLink] = useState('');
  const [status, setStatus] = useState('idle');
  const [message, setMessage] = useState('');

  const handleTransfer = async () => {
    if (!playlistLink.trim()) {
      setMessage("Please enter a playlist link.");
      setStatus("error");
      return;
    }

    setStatus('loading');
    setMessage('');

    try {
      const response = await fetch('http://localhost:8080/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ playlist_link: playlistLink }),
      });

      const data = await response.json();

      if (response.ok) {
        setStatus('success');
        setMessage('✅ Playlist transferred successfully!');
      } else {
        setStatus('error');
        setMessage(`❌ Error: ${data.error || "Something went wrong."}`);
      }
    } catch (err) {
      setStatus('error');
      setMessage('❌ Failed to connect to the server.');
    }
  };

  const handleSwitchAccount = async () => {
    try {
      const res = await fetch('http://localhost:8080/logout', { method: 'POST' });
      const data = await res.json();
  
      if (res.ok) {
        setStatus("success");
        setMessage("✅ Logged out!");
        setPlaylistLink('');
      } else {
        setStatus("error");
        setMessage(`❌ Logout failed: ${data.error || "Unknown error"}`);
      }
    } catch (err) {
      setStatus("error");
      setMessage("❌ Could not contact the server.");
    }
  };

  return (
    <div style={{
      position: 'relative',
      minHeight: '100vh',
      minWidth: '100vw',
      backgroundColor: '#2222',
      fontFamily: 'Arial',
    }}>
      {/* Top-right Switch Account Button */}
      <div style={{
        position: 'absolute',
        top: '20px',
        right: '20px',
      }}>
        <button
          onClick={handleSwitchAccount}
          style={{
            backgroundColor: '#FF0000',
            color: '#fff',
            border: 'none',
            borderRadius: '5px',
            padding: '8px 16px',
            fontSize: '0.9rem',
            cursor: 'pointer',
          }}
        >
          Log Out
        </button>
      </div>

      {/* Main content */}
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        flexDirection: 'column',
        paddingTop: '100px', // padding to avoid overlap with top button
      }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '1rem', textAlign: 'center' }}>
          <span style={{ color: '#1DB954' }}>Spotify</span> to <span style={{ color: '#FF0000' }}>YouTube Music</span> Transfer
        </h1>

        <p style={{ fontSize: '1.2rem', textAlign: 'center', marginBottom: '1rem' }}>
          Paste your Spotify playlist link below and click transfer:
        </p>

        <input
          type="text"
          value={playlistLink}
          onChange={(e) => setPlaylistLink(e.target.value)}
          placeholder="Paste Spotify Playlist Link"
          style={{
            width: '60%',
            padding: '10px',
            borderRadius: '5px',
            border: '1px solid #ccc',
            marginBottom: '1rem',
            fontSize: '1rem',
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
            padding: '10px 20px',
            fontSize: '1rem',
            cursor: status === 'loading' ? 'not-allowed' : 'pointer',
          }}
        >
          {status === 'loading' ? 'Transferring...' : 'Transfer'}
        </button>

        {status !== 'idle' && (
          <p style={{
            fontSize: '1rem',
            marginTop: '1rem',
            color: status === 'success' ? 'green' : 'red',
          }}>
            {message}
          </p>
        )}
      </div>
    </div>
  );
}

export default App;
