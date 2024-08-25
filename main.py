import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pylast
import os

# Limit how many liked songs you want to transfer (order is starting with the most recent likes)
NUMBER_OF_RECENT_LIKES_TO_TRANSFER = 400
LOG_FILE = 'loved_songs.log'

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

# Function to read log file and get already loved songs
def read_loved_songs_log(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f)
    return set()

# Function to write a song to the log file
def log_loved_song(file_path, artist, track):
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(f"{artist} - {track}\n")

# Load already loved songs from the log file
loved_songs_log = read_loved_songs_log(LOG_FILE)

# Initialize variables for loop
offset = 0
liked_songs_count = 0
encountered_already_loved_song = False

while liked_songs_count < NUMBER_OF_RECENT_LIKES_TO_TRANSFER:
    # Fetch liked songs in batches of 50
    results = sp.current_user_saved_tracks(limit=50, offset=offset)
    liked_songs = results['items']

    if not liked_songs:  # If no more songs are found, break out of the loop
        break

    for item in liked_songs:
        if liked_songs_count >= NUMBER_OF_RECENT_LIKES_TO_TRANSFER:
            break

        track = item['track']
        artist_name = track['artists'][0]['name']
        track_name = track['name']
        song_identifier = f"{artist_name} - {track_name}"

        # Stop the process if the song is already loved
        if song_identifier in loved_songs_log:
            print(f"Encountered already loved song: {song_identifier}. Stopping the process.")
            encountered_already_loved_song = True
            liked_songs_count = NUMBER_OF_RECENT_LIKES_TO_TRANSFER  # Force exit of the outer loop
            break

        # Optional: Log the song being "loved"
        print(f"Loving {track_name} by {artist_name} on Last.fm")

        # Love the song on Last.fm
        track = network.get_track(artist_name, track_name)
        track.love()

        # Log the song to the file
        log_loved_song(LOG_FILE, artist_name, track_name)

        liked_songs_count += 1

    # Increase offset to get the next batch of liked songs
    offset += 50

# Final message
if encountered_already_loved_song:
    print("Stopped because it encountered an already logged liked song.")
else:
    print(f"Done loving {liked_songs_count} liked songs on Last.fm!")
