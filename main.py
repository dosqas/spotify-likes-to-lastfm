import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pylast

# Limit how many liked songs you want transfer (order is starting with the most recent likes)
NUMBER_OF_LIKES = 400

# Replace these with your actual credentials
SPOTIFY_CLIENT_ID = 'SPOTIFY_CLIENT_ID'
SPOTIFY_CLIENT_SECRET = 'SPOTIFY_CLIENT_SECRET'
SPOTIFY_REDIRECT_URI = 'http://localhost:8888/callback'
LASTFM_API_KEY = 'LASTFM_API_KEY'
LASTFM_API_SECRET = 'LASTFM_API_SECRET'
LASTFM_USERNAME = 'LASTFM_USERNAME'
LASTFM_PASSWORD = 'LASTFM_PASSWORD'

# Step 1: Authenticate with Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID,
                                               client_secret=SPOTIFY_CLIENT_SECRET,
                                               redirect_uri=SPOTIFY_REDIRECT_URI,
                                               scope="user-library-read"))

# Step 2: Authenticate with Last.fm
network = pylast.LastFMNetwork(
    api_key=LASTFM_API_KEY,
    api_secret=LASTFM_API_SECRET,
    username=LASTFM_USERNAME,
    password_hash=pylast.md5(LASTFM_PASSWORD),
)

# Initialize variables for loop
offset = 0
liked_songs_count = 0

while liked_songs_count < NUMBER_OF_LIKES:
    # Fetch liked songs in batches of 50
    results = sp.current_user_saved_tracks(limit=50, offset=offset)
    liked_songs = results['items']

    if not liked_songs:  # If no more songs are found, break out of the loop
        break

    for item in liked_songs:
        if liked_songs_count >= NUMBER_OF_LIKES:
            break

        track = item['track']
        artist_name = track['artists'][0]['name']
        track_name = track['name']

        # Optional: Log the song being "loved"
        print(f"Loving {track_name} by {artist_name} on Last.fm")

        # Love the song on Last.fm
        track = network.get_track(artist_name, track_name)
        track.love()

        liked_songs_count += 1

    # Increase offset to get the next batch of liked songs
    offset += 50

print(f"Done loving {liked_songs_count} liked songs on Last.fm!")
