import tkinter as tk


class HomePage(tk.Frame):
    """Main menu with the three top-level actions."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        tk.Label(self, text="Music Player", font=("TkDefaultFont", 16, "bold")).pack(pady=(25, 15))

        button_width = 24
        tk.Button(self, text="Create / edit playlists", width=button_width,
                  command=lambda: app.show_page("playlists")).pack(pady=4)
        tk.Button(self, text="Play playlist", width=button_width,
                  command=lambda: app.show_page("play")).pack(pady=4)
        tk.Button(self, text="Play single", width=button_width,
                  command=lambda: app.show_page("play_single")).pack(pady=4)
        tk.Button(self, text="Download songs", width=button_width,
                  command=lambda: app.show_page("download")).pack(pady=4)

        self.message = tk.Label(self, text="", fg="gray")
        self.message.pack(pady=10)

    def not_implemented(self, name):
        self.message.config(text=f"{name} is not implemented yet.")

    def on_show(self):
        self.message.config(text="")