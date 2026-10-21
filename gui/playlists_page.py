import tkinter as tk
from tkinter import messagebox, simpledialog


class PlaylistsPage(tk.Frame):
    """Choose a playlist to edit, or create, rename or delete playlists."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.manager = app.manager
        self.names = []  # playlist names, in the same order as the listbox rows

        tk.Label(self, text="Your playlists", font=("TkDefaultFont", 14, "bold")).pack(pady=(15, 5))

        list_frame = tk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=20, pady=5)
        self.listbox = tk.Listbox(list_frame, exportselection=False)
        scrollbar = tk.Scrollbar(list_frame, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scrollbar.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.listbox.bind("<Double-Button-1>", lambda event: self.edit_playlist())

        buttons = tk.Frame(self)
        buttons.pack(pady=5)
        tk.Button(buttons, text="New", width=8, command=self.new_playlist).grid(row=0, column=0, padx=3)
        tk.Button(buttons, text="Edit", width=8, command=self.edit_playlist).grid(row=0, column=1, padx=3)
        tk.Button(buttons, text="Rename", width=8, command=self.rename_playlist).grid(row=0, column=2, padx=3)
        tk.Button(buttons, text="Delete", width=8, command=self.delete_playlist).grid(row=0, column=3, padx=3)

        self.status_label = tk.Label(self, text="", fg="gray")
        self.status_label.pack()

        tk.Button(self, text="Back", command=lambda: app.show_page("home")).pack(pady=(5, 12))

    def on_show(self):
        self.status_label.config(text="")
        self.refresh()

    def refresh(self):
        self.names = self.manager.names()
        self.listbox.delete(0, tk.END)
        for name in self.names:
            count = len(self.manager.songs_in(name))
            noun = "song" if count == 1 else "songs"
            self.listbox.insert(tk.END, f"{name}   ({count} {noun})")
        if not self.names:
            self.status_label.config(text='No playlists yet. Click "New" to create one.')

    def selected_name(self):
        selection = self.listbox.curselection()
        if not selection:
            self.status_label.config(text="Select a playlist first.")
            return None
        return self.names[selection[0]]

    def new_playlist(self):
        name = simpledialog.askstring("New playlist", "Playlist name:", parent=self)
        if name is None:
            return  # cancelled
        try:
            name = self.manager.create(name)
        except ValueError as error:
            messagebox.showerror("Can't create playlist", str(error), parent=self)
            return
        self.app.show_page("editor", playlist_name=name)

    def edit_playlist(self):
        name = self.selected_name()
        if name is not None:
            self.app.show_page("editor", playlist_name=name)

    def rename_playlist(self):
        name = self.selected_name()
        if name is None:
            return
        new_name = simpledialog.askstring(
            "Rename playlist", "New name:", initialvalue=name, parent=self
        )
        if new_name is None:
            return
        try:
            self.manager.rename(name, new_name)
        except ValueError as error:
            messagebox.showerror("Can't rename playlist", str(error), parent=self)
            return
        self.refresh()

    def delete_playlist(self):
        name = self.selected_name()
        if name is None:
            return
        if messagebox.askyesno("Delete playlist", f'Delete "{name}"? This can\'t be undone.', parent=self):
            self.manager.delete(name)
            self.status_label.config(text="")
            self.refresh()