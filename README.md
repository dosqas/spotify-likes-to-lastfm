# Spotify to Last.fm - Transfer Liked Songs Script

This Python script allows you to transfer your liked songs from Spotify to your Last.fm account as "loved" tracks. The script logs the transferred likes, allowing you to rerun it periodically to update recent likes. It helps you synchronize your music preferences between the two platforms by automating the process.

## Features

- **Automatic Transfer**: The script automatically transfers your liked songs from Spotify to Last.fm.
- **Automatic Updates**: It keeps a log of already transferred songs and skips those that are already loved.
- **Customizable Limit**: You can optionally set a limit on the number of songs to transfer. It will always start transferring the most recent likes.
- **Delete Option**: You can delete all loved tracks from your Last.fm account using the `--deleteAll` flag.

## Prerequisites

Before you begin, ensure you have the following:

1. **Python 3.x**: The script requires Python 3.x to run. You can download Python from [python.org](https://www.python.org/downloads/). Or use [uv](https://docs.astral.sh/uv/) to install and manage python versions.
2. **Spotify Developer Account**: You need to create an app in the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications) to get your Client ID and Client Secret.
3. **Last.fm API Key**: Create a developer account and generate an API key on the [Last.fm API page](https://www.last.fm/api).

## Installation Guide

Follow these steps to set up and run the script:

### 1. Clone the Repository

First, download or clone the repository:

```bash
git clone https://github.com/hazre/SpotifyLikesToLastfm.git
cd SpotifyLikesToLastfm
```

### 2. Install Required Python Packages

This project uses `uv` for package management and dependency resolution. You can install packages using either uv or traditional pip:

With uv (recommended):
```bash
uv pip install .
```

With traditional pip:
```bash
pip install .
```

### 3. Set Up Your Spotify and Last.fm Credentials

#### Spotify App Configuration

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications) and log in.
2. Create a new app by clicking the "Create an App" button.
3. Fill in the required details for your app.
4. After creating the app, you'll see a section called **Redirect URIs**.
5. Add `http://localhost:8888/callback` as a redirect URI. This is necessary because the script uses this address to receive the authentication token from Spotify.
6. Save your changes and note down your **Client ID** and **Client Secret**.

#### Last.fm Developer Account Setup

1. Visit the [Last.fm API page](https://www.last.fm/api).
2. Log in with your Last.fm account or create one if you don't have it.
3. Click on the "Get an API account" link.
4. Fill in the form with any app name (it can be anything, like "Spotify to Last.fm Transfer").
5. After submitting the form, you'll receive your **API Key** and **Shared Secret**.

#### Configure Environment Variables

The script now uses environment variables for configuration. Create a `.env` file in the project directory by copying the example file:

```bash
cp .env.example .env
```

Then edit the `.env` file and add your credentials:

```
SPOTIFY_CLIENT_ID="your_spotify_client_id"
SPOTIFY_CLIENT_SECRET="your_spotify_client_secret"
LASTFM_API_KEY="your_lastfm_api_key"
LASTFM_API_SECRET="your_lastfm_api_secret"
LASTFM_USERNAME="your_lastfm_username"
LASTFM_PASSWORD="your_lastfm_password"

# Optional settings
SPOTIFY_REDIRECT_URI="http://localhost:8888/callback"
LOG_FILE="loved_songs.log"
LIMIT_NUMBER_OF_RECENT_LIKES="100"
```

All settings after the "Optional settings" comment are optional:
- `SPOTIFY_REDIRECT_URI` defaults to "http://localhost:8888/callback"
- `LOG_FILE` defaults to "loved_songs.log"
- `LIMIT_NUMBER_OF_RECENT_LIKES` is not set by default (transfers all songs)

### 4. Run the Script

Once you have set up your credentials, you can run the script:

With uv:
```bash
# Transfer liked songs
uv run main.py

# Delete all loved songs from Last.fm
uv run main.py --deleteAll
```

With traditional Python:
```bash
# Transfer liked songs
python main.py

# Delete all loved songs from Last.fm
python main.py --deleteAll
```

### 5. Development

This project uses:
- `uv` for package management
- `ruff` for linting and formatting

To run the linter:
```bash
# With uv
uv run ruff check
```

To format code:
```bash
# With uv
uv run ruff format
```

## Contributing

If you want to contribute to this project, feel free to fork the repository and submit pull requests.

## License

This project is licensed under the MIT License.