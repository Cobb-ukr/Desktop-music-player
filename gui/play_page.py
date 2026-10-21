import tkinter as tk
from tkinter import messagebox, ttk

import library
from gui.seek_bar import SeekBar
from play_session import PlaySession
from player import PlayerError

POLL_MS = 250            # how often we check on the song that's playing
RESTART_AFTER = 3        # "Previous" restarts the song if it has played longer than this (seconds)


class PlayPage(tk.Frame):
    """Play a playlist in a loop, with a "Play next" queue.

    Which song comes next is decided by PlaySession (playlist + queue);
    the audio itself is handled by AudioPlayer. This page just connects
    them to the buttons.
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.manager = app.manager
        self.player = app.player  # shared with the other play page
        self.session = None
        self.playlist_files = []  # filenames shown in the playlist listbox, in order

        tk.Label(self, text="Play playlist", font=("TkDefaultFont", 14, "bold")).pack(pady=(12, 6))

        # ----- choose a playlist -----
        chooser = tk.Frame(self)
        chooser.pack()
        tk.Label(chooser, text="Playlist:").pack(side="left", padx=(0, 6))
        self.playlist_combo = ttk.Combobox(chooser, state="readonly", width=30)
        self.playlist_combo.pack(side="left")
        tk.Button(chooser, text="Start", command=self.start_playlist).pack(side="left", padx=6)

        # ----- two lists: playlist and queue -----
        columns = tk.Frame(self)
        columns.pack(fill="both", expand=True, padx=12, pady=8)
        columns.columnconfigure(0, weight=3, uniform="col")
        columns.columnconfigure(1, weight=2, uniform="col")
        columns.rowconfigure(1, weight=1)

        tk.Label(columns, text="Playlist (loops forever)").grid(row=0, column=0)
        self.playlist_listbox = self.make_listbox(columns, column=0)
        self.playlist_listbox.bind("<Double-Button-1>", lambda event: self.play_selected())
        playlist_buttons = tk.Frame(columns)
        playlist_buttons.grid(row=2, column=0, pady=(6, 0))
        tk.Button(playlist_buttons, text="Play this song", command=self.play_selected).grid(row=0, column=0, padx=3)
        tk.Button(playlist_buttons, text="Play next (add to queue)", command=self.queue_selected).grid(row=0, column=1, padx=3)

        tk.Label(columns, text="Up next (queue)").grid(row=0, column=1)
        self.queue_listbox = self.make_listbox(columns, column=1)
        queue_buttons = tk.Frame(columns)
        queue_buttons.grid(row=2, column=1, pady=(6, 0))
        tk.Button(queue_buttons, text="Remove", command=self.remove_from_queue).grid(row=0, column=0, padx=3)
        tk.Button(queue_buttons, text="Clear queue", command=self.clear_queue).grid(row=0, column=1, padx=3)

        # ----- now playing, seek bar, controls -----
        self.now_playing_label = tk.Label(
            self, text="Nothing playing", font=("TkDefaultFont", 11, "bold"), wraplength=780
        )
        self.now_playing_label.pack()

        self.seek_bar = SeekBar(self, on_seek=self.seek_to)
        self.seek_bar.pack(fill="x", padx=30, pady=4)

        controls = tk.Frame(self)
        controls.pack(pady=4)
        self.prev_button = tk.Button(controls, text="Previous", width=9, command=self.previous)
        self.prev_button.grid(row=0, column=0, padx=4)
        self.play_pause_button = tk.Button(controls, text="Play", width=9, command=self.toggle_play_pause)
        self.play_pause_button.grid(row=0, column=1, padx=4)
        self.next_button = tk.Button(controls, text="Next", width=9, command=self.advance)
        self.next_button.grid(row=0, column=2, padx=4)
        self.stop_button = tk.Button(controls, text="Stop", width=9, command=self.stop_clicked)
        self.stop_button.grid(row=0, column=3, padx=4)

        volume_frame = tk.Frame(self)
        volume_frame.pack()
        tk.Label(volume_frame, text="Volume").pack(side="left", padx=(0, 6))
        self.volume_scale = tk.Scale(
            volume_frame, from_=0, to=100, orient="horizontal", length=240, command=self.on_volume
        )
        self.volume_scale.set(70)
        self.volume_scale.pack(side="left")

        self.status_label = tk.Label(self, text="", fg="gray", wraplength=780)
        self.status_label.pack(pady=(4, 2))
        tk.Button(self, text="Back", command=self.go_back).pack(pady=(2, 12))

        self.update_buttons()
        self.poll()

    # ---------- setup helpers ----------

    def make_listbox(self, parent, column):
        frame = tk.Frame(parent)
        frame.grid(row=1, column=column, sticky="nsew", padx=4)
        listbox = tk.Listbox(frame, exportselection=False)
        scrollbar = tk.Scrollbar(frame, command=listbox.yview)
        listbox.config(yscrollcommand=scrollbar.set)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return listbox

    # ---------- page lifecycle ----------

    def on_show(self):
        self.clear_session()
        self.volume_scale.set(round(self.player.volume * 100))
        names = self.manager.names()
        self.playlist_combo.config(values=names)
        if names:
            if self.playlist_combo.get() not in names:
                self.playlist_combo.set(names[0])
            self.set_status("Choose a playlist and click Start.")
        else:
            self.playlist_combo.set("")
            self.set_status("You don't have any playlists yet. Create one first.")

    def go_back(self):
        self.clear_session()
        self.app.show_page("home")

    def clear_session(self):
        self.stop_playback()
        self.session = None
        self.playlist_files = []
        self.refresh_playlist()
        self.refresh_queue()

    # ---------- starting and playing ----------

    def start_playlist(self):
        name = self.playlist_combo.get()
        if not name:
            self.set_status("Choose a playlist first.")
            return
        playlist = self.manager.get_linked_list(name)
        if playlist.is_empty():
            self.set_status(f'"{name}" is empty. Add songs to it in "Create / edit playlists".')
            return
        self.stop_playback()
        self.session = PlaySession(playlist)
        self.playlist_files = playlist.to_list()
        self.play_song(self.session.start())

    def play_song(self, filename):
        """Play `filename`. Returns False (and stops) if it can't be played."""
        try:
            self.player.play(library.song_path(filename))
        except PlayerError as error:
            self.stop_playback()
            messagebox.showerror("Can't play song", str(error), parent=self)
            return False
        self.seek_bar.set_duration(self.player.duration)
        self.set_status("Playing." if self.player.duration else "Playing. (Couldn't read the song length, so seeking is off.)")
        self.refresh_all()
        return True

    def advance(self):
        """Go to the next song: queued songs first, then the next playlist song."""
        if self.session is None:
            return
        song = self.session.next()
        if song is None:
            self.stop_playback()
            return
        self.play_song(song)

    def previous(self):
        if self.session is None:
            return
        # Like most players: if the song has been playing a while, restart it instead
        if self.player.state != "stopped" and self.player.position() > RESTART_AFTER:
            self.seek_to(0)
            return
        song = self.session.prev()
        if song is not None:
            self.play_song(song)

    def toggle_play_pause(self):
        if self.session is None:
            self.set_status("Choose a playlist and click Start.")
            return
        if self.player.state == "stopped":
            self.play_song(self.session.now_playing)
        else:
            self.player.toggle_pause()
            self.set_status("Paused." if self.player.state == "paused" else "Playing.")
            self.update_buttons()

    def stop_clicked(self):
        self.stop_playback()
        if self.session is not None:
            self.set_status("Stopped.")

    def stop_playback(self):
        self.player.stop()
        self.seek_bar.reset()
        self.refresh_all()

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

    # ---------- playlist list actions ----------

    def selected_playlist_index(self):
        selection = self.playlist_listbox.curselection()
        return selection[0] if selection else None

    def play_selected(self):
        if self.session is None:
            self.set_status("Choose a playlist and click Start first.")
            return
        index = self.selected_playlist_index()
        if index is None:
            self.set_status("Select a song in the playlist first.")
            return
        self.play_song(self.session.jump_to(index))

    def queue_selected(self):
        if self.session is None:
            self.set_status("Choose a playlist and click Start first.")
            return
        index = self.selected_playlist_index()
        if index is None:
            self.set_status("Select a song in the playlist to play next.")
            return
        filename = self.playlist_files[index]
        self.session.queue_song(filename)
        self.refresh_queue()
        self.set_status(f'"{library.display_name(filename)}" will play next.')

    # ---------- queue list actions ----------

    def remove_from_queue(self):
        selection = self.queue_listbox.curselection()
        if self.session is None or not selection:
            self.set_status("Select a song in the queue first.")
            return
        self.session.remove_from_queue(selection[0])
        self.refresh_queue()

    def clear_queue(self):
        if self.session is not None:
            self.session.clear_queue()
            self.refresh_queue()

    # ---------- checking on the song while it plays ----------

    def poll(self):
        """Runs every POLL_MS: moves the seek bar, and starts the next song when one ends."""
        if self.app.current_page is self and self.player.state == "playing":
            if self.player.check_finished():
                self.advance()  # this is what makes the playlist loop
            else:
                self.seek_bar.update_position(self.player.position())
        self.after(POLL_MS, self.poll)

    # ---------- display ----------

    def refresh_all(self):
        self.refresh_now_playing()
        self.refresh_playlist()
        self.refresh_queue()
        self.update_buttons()

    def refresh_now_playing(self):
        if self.session is not None and self.session.now_playing and self.player.state != "stopped":
            text = library.display_name(self.session.now_playing)
            if self.session.from_queue:
                text += "   (from queue)"
        else:
            text = "Nothing playing"
        self.now_playing_label.config(text=text)

    def refresh_playlist(self):
        selection = self.playlist_listbox.curselection()
        playing_index = None
        if self.session is not None and self.player.state != "stopped":
            playing_index = self.session.playing_index()
        self.playlist_listbox.delete(0, tk.END)
        for index, filename in enumerate(self.playlist_files):
            marker = "▶ " if index == playing_index else "    "
            self.playlist_listbox.insert(tk.END, f"{marker}{index + 1}. {library.display_name(filename)}")
        if selection and selection[0] < len(self.playlist_files):
            self.playlist_listbox.selection_set(selection[0])

    def refresh_queue(self):
        self.queue_listbox.delete(0, tk.END)
        if self.session is not None:
            for number, filename in enumerate(self.session.queue.to_list(), start=1):
                self.queue_listbox.insert(tk.END, f"{number}. {library.display_name(filename)}")

    def update_buttons(self):
        state = self.player.state
        self.play_pause_button.config(
            text={"playing": "Pause", "paused": "Resume"}.get(state, "Play")
        )
        has_session = self.session is not None
        self.prev_button.config(state="normal" if has_session else "disabled")
        self.next_button.config(state="normal" if has_session else "disabled")
        self.stop_button.config(state="normal" if state != "stopped" else "disabled")

    def set_status(self, text):
        self.status_label.config(text=text)