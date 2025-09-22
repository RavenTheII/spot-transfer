import React, { useState, useEffect } from 'react';

const BASE_URL = import.meta.env.VITE_API_URL || window.location.origin;
const api = (path) => new URL(path, BASE_URL).toString();

const parseJsonSafe = async (res) => {
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/json')) {
    try { return await res.json(); } catch { return null; }
  }
  return null;
};

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

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(api('/me'), { credentials: 'include' });
        setIsLoggedIn(res.ok);
      } catch (e) {
        setIsLoggedIn(false);
      }
    })();
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
      const response = await fetch(api('/create'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ playlist_link: playlistLink }),
        credentials: 'include',
      });

      const data = (await parseJsonSafe(response)) || {};

      if (response.ok) {
        setStatus('success');
        setMessage(`✅ ${data.message || 'Playlist transferred successfully!'}`);
        if (data.missed_tracks && data.missed_tracks.length > 0) {
          setMessage(prevMessage => `${prevMessage} Some tracks were not found: ${data.missed_tracks.join(', ')}`);
        }
      } else {
        setStatus('error');
        let errMsg = `❌ Error: ${data.error || 'Something went wrong.'}`;
        if (data && data.detail) {
          errMsg += ` Details: ${data.detail}`;
        }
        if (data && data.exception) {
          errMsg += ` (${data.exception})`;
        }
        setMessage(errMsg);
        if (data && data.trace) {
          // Print stack trace to dev console for deeper debugging
          // eslint-disable-next-line no-console
          console.error('Server trace:', data.trace);
        }
        if (response.status === 401) {
          setIsLoggedIn(false);
          setMessage('❌ Authentication required. Please log in.');
        }
      }
    } catch (err) {
      setStatus('error');
      setMessage('❌ Failed to connect to the server.');
    }
  };

  const handleLogin = () => {
    window.location.href = api('/login/google');
  };

  const handleLogout = async () => {
    setStatus('loading');
    setMessage('');
    try {
      const res = await fetch(api('/logout'), {
        method: 'POST',
        credentials: 'include',
      });
      const data = (await parseJsonSafe(res)) || {};
  
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
  <div
    className="relative min-h-screen w-full bg-gray-50 font-sans text-gray-900 p-6 box-border flex flex-col"
  >
    <div className="absolute top-5 right-5">
      {isLoggedIn ? (
        <button
          onClick={handleLogout}
          disabled={status === 'loading'}
          className="bg-red-600 text-white rounded-md px-5 py-2 text-base font-semibold cursor-pointer shadow-md transition-colors duration-300 ease-in-out hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-1"
        >
          Log Out
        </button>
      ) : (
        <button
          onClick={handleLogin}
          disabled={status === 'loading'}
          className="animate-fade-in-scale flex items-center gap-3 bg-white text-black font-medium border border-gray-300 rounded-full px-7 py-3 text-base shadow-sm hover:shadow-md transition-transform duration-200 ease-in-out hover:scale-105 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
        >
          <img
            src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg"
            alt="Google logo"
            className="w-5 h-5"
          />
          Sign in with Google
        </button>
      )}
    </div>

    <div
      className="flex flex-col justify-start items-stretch text-left w-full flex-1"
      style={{ paddingTop: isLoggedIn ? '80px' : '120px' }}
    >
      <h1 className="text-3xl sm:text-4xl lg:text-5xl mb-8 font-extrabold tracking-tight leading-tight">
        <span className="text-green-600">Spotify</span> to{' '}
        <span className="text-red-600">YouTube Music</span> Transfer
      </h1>

      {message && (
        <p
          className={`text-lg my-6 px-5 py-3 rounded-md border max-w-full w-4/5 break-words
            ${status === 'success' ? 'bg-green-100 text-green-900 border-green-300' : ''}
            ${status === 'error' ? 'bg-red-100 text-red-900 border-red-300' : ''}
            ${status === 'idle' ? 'bg-gray-100 text-gray-900 border-gray-300' : ''}
          `}
          role="alert"
          aria-live="polite"
        >
          {message}
        </p>
      )}

      {!isLoggedIn && (
        <p className="text-xl mt-16 text-gray-700 max-w-md animate-fade-in-scale">
          Please log in with your Google account to transfer playlists.
        </p>
      )}

      {isLoggedIn && (
        <>
          <p className="text-xl mb-6 font-medium animate-fade-in-scale">
            Paste your Spotify playlist link below and click transfer:
          </p>

          <input
            type="text"
            value={playlistLink}
            onChange={(e) => {
              setPlaylistLink(e.target.value);
              setMessage('');
              setStatus('idle');
            }}
            placeholder="Paste Spotify Playlist Link"
            className="w-full max-w-xl p-4 rounded-lg border border-gray-300 mb-8 text-base shadow-inner focus:outline-none focus:ring-4 focus:ring-blue-400 focus:ring-opacity-50 transition-shadow duration-300 ease-in-out"
          />

          <button
            onClick={handleTransfer}
            disabled={status === 'loading'}
            className={`bg-green-600 text-white rounded-lg px-8 py-3 text-lg font-semibold cursor-pointer shadow-lg transition-all duration-300 ease-in-out hover:bg-green-700 focus:outline-none focus:ring-4 focus:ring-green-500 focus:ring-opacity-60
              ${status === 'loading' ? 'opacity-70 cursor-not-allowed' : ''}
            `}
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
