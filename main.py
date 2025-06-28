"""
MIT License

Copyright (c) 2024 Raphael Maschinsen
raphaelmaschinsen@gmail.com
Copyright (c) 2025 hazre

Copyright (c) 2025 Sebastian "dosqas" Soptelea
sebastian.soptelea@proton.me

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

import argparse
import logging
import os
import socket
import time
from datetime import datetime
from typing import Optional, Tuple

import pylast
import requests
import spotipy
from colorama import Fore, Style, init
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
import keyboard

# Global state
paused = False

# Color constants
FOREGROUND_WHITE = "\x1b[97m"
FOREGROUND_GREY = "\x1b[37m"
FOREGROUND_DARK_GREY = "\x1b[90m"
FOREGROUND_LIGHT_GREY = "\x1b[38;5;250m"


def toggle_pause(_: keyboard.KeyboardEvent) -> None:
    """Toggle pause state when space key is pressed."""
    global paused
    paused = not paused
    if paused:
        logging.info(f"{FOREGROUND_LIGHT_GREY}[!] Paused. Press space to resume.")
    else:
        logging.info(f"{FOREGROUND_LIGHT_GREY}[!] Resumed.")


class CustomFormatter(logging.Formatter):
    """Custom formatter for colored log output."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors and timestamps."""
        # Timestamp will be formatted as HH:MM:SS and colored grey
        time_str = f"{Style.BRIGHT}{FOREGROUND_GREY}{datetime.fromtimestamp(record.created).strftime('%H:%M:%S')}"
        prefix = f"{Style.BRIGHT}"

        if record.levelno == logging.WARNING:
            prefix += f"{Fore.YELLOW}[/!\\] "
        elif record.levelno == logging.ERROR:
            prefix += f"{Fore.RED}[!!!] "
        elif record.levelno == logging.INFO:
            prefix += f"{FOREGROUND_LIGHT_GREY}"

        # Format the message with the prefix and color it white
        original_msg = record.getMessage()
        msg = f"{prefix}{original_msg}{Style.RESET_ALL}"

        # Combine and return full formatted string
        return f"{time_str} {msg}"


def setup_logging() -> None:
    """Set up logging configuration with custom formatter."""
    handler = logging.StreamHandler()
    handler.setFormatter(CustomFormatter())

    # Configure root logger
    logging.basicConfig(level=logging.INFO, handlers=[handler])
    logging.getLogger("pylast").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Transfer Spotify liked songs to LastFM or delete all loved songs from LastFM"
    )
    parser.add_argument(
        "--deleteAll",
        action="store_true",
        help="Delete all loved songs from LastFM account",
    )
    return parser.parse_args()


