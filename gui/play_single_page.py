import tkinter as tk
from tkinter import messagebox

import library
from gui.seek_bar import SeekBar
from player import PlayerError

POLL_MS = 250  # how often we check on the song that's playing


class PlaySinglePage(tk.Frame):
    """Pick any song from the songs folder and play it, with no playlist involved."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.player = app.player  # shared with the other play page
        self.songs = []           # mp3 filenames, in the same order as the listbox rows

        # ----- song list -----
        tk.Label(self, text="Play single", font=("TkDefaultFont", 14, "bold")).pack(pady=(12, 4))

        list_frame = tk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=15)
        self.listbox = tk.Listbox(list_frame, exportselection=False)
        scrollbar = tk.Scrollbar(list_frame, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scrollbar.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.listbox.bind("<Double-Button-1>", lambda event: self.play_selected())

        list_buttons = tk.Frame(self)
        list_buttons.pack(pady=(6, 0))
        tk.Button(list_buttons, text="Refresh list", command=self.refresh_songs).pack(side="left", padx=4)
        self.count_label = tk.Label(list_buttons, text="", fg="gray")
        self.count_label.pack(side="left", padx=4)

        # ----- now playing -----
        divider = tk.Frame(self, height=1, bg="#cccccc")
        divider.pack(fill="x", padx=15, pady=10)

        self.now_playing_label = tk.Label(
            self, text="Nothing playing", font=("TkDefaultFont", 11, "bold"), wraplength=440
        )
        self.now_playing_label.pack()

        self.seek_bar = SeekBar(self, on_seek=self.seek_to)
        self.seek_bar.pack(fill="x", padx=15, pady=6)

        # ----- playback buttons -----
        controls = tk.Frame(self)
        controls.pack(pady=6)
        self.play_button = tk.Button(controls, text="Play", width=9, command=self.play_selected)
        self.play_button.grid(row=0, column=0, padx=4)
        self.pause_button = tk.Button(controls, text="Pause", width=9, command=self.toggle_pause)
        self.pause_button.grid(row=0, column=1, padx=4)
        self.stop_button = tk.Button(controls, text="Stop", width=9, command=self.stop_clicked)
        self.stop_button.grid(row=0, column=2, padx=4)

        # ----- volume -----
        volume_frame = tk.Frame(self)
        volume_frame.pack(pady=4)
        tk.Label(volume_frame, text="Volume").pack(side="left", padx=(0, 6))
        self.volume_scale = tk.Scale(
            volume_frame, from_=0, to=100, orient="horizontal", length=240, command=self.on_volume
        )
        self.volume_scale.set(70)
        self.volume_scale.pack(side="left")

        self.status_label = tk.Label(self, text="", fg="gray", wraplength=440)
        self.status_label.pack(pady=(4, 4))
        tk.Button(self, text="Back", command=self.go_back).pack(pady=(2, 12))

        self.update_buttons()
        self.poll()

    # ---------- page lifecycle ----------

    def on_show(self):
        self.stop_playback()
        self.volume_scale.set(round(self.player.volume * 100))
        self.refresh_songs()

    def go_back(self):
        self.stop_playback()
        self.app.show_page("home")

    # ---------- song list ----------

    def refresh_songs(self):
        self.songs = library.get_songs()
        self.listbox.delete(0, tk.END)
        for filename in self.songs:
            self.listbox.insert(tk.END, library.display_name(filename))

        if self.songs:
            self.count_label.config(text=f"{len(self.songs)} songs found")
            self.set_status("Select a song and click Play (or double-click it).")
        else:
            self.count_label.config(text="")
            self.set_status("No songs found. Download some first.")

    # ---------- playback actions ----------

    def play_selected(self):
        selection = self.listbox.curselection()
        if not selection:
            self.set_status("Select a song first.")
            return
        filename = self.songs[selection[0]]
        try:
            self.player.play(library.song_path(filename))
        except PlayerError as error:
            self.stop_playback()
            messagebox.showerror("Can't play song", str(error), parent=self)
            return

        self.seek_bar.set_duration(self.player.duration)
        self.now_playing_label.config(text=library.display_name(filename))
        self.set_status(
            "Playing." if self.player.duration
            else "Playing. (Couldn't read the song length, so seeking is off.)"
        )
        self.update_buttons()

    def toggle_pause(self):
        if self.player.state == "stopped":
            return
        self.player.toggle_pause()
        self.set_status("Paused." if self.player.state == "paused" else "Playing.")
        self.update_buttons()

    def stop_clicked(self):
        self.stop_playback()
        self.set_status("Stopped.")

    def stop_playback(self):
        self.player.stop()
        self.seek_bar.reset()
        self.now_playing_label.config(text="Nothing playing")
        self.update_buttons()

    def seek_to(self, seconds):
        try:
            jumped_to = self.player.seek(seconds)
        except PlayerError as error:
            self.set_status(str(error))
            return
        if jumped_to is not None:
            self.seek_bar.update_position(jumped_to)

    def on_volume(self, value):
        self.player.set_volume(float(value) / 100)

    # ---------- checking on the song while it plays ----------

    def poll(self):
        """Runs every POLL_MS: moves the seek bar and notices when the song ends."""
        if self.app.current_page is self and self.player.state == "playing":
            if self.player.check_finished():
                finished = self.now_playing_label.cget("text")
                self.seek_bar.reset()
                self.now_playing_label.config(text="Nothing playing")
                self.set_status(f'Finished "{finished}".')
                self.update_buttons()
            else:
                self.seek_bar.update_position(self.player.position())
        self.after(POLL_MS, self.poll)

    # ---------- display ----------

    def update_buttons(self):
        state = self.player.state
        self.pause_button.config(
            text="Resume" if state == "paused" else "Pause",
            state="normal" if state in ("playing", "paused") else "disabled",
        )
        self.stop_button.config(state="normal" if state != "stopped" else "disabled")

    def set_status(self, text):
        self.status_label.config(text=text)