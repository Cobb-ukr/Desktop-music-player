import os

# Always resolve paths relative to this project folder,
# so the program works no matter where it is launched from.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SONGS_DIR = os.path.join(BASE_DIR, "songs")

# All downloaded audio is converted to this format and bitrate (kbps)
AUDIO_FORMAT = "mp3"
AUDIO_QUALITY = "192"

# All playlists are saved in this one JSON file
PLAYLISTS_FILE = os.path.join(BASE_DIR, "playlists.json")