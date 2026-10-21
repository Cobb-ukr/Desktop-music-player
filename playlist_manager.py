import json
import os

from config import PLAYLISTS_FILE, SONGS_DIR
from data_structures.circular_doubly_linked_list import CircularDoublyLinkedList


class PlaylistManager:
    """Holds all playlists and saves them to disk.

    Each playlist is a CircularDoublyLinkedList of song filenames, stored in a
    dictionary under the playlist's name. The GUI only calls the methods here;
    it never touches the linked lists directly.

    Every change is saved to the JSON file straight away.
    Positions are 0-based.
    """

    def __init__(self, file_path=PLAYLISTS_FILE, songs_folder=SONGS_DIR):
        self.file_path = file_path
        self.songs_folder = songs_folder
        self._playlists = {}  # name -> CircularDoublyLinkedList
        self.load()

    # ---------- playlists ----------

    def names(self):
        """All playlist names, sorted."""
        return sorted(self._playlists, key=str.lower)

    def exists(self, name):
        return self._find_name(name) is not None

    def create(self, name):
        name = self._clean_name(name)
        if self.exists(name):
            raise ValueError(f'A playlist called "{name}" already exists.')
        self._playlists[name] = CircularDoublyLinkedList()
        self.save()
        return name

    def delete(self, name):
        del self._playlists[self._require(name)]
        self.save()

    def rename(self, old_name, new_name):
        old_name = self._require(old_name)
        new_name = self._clean_name(new_name)
        # Allow changing only the capitalisation of the same playlist
        if new_name.casefold() != old_name.casefold() and self.exists(new_name):
            raise ValueError(f'A playlist called "{new_name}" already exists.')
        self._playlists[new_name] = self._playlists.pop(old_name)
        self.save()
        return new_name

    # ---------- songs inside a playlist ----------

    def songs_in(self, name):
        """The playlist's songs, in order, as a normal Python list."""
        return self._playlists[self._require(name)].to_list()

    def add_song(self, name, filename, position=None):
        """Insert a song at `position`. If position is None, add it to the end."""
        playlist = self._playlists[self._require(name)]
        if not os.path.isfile(os.path.join(self.songs_folder, filename)):
            raise ValueError(f'"{filename}" is not in the songs folder.')
        if position is None:
            position = len(playlist)
        playlist.insert_at(position, filename)  # raises IndexError if out of range
        self.save()

    def remove_song(self, name, position):
        """Remove the song at `position` and return its filename."""
        playlist = self._playlists[self._require(name)]
        filename = playlist.remove_at(position)  # raises IndexError if out of range
        self.save()
        return filename

    def move_song(self, name, from_position, to_position):
        """Move a song so that it ends up at `to_position`."""
        playlist = self._playlists[self._require(name)]
        last = len(playlist) - 1
        # Check both positions first so a bad request can't lose the song
        for position in (from_position, to_position):
            if position < 0 or position > last:
                raise IndexError(f"Position {position} out of range (0 to {last})")
        filename = playlist.remove_at(from_position)
        playlist.insert_at(to_position, filename)
        self.save()

    def get_linked_list(self, name):
        """The playlist's linked list itself (the player will use this later)."""
        return self._playlists[self._require(name)]

    # ---------- saving and loading ----------

    def save(self):
        data = {name: playlist.to_list() for name, playlist in self._playlists.items()}
        # Write to a temporary file first so a crash can't leave a half-written file
        temp_path = self.file_path + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, self.file_path)

    def load(self):
        """Rebuild every playlist from the JSON file.

        Songs whose mp3 no longer exists are skipped. A missing file means
        no playlists yet. An unreadable file is kept as a .bak backup.
        """
        self._playlists = {}
        if not os.path.isfile(self.file_path):
            return
        try:
            with open(self.file_path, encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("playlists file has the wrong structure")
        except (json.JSONDecodeError, ValueError, OSError):
            os.replace(self.file_path, self.file_path + ".bak")
            return

        for name, filenames in data.items():
            playlist = CircularDoublyLinkedList()
            for filename in filenames:
                if os.path.isfile(os.path.join(self.songs_folder, filename)):
                    playlist.append(filename)
            self._playlists[name] = playlist

    # ---------- helpers ----------

    def _clean_name(self, name):
        name = name.strip()
        if not name:
            raise ValueError("Playlist name can't be empty.")
        return name

    def _find_name(self, name):
        """Match a name ignoring capitalisation; return the stored name or None."""
        for stored in self._playlists:
            if stored.casefold() == name.strip().casefold():
                return stored
        return None

    def _require(self, name):
        stored = self._find_name(name)
        if stored is None:
            raise KeyError(f'No playlist called "{name}".')
        return stored