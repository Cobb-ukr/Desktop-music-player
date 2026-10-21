"""Checks for library.py and playlist_manager.py, using temporary folders.
Run from the project folder with:  python test_playlist_manager.py
"""
import json
import os
import tempfile

import library
from playlist_manager import PlaylistManager


def make_env(song_names=("a.mp3", "b.mp3", "c.mp3", "d.mp3")):
    """A temporary songs folder (with empty fake mp3s) and a playlists file path."""
    root = tempfile.mkdtemp()
    songs = os.path.join(root, "songs")
    os.makedirs(songs)
    for name in song_names:
        open(os.path.join(songs, name), "w").close()
    return songs, os.path.join(root, "playlists.json")


def new_manager(songs, path):
    return PlaylistManager(file_path=path, songs_folder=songs)


def expect(error_type, action):
    try:
        action()
    except error_type:
        return
    raise AssertionError(f"expected {error_type.__name__}")


def test_library_lists_only_mp3_sorted():
    songs, _ = make_env(("b.mp3", "A.mp3", "notes.txt", "c.webm"))
    assert library.get_songs(songs) == ["A.mp3", "b.mp3"]
    assert library.get_songs(os.path.join(songs, "missing")) == []
    assert library.display_name("My Song.mp3") == "My Song"


def test_create_rules():
    songs, path = make_env()
    m = new_manager(songs, path)
    assert m.create("  Gym ") == "Gym"
    expect(ValueError, lambda: m.create("gym"))       # duplicate, ignoring case
    expect(ValueError, lambda: m.create("   "))       # empty name
    assert m.names() == ["Gym"]


def test_add_insert_and_append():
    songs, path = make_env()
    m = new_manager(songs, path)
    m.create("P")
    m.add_song("P", "a.mp3")                 # append (position None)
    m.add_song("P", "c.mp3")                 # append
    m.add_song("P", "b.mp3", position=1)     # middle
    m.add_song("P", "d.mp3", position=0)     # front
    assert m.songs_in("P") == ["d.mp3", "a.mp3", "b.mp3", "c.mp3"]


def test_add_rejects_bad_input():
    songs, path = make_env()
    m = new_manager(songs, path)
    m.create("P")
    expect(ValueError, lambda: m.add_song("P", "ghost.mp3"))
    expect(IndexError, lambda: m.add_song("P", "a.mp3", position=5))
    expect(KeyError, lambda: m.add_song("Nope", "a.mp3"))
    assert m.songs_in("P") == []


def test_remove_song():
    songs, path = make_env()
    m = new_manager(songs, path)
    m.create("P")
    for s in ("a.mp3", "b.mp3", "c.mp3"):
        m.add_song("P", s)
    assert m.remove_song("P", 1) == "b.mp3"
    assert m.songs_in("P") == ["a.mp3", "c.mp3"]
    expect(IndexError, lambda: m.remove_song("P", 2))


def test_move_song():
    songs, path = make_env()
    m = new_manager(songs, path)
    m.create("P")
    for s in ("a.mp3", "b.mp3", "c.mp3", "d.mp3"):
        m.add_song("P", s)
    m.move_song("P", 0, 2)
    assert m.songs_in("P") == ["b.mp3", "c.mp3", "a.mp3", "d.mp3"]
    m.move_song("P", 3, 0)
    assert m.songs_in("P") == ["d.mp3", "b.mp3", "c.mp3", "a.mp3"]
    expect(IndexError, lambda: m.move_song("P", 0, 9))
    assert len(m.songs_in("P")) == 4           # nothing lost by the failed move


def test_rename_and_delete():
    songs, path = make_env()
    m = new_manager(songs, path)
    m.create("Old")
    m.create("Other")
    m.add_song("Old", "a.mp3")
    expect(ValueError, lambda: m.rename("Old", "other"))
    m.rename("Old", "New")
    assert m.names() == ["New", "Other"] and m.songs_in("New") == ["a.mp3"]
    m.delete("New")
    assert m.names() == ["Other"]
    expect(KeyError, lambda: m.delete("New"))


def test_lookup_ignores_case():
    songs, path = make_env()
    m = new_manager(songs, path)
    m.create("Gym")
    m.add_song("gym", "a.mp3")
    assert m.songs_in("GYM") == ["a.mp3"]


def test_save_and_load_round_trip():
    songs, path = make_env()
    m = new_manager(songs, path)
    m.create("Gym"); m.create("Study")
    m.add_song("Gym", "c.mp3"); m.add_song("Gym", "a.mp3")
    m.add_song("Study", "b.mp3")
    again = new_manager(songs, path)           # simulates restarting the app
    assert again.names() == ["Gym", "Study"]
    assert again.songs_in("Gym") == ["c.mp3", "a.mp3"]
    assert again.songs_in("Study") == ["b.mp3"]


def test_load_skips_missing_mp3_files():
    songs, path = make_env()
    m = new_manager(songs, path)
    m.create("P")
    for s in ("a.mp3", "b.mp3", "c.mp3"):
        m.add_song("P", s)
    os.remove(os.path.join(songs, "b.mp3"))
    assert new_manager(songs, path).songs_in("P") == ["a.mp3", "c.mp3"]


def test_corrupt_file_is_backed_up_not_crashing():
    songs, path = make_env()
    with open(path, "w") as f:
        f.write("{ this is not json")
    m = new_manager(songs, path)
    assert m.names() == []
    assert os.path.isfile(path + ".bak")


def test_wrong_structure_is_handled():
    songs, path = make_env()
    with open(path, "w") as f:
        json.dump(["not", "a", "dict"], f)
    assert new_manager(songs, path).names() == []


def test_no_file_means_no_playlists():
    songs, path = make_env()
    assert new_manager(songs, path).names() == []


def test_linked_list_supports_looping_playback():
    songs, path = make_env()
    m = new_manager(songs, path)
    m.create("P")
    m.add_song("P", "a.mp3"); m.add_song("P", "b.mp3")
    ll = m.get_linked_list("P")
    assert [ll.current(), ll.next(), ll.next()] == ["a.mp3", "b.mp3", "a.mp3"]


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print(f"PASS  {test.__name__}")
    print(f"\nAll {len(tests)} tests passed.")