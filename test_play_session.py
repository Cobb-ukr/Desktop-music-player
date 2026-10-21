"""Checks for PlaySession (playlist loop + "Play next" queue).
Run from the project folder with:  python test_play_session.py
"""
from data_structures.circular_doubly_linked_list import CircularDoublyLinkedList
from play_session import PlaySession


def make_session(*songs):
    playlist = CircularDoublyLinkedList()
    for song in songs:
        playlist.append(song)
    return PlaySession(playlist)


def test_start_plays_first_song():
    s = make_session("A", "B", "C")
    assert s.start() == "A" and s.now_playing == "A" and not s.from_queue


def test_next_loops_forever():
    s = make_session("A", "B", "C")
    s.start()
    assert [s.next() for _ in range(7)] == ["B", "C", "A", "B", "C", "A", "B"]


def test_single_song_playlist_loops_to_itself():
    s = make_session("A")
    s.start()
    assert s.next() == "A" and s.next() == "A"


def test_prev_wraps_backwards():
    s = make_session("A", "B", "C")
    s.start()
    assert [s.prev(), s.prev(), s.prev()] == ["C", "B", "A"]


def test_queue_songs_jump_ahead_in_order():
    s = make_session("A", "B", "C", "D")
    s.start()                              # playing A
    s.queue_song("D")
    s.queue_song("C")
    assert s.next() == "D" and s.from_queue
    assert s.next() == "C" and s.from_queue
    assert s.next() == "B" and not s.from_queue   # back to the playlist, after A


def test_queue_does_not_move_playlist_pointer():
    s = make_session("A", "B", "C")
    s.start(); s.next()                    # playing B
    s.queue_song("A")
    assert s.next() == "A"                 # queued
    assert s.playlist.current() == "B"     # pointer still on B
    assert s.next() == "C"                 # continues after B


def test_same_song_can_be_queued_twice():
    s = make_session("A", "B")
    s.start()
    s.queue_song("B"); s.queue_song("B")
    assert [s.next(), s.next(), s.next()] == ["B", "B", "B"]


def test_prev_from_queued_song_returns_to_playlist_song():
    s = make_session("A", "B", "C")
    s.start(); s.next()                    # playing B
    s.queue_song("C")
    assert s.next() == "C" and s.from_queue
    assert s.prev() == "B" and not s.from_queue


def test_jump_to_position():
    s = make_session("A", "B", "C", "D")
    s.start()
    assert s.jump_to(2) == "C" and not s.from_queue
    assert s.next() == "D"


def test_playing_index():
    s = make_session("A", "B", "C")
    s.start()
    assert s.playing_index() == 0
    s.next()
    assert s.playing_index() == 1
    s.queue_song("A")
    s.next()
    assert s.playing_index() is None       # a queued song has no playlist position


def test_remove_from_queue_and_clear():
    s = make_session("A", "B", "C")
    s.start()
    for song in ("A", "B", "C"):
        s.queue_song(song)
    assert s.remove_from_queue(1) == "B"
    assert s.queue.to_list() == ["A", "C"]
    s.clear_queue()
    assert s.queue.is_empty()
    assert s.next() == "B"                 # nothing queued, so the playlist continues


def test_empty_playlist():
    s = make_session()
    assert s.start() is None
    assert s.next() is None and s.prev() is None


def test_start_again_resets_to_first_song():
    s = make_session("A", "B", "C")
    s.start(); s.next(); s.next()
    assert s.start() == "A"


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print(f"PASS  {test.__name__}")
    print(f"\nAll {len(tests)} tests passed.")