"""
MIT License

Copyright (c) 2024 Raphael Maschinsen
raphaelmaschinsen@gmail.com
Copyright (c) 2025 hazre

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pylast
import os
import argparse
from dotenv import load_dotenv

load_dotenv()


def parse_args():
	parser = argparse.ArgumentParser(
		description="Transfer Spotify liked songs to LastFM or delete all loved songs from LastFM"
	)
	parser.add_argument(
		"--deleteAll",
		action="store_true",
		help="Delete all loved songs from LastFM account",
	)
	return parser.parse_args()


LIMIT_NUMBER_OF_RECENT_LIKES_TO_TRANSFER = (
	int(os.getenv("LIMIT_NUMBER_OF_RECENT_LIKES", "0")) or None
)
LOG_FILE = os.getenv("LOG_FILE") or "loved_songs.log"
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = (
	os.getenv("SPOTIFY_REDIRECT_URI") or "http://localhost:8888/callback"
)
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
LASTFM_API_SECRET = os.getenv("LASTFM_API_SECRET")
LASTFM_USERNAME = os.getenv("LASTFM_USERNAME")
LASTFM_PASSWORD = os.getenv("LASTFM_PASSWORD")

# Step 1: Authenticate with Spotify
sp = spotipy.Spotify(
	auth_manager=SpotifyOAuth(
		client_id=SPOTIFY_CLIENT_ID,
		client_secret=SPOTIFY_CLIENT_SECRET,
		redirect_uri=SPOTIFY_REDIRECT_URI,
		scope="user-library-read",
	)
)

# Step 2: Authenticate with Last.fm
network = pylast.LastFMNetwork(
	api_key=LASTFM_API_KEY,
	api_secret=LASTFM_API_SECRET,
	username=LASTFM_USERNAME,
	password_hash=pylast.md5(LASTFM_PASSWORD),
)


# Function to read log file and get already loved song identifiers
def read_loved_songs_log(file_path: str) -> set:
	if os.path.exists(file_path):
		with open(file_path, "r", encoding="utf-8") as f:
			return set(line.strip() for line in f)
	return set()


# Function to write a song's details to the log file
def log_loved_song(file_path: str, artist: str, title: str, id_: str):
	with open(file_path, "a", encoding="utf-8") as f:
		f.write(f"{artist} - {title} - {id_}\n")


# Load already loved song identifiers from the log file
loved_songs_log = read_loved_songs_log(LOG_FILE)


def delete_all_loved_songs(network: pylast.LastFMNetwork):
	"""Delete all loved songs from LastFM account"""
	print("Starting to delete all loved songs from LastFM...")
	deleted_count = 0
	batch_size = 50

	while True:
		# Get a batch of loved tracks
		loved_tracks = network.get_user(LASTFM_USERNAME).get_loved_tracks(
			limit=batch_size, cacheable=True
		)
		if not loved_tracks:
			break

		for loved_track in loved_tracks:
			track = loved_track.track
			print(f"Unlove track: {track.artist.name} - {track.title}")
			track.unlove()
			deleted_count += 1

		# If we got fewer tracks than the batch size, we've reached the end
		if len(loved_tracks) < batch_size:
			break

	print(f"Successfully deleted {deleted_count} loved songs from LastFM!")


def transfer_liked_songs():
	"""Transfer Spotify liked songs to LastFM"""
	# Initialize variables for loop
	offset = 0
	liked_songs_count = 0
	skipped_songs_count = 0

	while True:
		# Fetch liked songs in batches of 50
		results = sp.current_user_saved_tracks(limit=50, offset=offset)
		liked_songs = results["items"]

		if not liked_songs:  # If no more songs are found, break out of the loop
			break

		for item in liked_songs:
			if (
				LIMIT_NUMBER_OF_RECENT_LIKES_TO_TRANSFER is not None
				and liked_songs_count >= LIMIT_NUMBER_OF_RECENT_LIKES_TO_TRANSFER
			):
				break

			track = item["track"]
			track_id = track["id"]  # Get the unique track ID
			artist_name = track["artists"][0]["name"]
			track_name = track["name"]
			song_identifier = f"{artist_name} - {track_name} - {track_id}"

			# Skip if the song is already loved
			if song_identifier in loved_songs_log:
				print(f"Skipping already loved song: {track_name} by {artist_name}")
				skipped_songs_count += 1
				continue

			print(f"Loving {track_name} by {artist_name} on Last.fm")

			# Love the song on Last.fm
			track_lfm = network.get_track(artist_name, track_name)
			track_lfm.love()

			# Log the song details to the file
			log_loved_song(LOG_FILE, artist_name, track_name, track_id)

			liked_songs_count += 1

		if (
			LIMIT_NUMBER_OF_RECENT_LIKES_TO_TRANSFER is not None
			and liked_songs_count >= LIMIT_NUMBER_OF_RECENT_LIKES_TO_TRANSFER
		):
			break

		# Increase offset to get the next batch of liked songs
		offset += 50

	print(
		f"Done! Loved {liked_songs_count} new songs and skipped {skipped_songs_count} already loved songs on Last.fm!"
	)


def main():
	args = parse_args()

	if args.deleteAll:
		delete_all_loved_songs(network)
	else:
		transfer_liked_songs()


if __name__ == "__main__":
	main()
