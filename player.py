import os
import subprocess

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")  # silence pygame's startup banner
try:
    import pygame
except ImportError:
    pygame = None  # the rest of the app still works; playing shows an install hint

INSTALL_HINT = (
    "pygame is not installed.\n"
    "On Arch:  sudo pacman -S python-pygame\n"
    "or:       pip install --user pygame"
)


class PlayerError(Exception):
    """Raised when audio can't be started or a song can't be played."""


def get_duration(path):
    """Length of the song in seconds, or None if it can't be worked out.

    Uses ffprobe (installed with ffmpeg). Falls back to pygame, which has to
    decode the whole file and is slower.
    """
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=10,
        )
        return float(result.stdout.strip())
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    try:
        return pygame.mixer.Sound(path).get_length()
    except (AttributeError, pygame.error, OSError):
        return None


class AudioPlayer:
    """Plays one mp3 at a time with pygame.mixer.

    Tracks its own state ("stopped", "playing", "paused") because pygame
    reports a paused song as "not busy", which looks the same as a finished one.
    """

    def __init__(self):
        self.state = "stopped"
        self.duration = None      # length of the current song in seconds (None if unknown)
        self.start_offset = 0.0   # where playback (re)started, in seconds
        self._volume = 0.7
        self._ready = False

    def _ensure_ready(self):
        """Start the audio system the first time it's needed."""
        if pygame is None:
            raise PlayerError(INSTALL_HINT)
        if not self._ready:
            try:
                pygame.mixer.init()
            except pygame.error as error:
                raise PlayerError(f"Couldn't start the audio system: {error}")
            self._ready = True
            pygame.mixer.music.set_volume(self._volume)

    def play(self, path):
        """Load and start a song from the beginning."""
        self._ensure_ready()
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
        except (pygame.error, OSError) as error:
            self.state = "stopped"
            raise PlayerError(f"Can't play {os.path.basename(path)}: {error}")
        self.state = "playing"
        self.start_offset = 0.0
        self.duration = get_duration(path)

    def pause(self):
        if self.state == "playing":
            pygame.mixer.music.pause()
            self.state = "paused"

    def resume(self):
        if self.state == "paused":
            pygame.mixer.music.unpause()
            self.state = "playing"

    def toggle_pause(self):
        if self.state == "playing":
            self.pause()
        elif self.state == "paused":
            self.resume()

    def stop(self):
        if self._ready:
            pygame.mixer.music.stop()
        self.state = "stopped"
        self.duration = None
        self.start_offset = 0.0

    def seek(self, seconds):
        """Jump to `seconds` in the current song (stays paused if it was paused).

        Returns the position actually jumped to, or None if seeking isn't possible.
        """
        if self.state == "stopped" or not self.duration:
            return None
        # Stay just short of the very end, where jumping can fail
        seconds = max(0.0, min(seconds, self.duration - 0.5))
        was_paused = self.state == "paused"
        try:
            pygame.mixer.music.play(start=seconds)
        except pygame.error as error:
            raise PlayerError(f"Couldn't seek in this file: {error}")
        self.start_offset = seconds
        if was_paused:
            pygame.mixer.music.pause()
        return seconds

    def position(self):
        """Where we are in the song, in seconds.

        pygame's get_pos() only counts time played since the last play() call,
        so after a seek we add the point we jumped to.
        """
        if self.state == "stopped":
            return 0.0
        position = self.start_offset + max(0, pygame.mixer.music.get_pos()) / 1000
        if self.duration:
            position = min(position, self.duration)
        return position

    def check_finished(self):
        """True (once) if the song has just ended by itself. Call this regularly."""
        if self.state == "playing" and not pygame.mixer.music.get_busy():
            self.state = "stopped"
            self.duration = None
            return True
        return False

    @property
    def volume(self):
        """Current volume from 0.0 to 1.0."""
        return self._volume

    def set_volume(self, fraction):
        """Volume from 0.0 to 1.0. Remembered even before the audio system starts."""
        self._volume = max(0.0, min(1.0, fraction))
        if self._ready:
            pygame.mixer.music.set_volume(self._volume)

    def shutdown(self):
        if self._ready:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
            self._ready = False
        self.state = "stopped"