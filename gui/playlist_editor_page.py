import tkinter as tk
from tkinter import messagebox

import library


class PlaylistEditorPage(tk.Frame):
    """Build or change one playlist.

    Left: the downloaded songs. Right: the playlist, in play order.
    Adding, removing and moving songs call the playlist manager, which
    performs the linked list operations and saves the result.
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.manager = app.manager
        self.playlist_name = None
        self.library_files = []  # filenames, in the same order as the library listbox

        self.title_label = tk.Label(self, text="", font=("TkDefaultFont", 14, "bold"))
        self.title_label.pack(pady=(12, 0))
        tk.Label(self, text="Changes are saved automatically.", fg="gray").pack()

        columns = tk.Frame(self)
        columns.pack(fill="both", expand=True, padx=12, pady=8)
        columns.columnconfigure(0, weight=1, uniform="col")
        columns.columnconfigure(1, weight=1, uniform="col")
        columns.rowconfigure(1, weight=1)

        # ----- left column: song library -----
        tk.Label(columns, text="Song library").grid(row=0, column=0)
        self.library_listbox = self.make_listbox(columns, row=1, column=0)
        self.library_listbox.bind("<Double-Button-1>", lambda event: self.add_to_end())

        add_controls = tk.Frame(columns)
        add_controls.grid(row=2, column=0, pady=(6, 0))
        tk.Button(add_controls, text="Add to end", command=self.add_to_end).grid(row=0, column=0, padx=3)
        tk.Label(add_controls, text="or at position").grid(row=0, column=1, padx=(8, 2))
        self.position_var = tk.StringVar(value="1")
        self.position_spin = tk.Spinbox(add_controls, from_=1, to=1, width=4, textvariable=self.position_var)
        self.position_spin.grid(row=0, column=2)
        tk.Button(add_controls, text="Insert", command=self.insert_at_position).grid(row=0, column=3, padx=3)

        # ----- right column: the playlist -----
        tk.Label(columns, text="Playlist (plays in this order, then loops)").grid(row=0, column=1)
        self.playlist_listbox = self.make_listbox(columns, row=1, column=1)

        edit_controls = tk.Frame(columns)
        edit_controls.grid(row=2, column=1, pady=(6, 0))
        tk.Button(edit_controls, text="Move up", command=lambda: self.move_selected(-1)).grid(row=0, column=0, padx=3)
        tk.Button(edit_controls, text="Move down", command=lambda: self.move_selected(1)).grid(row=0, column=1, padx=3)
        tk.Button(edit_controls, text="Remove", command=self.remove_selected).grid(row=0, column=2, padx=3)

        # ----- bottom -----
        self.status_label = tk.Label(self, text="", fg="gray", wraplength=700)
        self.status_label.pack()
        tk.Button(self, text="Back to playlists", command=lambda: app.show_page("playlists")).pack(pady=(4, 12))

    # ---------- setup helpers ----------

    def make_listbox(self, parent, row, column):
        frame = tk.Frame(parent)
        frame.grid(row=row, column=column, sticky="nsew", padx=4)
        listbox = tk.Listbox(frame, exportselection=False)
        scrollbar = tk.Scrollbar(frame, command=listbox.yview)
        listbox.config(yscrollcommand=scrollbar.set)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return listbox

    # ---------- showing the page ----------

    def on_show(self, playlist_name):
        self.playlist_name = playlist_name
        self.title_label.config(text=f"Editing: {playlist_name}")
        self.refresh_library()
        self.refresh_playlist()
        if not self.library_files:
            self.set_status("No songs yet. Download some first, then come back.")
        else:
            self.set_status("")

    def refresh_library(self):
        self.library_files = library.get_songs()
        self.library_listbox.delete(0, tk.END)
        for filename in self.library_files:
            self.library_listbox.insert(tk.END, library.display_name(filename))

    def refresh_playlist(self, select=None):
        songs = self.manager.songs_in(self.playlist_name)
        self.playlist_listbox.delete(0, tk.END)
        for number, filename in enumerate(songs, start=1):
            self.playlist_listbox.insert(tk.END, f"{number}. {library.display_name(filename)}")
        # The "insert at position" box accepts 1 to (number of songs + 1)
        self.position_spin.config(to=len(songs) + 1)
        self.position_var.set(str(len(songs) + 1))
        if select is not None and 0 <= select < len(songs):
            self.playlist_listbox.selection_set(select)
            self.playlist_listbox.see(select)

    # ---------- actions ----------

    def selected_library_song(self):
        selection = self.library_listbox.curselection()
        if not selection:
            self.set_status("Select a song in the library first.")
            return None
        return self.library_files[selection[0]]

    def selected_playlist_index(self):
        selection = self.playlist_listbox.curselection()
        if not selection:
            self.set_status("Select a song in the playlist first.")
            return None
        return selection[0]

    def add_to_end(self):
        filename = self.selected_library_song()
        if filename is not None:
            self.add_song(filename, position=None)

    def insert_at_position(self):
        filename = self.selected_library_song()
        if filename is None:
            return
        try:
            position = int(self.position_var.get())
        except ValueError:
            self.set_status("Position must be a whole number.")
            return
        self.add_song(filename, position=position - 1)  # the GUI counts from 1, the list from 0

    def add_song(self, filename, position):
        try:
            self.manager.add_song(self.playlist_name, filename, position)
        except (ValueError, IndexError) as error:
            messagebox.showerror("Can't add song", str(error), parent=self)
            return
        songs = self.manager.songs_in(self.playlist_name)
        added_at = len(songs) - 1 if position is None else position
        self.refresh_playlist(select=added_at)
        self.set_status(f'Added "{library.display_name(filename)}" at position {added_at + 1}.')

    def remove_selected(self):
        index = self.selected_playlist_index()
        if index is None:
            return
        try:
            filename = self.manager.remove_song(self.playlist_name, index)
        except IndexError as error:
            messagebox.showerror("Can't remove song", str(error), parent=self)
            return
        remaining = len(self.manager.songs_in(self.playlist_name))
        self.refresh_playlist(select=min(index, remaining - 1))
        self.set_status(f'Removed "{library.display_name(filename)}".')

    def move_selected(self, step):
        index = self.selected_playlist_index()
        if index is None:
            return
        new_index = index + step
        if new_index < 0 or new_index >= len(self.manager.songs_in(self.playlist_name)):
            return  # already at the top or bottom
        try:
            self.manager.move_song(self.playlist_name, index, new_index)
        except IndexError as error:
            messagebox.showerror("Can't move song", str(error), parent=self)
            return
        self.refresh_playlist(select=new_index)

    def set_status(self, text):
        self.status_label.config(text=text)