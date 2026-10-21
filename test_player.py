"""Checks for player.py's state tracking and seek maths, using a fake pygame
(so no sound card is needed).
Run from the project folder with:  python test_player.py
"""
import types

import player as player_module
from player import AudioPlayer, PlayerError


class FakeError(Exception):
    pass


class FakeMusic:
    """Mimics pygame.mixer.music, including the quirk that a paused song is 'not busy'."""

    def __init__(self):
        self.busy = False
        self.pos = 0            # milliseconds played since the last play() call
        self.loaded = None
        self.fail_load = None   # an exception to raise from load()
        self.play_calls = []
        self.pause_calls = 0
        self.volume = None

    def load(self, path):
        if self.fail_load:
            raise self.fail_load
        self.loaded = path

    def play(self, loops=0, start=0.0):
        self.busy = True
        self.pos = 0            # like pygame, the counter restarts and ignores `start`
        self.play_calls.append(start)

    def pause(self):
        self.busy = False
        self.pause_calls += 1

    def unpause(self):
        self.busy = True

    def stop(self):
        self.busy = False

    def get_busy(self):
        return self.busy

    def get_pos(self):
        return self.pos

    def set_volume(self, value):
        self.volume = value


class FakePygame:
    error = FakeError

    def __init__(self):
        self.mixer = types.SimpleNamespace(music=FakeMusic(), init=lambda: None, quit=lambda: None)


def make_player(duration=100.0):
    fake = FakePygame()
    player_module.pygame = fake
    player_module.get_duration = lambda path: duration
    return AudioPlayer(), fake.mixer.music


def expect_player_error(action):
    try:
        action()
    except PlayerError:
        return
    raise AssertionError("expected a PlayerError")


def test_play_sets_state_and_duration():
    p, music = make_player(180.0)
    p.play("/x/song.mp3")
    assert p.state == "playing" and p.duration == 180.0 and music.loaded == "/x/song.mp3"


def test_pause_and_resume():
    p, music = make_player()
    p.play("/x/a.mp3")
    p.pause()
    assert p.state == "paused"
    p.resume()
    assert p.state == "playing"
    p.toggle_pause(); assert p.state == "paused"
    p.toggle_pause(); assert p.state == "playing"


def test_paused_song_is_not_reported_finished():
    p, music = make_player()
    p.play("/x/a.mp3")
    p.pause()                              # fake get_busy() is now False, like real pygame
    assert p.check_finished() is False and p.state == "paused"


def test_finished_is_reported_once():
    p, music = make_player()
    p.play("/x/a.mp3")
    music.busy = False                     # the song ran out
    assert p.check_finished() is True
    assert p.state == "stopped"
    assert p.check_finished() is False


def test_still_playing_is_not_finished():
    p, music = make_player()
    p.play("/x/a.mp3")
    assert p.check_finished() is False and p.state == "playing"


def test_position_counts_from_start():
    p, music = make_player()
    p.play("/x/a.mp3")
    music.pos = 5000
    assert p.position() == 5.0


def test_position_after_seek_adds_the_jump_point():
    p, music = make_player()
    p.play("/x/a.mp3")
    assert p.seek(30) == 30
    assert music.play_calls[-1] == 30
    music.pos = 2000                       # 2 seconds since the jump
    assert p.position() == 32.0
    assert p.seek(60) == 60                # seek again: offsets must not pile up
    music.pos = 1000
    assert p.position() == 61.0


def test_seek_while_paused_stays_paused():
    p, music = make_player()
    p.play("/x/a.mp3")
    p.pause()
    assert music.pause_calls == 1
    p.seek(20)
    assert p.state == "paused" and music.pause_calls == 2   # re-paused after the jump
    p.resume()
    assert p.state == "playing"


def test_seek_is_clamped_to_the_song():
    p, music = make_player(100.0)
    p.play("/x/a.mp3")
    assert p.seek(1000) == 99.5
    assert p.seek(-5) == 0.0


def test_seek_does_nothing_when_stopped_or_length_unknown():
    p, music = make_player()
    assert p.seek(10) is None              # nothing playing
    p2, music2 = make_player(duration=None)
    p2.play("/x/a.mp3")
    assert p2.seek(10) is None             # no known length


def test_position_is_capped_at_duration():
    p, music = make_player(10.0)
    p.play("/x/a.mp3")
    music.pos = 99000
    assert p.position() == 10.0


def test_stop_resets_everything():
    p, music = make_player()
    p.play("/x/a.mp3"); p.seek(40)
    p.stop()
    assert p.state == "stopped" and p.position() == 0.0 and p.duration is None


def test_load_failure_raises_player_error():
    p, music = make_player()
    music.fail_load = FakeError("corrupt file")
    expect_player_error(lambda: p.play("/x/bad.mp3"))
    assert p.state == "stopped"


def test_missing_file_raises_player_error():
    p, music = make_player()
    music.fail_load = FileNotFoundError("no such file")
    expect_player_error(lambda: p.play("/x/gone.mp3"))
    assert p.state == "stopped"


def test_missing_pygame_raises_player_error_with_install_hint():
    player_module.pygame = None
    p = AudioPlayer()
    try:
        p.play("/x/a.mp3")
    except PlayerError as error:
        assert "pygame" in str(error)
    else:
        raise AssertionError("expected a PlayerError")


def test_volume_is_remembered_before_audio_starts():
    p, music = make_player()
    p.set_volume(0.3)
    assert music.volume is None            # audio system not started yet
    p.play("/x/a.mp3")
    assert music.volume == 0.3
    p.set_volume(5)                        # clamped to the valid range
    assert music.volume == 1.0 and p.volume == 1.0


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print(f"PASS  {test.__name__}")
    print(f"\nAll {len(tests)} tests passed.")