class Config:
    """Configuration class to manage environment variables."""
    
    def __init__(self) -> None:
        load_dotenv()
        
        self.limit_number_of_recent_likes_to_transfer = (
            int(os.getenv("LIMIT_NUMBER_OF_RECENT_LIKES", "0")) or None
        )
        self.log_file = os.getenv("LOG_FILE") or "loved_songs.log"
        self.spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.spotify_redirect_uri = (
            os.getenv("SPOTIFY_REDIRECT_URI") or "http://127.0.0.1:8888/callback"
        )
        self.lastfm_api_key = os.getenv("LASTFM_API_KEY")
        self.lastfm_api_secret = os.getenv("LASTFM_API_SECRET")
        self.lastfm_username = os.getenv("LASTFM_USERNAME")
        self.lastfm_password = os.getenv("LASTFM_PASSWORD")
        
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate that required configuration values are present."""
        required_fields = [
            ("SPOTIFY_CLIENT_ID", self.spotify_client_id),
            ("SPOTIFY_CLIENT_SECRET", self.spotify_client_secret),
            ("LASTFM_API_KEY", self.lastfm_api_key),
            ("LASTFM_API_SECRET", self.lastfm_api_secret),
            ("LASTFM_USERNAME", self.lastfm_username),
            ("LASTFM_PASSWORD", self.lastfm_password),
        ]
        
        missing_fields = [field for field, value in required_fields if not value]
        if missing_fields:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_fields)}")
        
        # After validation, we know these are not None
        assert self.spotify_client_id is not None
        assert self.spotify_client_secret is not None
        assert self.lastfm_api_key is not None
        assert self.lastfm_api_secret is not None
        assert self.lastfm_username is not None
        assert self.lastfm_password is not None


class Authenticator:
    """Handles authentication with Spotify and Last.fm."""
    
    def __init__(self, config: Config) -> None:
        self.config = config
    
    def authenticate_spotify(self) -> spotipy.client.Spotify:
        """Authenticate with Spotify using OAuth."""
        logging.info(f"{FOREGROUND_LIGHT_GREY}Authenticating with Spotify...")
        try:
            sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=self.config.spotify_client_id,
                client_secret=self.config.spotify_client_secret,
                redirect_uri=self.config.spotify_redirect_uri,
                scope="user-library-read",
            ))
            logging.info(f"{FOREGROUND_LIGHT_GREY}[!] Successfully authenticated with Spotify.")
            return sp
        except spotipy.SpotifyException as e:
            logging.error(f"Spotify API error: {e}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error during Spotify auth: {e}")
        except Exception as e:
            logging.error(f"Unexpected error during Spotify auth: {e}")
        raise RuntimeError("Failed to authenticate with Spotify")
    
    def authenticate_lastfm(self) -> pylast.LastFMNetwork:
        """Authenticate with Last.fm using API key and secret."""
        logging.info(f"{FOREGROUND_LIGHT_GREY}Authenticating with Last.fm...")
        try:
            # Type assertions since we validated these are not None
            assert self.config.lastfm_api_key is not None
            assert self.config.lastfm_api_secret is not None
            assert self.config.lastfm_username is not None
            assert self.config.lastfm_password is not None
            
            network = pylast.LastFMNetwork(
                api_key=self.config.lastfm_api_key,
                api_secret=self.config.lastfm_api_secret,
                username=self.config.lastfm_username,
                password_hash=pylast.md5(self.config.lastfm_password),
            )
            logging.info(f"{FOREGROUND_LIGHT_GREY}[!] Successfully authenticated with Last.fm.")
            return network
        except pylast.WSError as e:
            logging.error(f"Last.fm API error: {e}")
        except (requests.exceptions.RequestException, socket.error) as e:
            logging.error(f"Network error during Last.fm auth: {e}")
        except Exception as e:
            logging.error(f"Unexpected error during Last.fm auth: {e}")
        raise RuntimeError("Failed to authenticate with Last.fm")
    
    def authenticate(self) -> Tuple[spotipy.client.Spotify, pylast.LastFMNetwork]:
        """Authenticate with both Spotify and Last.fm."""
        return self.authenticate_spotify(), self.authenticate_lastfm()


class LogManager:
    """Manages the log file for tracking loved songs."""
    
    def __init__(self, log_file: str) -> None:
        self.log_file = log_file
        self.loved_songs_log = self._read_loved_songs_log()
    
    def _read_loved_songs_log(self) -> set[str]:
        """Read log file and get already loved song identifiers."""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, "r", encoding="utf-8") as f:
                    return set(line.strip() for line in f)
        except OSError as e:
            logging.error(f"Error reading log file: {e}")
        return set()
    
    def log_loved_song(self, artist: str, title: str, track_id: str) -> None:
        """Write a song's details to the log file."""
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"{artist} - {title} - {track_id}\n")
        except OSError as e:
            logging.error(f"Error writing to log file: {e}")
    
    def is_song_loved(self, song_identifier: str) -> bool:
        """Check if a song is already in the loved songs log."""
        return song_identifier in self.loved_songs_log


class LastFMService:
    """Handles Last.fm operations."""
    
    def __init__(self, network: pylast.LastFMNetwork, username: str) -> None:
        self.network = network
        self.username = username
    
    def delete_all_loved_songs(self) -> None:
        """Delete all loved songs from LastFM account."""
        logging.info(f"{FOREGROUND_LIGHT_GREY}[!] Starting to delete all loved songs from LastFM...")
        deleted_count = 0
        batch_size = 50

        while True:
            # Get a batch of loved tracks
            loved_tracks = list(self.network.get_user(self.username).get_loved_tracks(
                limit=batch_size, cacheable=True
            ))
            
            if not loved_tracks:
                break

            for loved_track in loved_tracks:
                while paused:
                    time.sleep(0.1)

                track = loved_track.track
                logging.info(f"Unloving track: {FOREGROUND_WHITE}{track.artist.name} {FOREGROUND_DARK_GREY}- {FOREGROUND_WHITE}{track.title}")
                track.unlove()
                deleted_count += 1

            # If we got fewer tracks than the batch size, we've reached the end
            if len(loved_tracks) < batch_size:
                break

        logging.info(f"{FOREGROUND_LIGHT_GREY}Successfully removed {deleted_count} loved songs from LastFM!")
    
    def love_track(self, artist_name: str, track_name: str) -> None:
        """Love a track on Last.fm."""
        track_lfm = self.network.get_track(artist_name, track_name)
        track_lfm.love()


