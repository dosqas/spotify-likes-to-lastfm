import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time

# Replace these with your actual credentials
SPOTIFY_CLIENT_ID = 'your_spotify_client_id'
SPOTIFY_CLIENT_SECRET = 'your_spotify_client_secret'
SPOTIFY_REDIRECT_URI = 'http://localhost:8888/callback'
LASTFM_API_KEY = 'your_lastfm_api_key'
LASTFM_API_SECRET = 'your_lastfm_api_secret'
LASTFM_USERNAME = 'your_lastfm_username'
LASTFM_PASSWORD = 'your_lastfm_password'  # This should be hashed using MD5

# Step 1: Authenticate with Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID,
                                               client_secret=SPOTIFY_CLIENT_SECRET,
                                               redirect_uri=SPOTIFY_REDIRECT_URI,
                                               scope="user-library-read"))

# Step 2: Get liked songs from Spotify
results = sp.current_user_saved_tracks()
liked_songs = results['items']

# Step 3: Authenticate with Last.fm
import pylast

network = pylast.LastFMNetwork(
    api_key=LASTFM_API_KEY,
    api_secret=LASTFM_API_SECRET,
    username=LASTFM_USERNAME,
    password_hash=pylast.md5(LASTFM_PASSWORD),
)

# Step 4: Scrobble each song to Last.fm
for item in liked_songs:
    track = item['track']
    artist_name = track['artists'][0]['name']
    track_name = track['name']

    # Optional: Log the song being scrobbled
    print(f"Scrobbling {track_name} by {artist_name}")

    # Scrobble the song to Last.fm
    network.scrobble(artist=artist_name, title=track_name, timestamp=int(time.time()))

print("Done scrobbling all liked songs!")
