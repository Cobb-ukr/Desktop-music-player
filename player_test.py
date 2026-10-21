"""Standalone test: pick an mp3 from the songs folder and play it with pygame.mixer.

Put this file in the music_player folder (next to the songs/ folder) and run:

    python player_test.py

It doesn't use any other file from the project. Song lengths come from ffprobe
(installed together with ffmpeg); if that's missing it falls back to pygame.
"""
import os
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, ttk

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")  # silence pygame's startup banner
try:
    import pygame
except ImportError:
    sys.exit(
        "pygame is not installed.\n"
        "On Arch:  sudo pacman -S python-pygame\n"
        "or:       pip install --user pygame"
    )

SONGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "songs")
POLL_MS = 250  # how often we check the playback state


def format_time(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"


def get_duration(path):
    """Length of the song in seconds, or None if it can't be worked out."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=10,
        )
        return float(result.stdout.strip())
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    # Fallback: decode the whole file just to measure it (slower, uses more memory)
    try:
        return pygame.mixer.Sound(path).get_length()
    except (pygame.error, OSError):
        return None


class PlayerTestApp:
    def __init__(self, root):
        self.root = root
        root.title("Song player test")
        root.geometry("480x580")
        root.protocol("WM_DELETE_WINDOW", self.close)

        self.songs = []            # mp3 filenames, in the same order as the listbox rows
        self.current_song = None   # filename of the song that is loaded
        self.state = "stopped"     # "stopped", "playing" or "paused"
        self.duration = None       # length of the current song in seconds
        self.start_offset = 0.0    # where in the song playback (re)started, in seconds
        self.dragging = False      # True while the user is dragging the seek bar

        # ----- song list -----
        tk.Label(root, text="Pick a song", font=("TkDefaultFont", 14, "bold")).pack(pady=(12, 4))

        list_frame = tk.Frame(root)
        list_frame.pack(fill="both", expand=True, padx=15)
        self.listbox = tk.Listbox(list_frame, exportselection=False)
        scrollbar = tk.Scrollbar(list_frame, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scrollbar.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.listbox.bind("<Double-Button-1>", lambda event: self.play_selected())

        list_buttons = tk.Frame(root)
        list_buttons.pack(pady=(6, 0))
        tk.Button(list_buttons, text="Refresh list", command=self.refresh_songs).pack(side="left", padx=4)
        self.count_label = tk.Label(list_buttons, text="", fg="gray")
        self.count_label.pack(side="left", padx=4)

        # ----- now playing -----
        divider = tk.Frame(root, height=1, bg="#cccccc")
        divider.pack(fill="x", padx=15, pady=10)

        self.now_playing_label = tk.Label(
            root, text="Nothing playing", font=("TkDefaultFont", 11, "bold"), wraplength=440
        )
        self.now_playing_label.pack()

        # ----- seek bar:  elapsed | ------o-------- | total -----
        seek_frame = tk.Frame(root)
        seek_frame.pack(fill="x", padx=15, pady=6)
        self.time_label = tk.Label(seek_frame, text="0:00", width=5, font=("TkFixedFont", 11))
        self.time_label.pack(side="left")
        self.total_label = tk.Label(seek_frame, text="0:00", width=5, font=("TkFixedFont", 11))
        self.total_label.pack(side="right")
        self.seek_scale = ttk.Scale(seek_frame, from_=0, to=1, orient="horizontal")
        self.seek_scale.pack(side="left", fill="x", expand=True, padx=6)
        # We handle the mouse ourselves so that a click jumps straight to that spot
        # and dragging doesn't fight with the timer that moves the bar as the song plays.
        self.seek_scale.bind("<ButtonPress-1>", self.on_seek_press)
        self.seek_scale.bind("<B1-Motion>", self.on_seek_drag)
        self.seek_scale.bind("<ButtonRelease-1>", self.on_seek_release)
        self.reset_seek_bar()

        # ----- playback buttons -----
        controls = tk.Frame(root)
        controls.pack(pady=6)
        self.play_button = tk.Button(controls, text="Play", width=9, command=self.play_selected)
        self.play_button.grid(row=0, column=0, padx=4)
        self.pause_button = tk.Button(controls, text="Pause", width=9, command=self.toggle_pause)
        self.pause_button.grid(row=0, column=1, padx=4)
        self.stop_button = tk.Button(controls, text="Stop", width=9, command=self.stop)
        self.stop_button.grid(row=0, column=2, padx=4)

        # ----- volume -----
        volume_frame = tk.Frame(root)
        volume_frame.pack(pady=4)
        tk.Label(volume_frame, text="Volume").pack(side="left", padx=(0, 6))
        self.volume_scale = tk.Scale(
            volume_frame, from_=0, to=100, orient="horizontal", length=240, command=self.on_volume
        )
        self.volume_scale.set(70)
        self.volume_scale.pack(side="left")

        self.status_label = tk.Label(root, text="", fg="gray", wraplength=440)
        self.status_label.pack(pady=(4, 12))

        self.refresh_songs()
        self.update_buttons()
        self.poll()

    # ---------- song list ----------

    def refresh_songs(self):
        if os.path.isdir(SONGS_DIR):
            files = [f for f in os.listdir(SONGS_DIR) if f.lower().endswith(".mp3")]
            self.songs = sorted(files, key=str.lower)
        else:
            self.songs = []

        self.listbox.delete(0, tk.END)
        for filename in self.songs:
            self.listbox.insert(tk.END, os.path.splitext(filename)[0])

        if self.songs:
            self.count_label.config(text=f"{len(self.songs)} songs found")
            self.set_status("Select a song and click Play (or double-click it).")
        else:
            self.count_label.config(text="")
            self.set_status(f"No mp3 files found in:\n{SONGS_DIR}\nDownload some songs first.")

    # ---------- playback actions ----------

    def play_selected(self):
        selection = self.listbox.curselection()
        if not selection:
            self.set_status("Select a song first.")
            return
        filename = self.songs[selection[0]]
        path = os.path.join(SONGS_DIR, filename)
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
        except pygame.error as error:
            self.state = "stopped"
            self.reset_seek_bar()
            self.update_buttons()
            messagebox.showerror("Can't play song", f"{filename}\n\n{error}")
            return

        self.current_song = filename
        self.state = "playing"
        self.start_offset = 0.0
        self.dragging = False
        self.duration = get_duration(path)
        self.setup_seek_bar()
        self.now_playing_label.config(text=os.path.splitext(filename)[0])
        self.set_status("Playing." if self.duration else "Playing. (Couldn't read the song length, so seeking is off.)")
        self.update_buttons()

    def toggle_pause(self):
        if self.state == "playing":
            pygame.mixer.music.pause()
            self.state = "paused"
            self.set_status("Paused.")
        elif self.state == "paused":
            pygame.mixer.music.unpause()
            self.state = "playing"
            self.set_status("Playing.")
        self.update_buttons()

    def stop(self):
        pygame.mixer.music.stop()
        self.state = "stopped"
        self.dragging = False
        self.now_playing_label.config(text="Nothing playing")
        self.reset_seek_bar()
        self.set_status("Stopped.")
        self.update_buttons()

    def on_volume(self, value):
        pygame.mixer.music.set_volume(float(value) / 100)

    # ---------- seeking ----------

    def current_position(self):
        """Where we are in the song, in seconds.

        pygame's get_pos() only counts the time played since the last play() call,
        so after a seek we add the point we jumped to.
        """
        position = self.start_offset + max(0, pygame.mixer.music.get_pos()) / 1000
        if self.duration:
            position = min(position, self.duration)
        return position

    def seek_to(self, seconds):
        """Jump to `seconds` in the current song (keeps it paused if it was paused)."""
        if self.state == "stopped" or not self.duration:
            return
        # Stay just short of the very end, where jumping can fail
        seconds = max(0.0, min(seconds, self.duration - 0.5))
        was_paused = self.state == "paused"
        try:
            pygame.mixer.music.play(start=seconds)
        except pygame.error as error:
            self.set_status(f"Couldn't seek in this file: {error}")
            return
        self.start_offset = seconds
        if was_paused:
            pygame.mixer.music.pause()
        self.show_position(seconds)

    def on_seek_press(self, event):
        if self.state != "stopped" and self.duration:
            self.dragging = True
            self.drag_to(event)
        return "break"  # skip the default behaviour (which moves in small steps)

    def on_seek_drag(self, event):
        if self.dragging:
            self.drag_to(event)
        return "break"

    def on_seek_release(self, event):
        if self.dragging:
            self.dragging = False
            self.seek_to(self.seek_scale.get())
        return "break"

    def drag_to(self, event):
        """Move the bar to where the mouse is, without seeking yet."""
        slider_margin = 7  # rough half-width of the slider handle
        usable_width = max(1, self.seek_scale.winfo_width() - 2 * slider_margin)
        fraction = min(1.0, max(0.0, (event.x - slider_margin) / usable_width))
        self.show_position(fraction * self.duration)

    def show_position(self, seconds):
        self.time_label.config(text=format_time(seconds))
        if self.duration:
            self.seek_scale.set(seconds)

    def setup_seek_bar(self):
        self.show_position(0)
        if self.duration:
            self.seek_scale.config(to=self.duration)
            self.seek_scale.state(["!disabled"])
            self.total_label.config(text=format_time(self.duration))
        else:
            self.seek_scale.state(["disabled"])
            self.total_label.config(text="--:--")
        self.time_label.config(text="0:00")
        self.seek_scale.set(0)

    def reset_seek_bar(self):
        self.duration = None
        self.start_offset = 0.0
        self.seek_scale.config(to=1)
        self.seek_scale.set(0)
        self.seek_scale.state(["disabled"])
        self.time_label.config(text="0:00")
        self.total_label.config(text="0:00")

    # ---------- checking on the song while it plays ----------

    def poll(self):
        """Runs every POLL_MS. Moves the seek bar and notices when a song ends."""
        if self.state == "playing":
            if pygame.mixer.music.get_busy():
                if not self.dragging:
                    self.show_position(self.current_position())
            else:
                # Not paused by us, but nothing is playing any more: the song finished.
                # (This is the moment a playlist player would move on to the next song.)
                finished = os.path.splitext(self.current_song)[0]
                self.state = "stopped"
                self.dragging = False
                self.now_playing_label.config(text="Nothing playing")
                self.reset_seek_bar()
                self.set_status(f'Finished "{finished}".')
                self.update_buttons()
        self.root.after(POLL_MS, self.poll)

    # ---------- GUI helpers ----------

    def update_buttons(self):
        self.pause_button.config(
            text="Resume" if self.state == "paused" else "Pause",
            state="normal" if self.state in ("playing", "paused") else "disabled",
        )
        self.stop_button.config(state="normal" if self.state != "stopped" else "disabled")

    def set_status(self, text):
        self.status_label.config(text=text)

    def close(self):
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        self.root.destroy()


def main():
    root = tk.Tk()
    try:
        pygame.mixer.init()
    except pygame.error as error:
        root.withdraw()
        messagebox.showerror("Audio error", f"Couldn't start the audio system:\n\n{error}")
        root.destroy()
        return
    PlayerTestApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()