class SpotifyService:
    """Handles Spotify operations."""
    
    def __init__(self, client: spotipy.client.Spotify) -> None:
        self.client = client
    
    def get_liked_songs(self, limit: int = 50, offset: int = 0) -> Optional[dict]:
        """Get liked songs from Spotify."""
        try:
            return self.client.current_user_saved_tracks(limit=limit, offset=offset)
        except Exception as e:
            logging.error(f"Error fetching liked songs: {e}")
            return None


class TransferService:
    """Handles the transfer of songs between Spotify and Last.fm."""
    
    def __init__(self, spotify_service: SpotifyService, lastfm_service: LastFMService, log_manager: LogManager, config: Config) -> None:
        self.spotify_service = spotify_service
        self.lastfm_service = lastfm_service
        self.log_manager = log_manager
        self.config = config
    
    def transfer_liked_songs(self) -> None:
        """Transfer Spotify liked songs to LastFM."""
        offset = 0
        liked_songs_count = 0
        skipped_songs_count = 0

        while True:
            # Fetch liked songs in batches of 50
            results = self.spotify_service.get_liked_songs(limit=50, offset=offset)
            if not results:
                break
                
            liked_songs = results["items"]

            if not liked_songs:  # If no more songs are found, break out of the loop
                break

            for item in liked_songs:
                while paused:
                    time.sleep(0.1)

                if (
                    self.config.limit_number_of_recent_likes_to_transfer is not None
                    and liked_songs_count >= self.config.limit_number_of_recent_likes_to_transfer
                ):
                    break

                track = item["track"]
                if track is None:
                    logging.warning("Skipping a removed or unavailable track.")
                    continue

                track_id = track["id"]  # Get the unique track ID
                artist_name = track["artists"][0]["name"]
                track_name = track["name"]
                song_identifier = f"{artist_name} - {track_name} - {track_id}"

                # Skip if the song is already loved
                if self.log_manager.is_song_loved(song_identifier):
                    logging.info(f"Skipping already loved song: {FOREGROUND_WHITE}{track_name} {FOREGROUND_DARK_GREY}by {FOREGROUND_WHITE}{artist_name}")
                    skipped_songs_count += 1
                    continue

                logging.info(f"Loving {FOREGROUND_WHITE}{track_name} {FOREGROUND_DARK_GREY}by {FOREGROUND_WHITE}{artist_name} {FOREGROUND_LIGHT_GREY}on Last.fm")

                # Love the song on Last.fm
                self.lastfm_service.love_track(artist_name, track_name)

                # Log the song details to the file
                self.log_manager.log_loved_song(artist_name, track_name, track_id)

                liked_songs_count += 1

            if (
                self.config.limit_number_of_recent_likes_to_transfer is not None
                and liked_songs_count >= self.config.limit_number_of_recent_likes_to_transfer
            ):
                break

            # Increase offset to get the next batch of liked songs
            offset += 50

        logging.info(
            f"{FOREGROUND_LIGHT_GREY}[!] Done! Loved {liked_songs_count} new songs and skipped {skipped_songs_count} already loved songs on Last.fm!"
        )


def main() -> None:
    """Main function to orchestrate the transfer process."""
    # Initialize colorama
    init(autoreset=True)
    
    # Set up logging
    setup_logging()
    
    # Set up keyboard listener
    keyboard.on_press_key("space", toggle_pause)
    
    try:
        args = parse_args()
        logging.info(f"{FOREGROUND_LIGHT_GREY}Starting script. Press SPACE at any time to pause it. Authorizing...")
        
        # Initialize configuration
        config = Config()
        
        # Initialize services
        authenticator = Authenticator(config)
        sp, network = authenticator.authenticate()
        
        spotify_service = SpotifyService(sp)
        lastfm_service = LastFMService(network, config.lastfm_username)
        log_manager = LogManager(config.log_file)
        transfer_service = TransferService(spotify_service, lastfm_service, log_manager, config)

        if args.deleteAll:
            lastfm_service.delete_all_loved_songs()
        else:
            transfer_service.transfer_liked_songs()
            
    except KeyboardInterrupt:
        logging.info(f"{FOREGROUND_LIGHT_GREY}[!] Script stopped by user. Exiting gracefully.")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
