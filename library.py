import os

from config import SONGS_DIR


def get_songs(folder=SONGS_DIR):
    """Return the mp3 filenames in the songs folder, sorted alphabetically.

    This is the "downloads list": a plain Python list (array) of filenames.
    Returns an empty list if the folder doesn't exist yet.
    """
    if not os.path.isdir(folder):
        return []
    files = [f for f in os.listdir(folder) if f.lower().endswith(".mp3")]
    return sorted(files, key=str.lower)


def song_path(filename, folder=SONGS_DIR):
    """Full path to a song file (used later by the player)."""
    return os.path.join(folder, filename)


def display_name(filename):
    """A nicer name for showing in the GUI: the filename without '.mp3'."""
    return os.path.splitext(filename)[0]