import tkinter as tk

from player import AudioPlayer
from playlist_manager import PlaylistManager
from gui.home_page import HomePage
from gui.download_page import DownloadPage
from gui.playlists_page import PlaylistsPage
from gui.playlist_editor_page import PlaylistEditorPage
from gui.play_page import PlayPage
from gui.play_single_page import PlaySinglePage

# Window size for each page
WINDOW_SIZES = {
    "home": "440x340",
    "download": "440x300",
    "playlists": "460x380",
    "editor": "780x520",
    "play": "860x660",
    "play_single": "480x620",
}


class App:
    def __init__(self, root, manager=None):
        self.root = root
        # One shared manager, so every page sees the same playlists
        self.manager = manager or PlaylistManager()
        # One shared audio player, since there is only one audio output
        self.player = AudioPlayer()
        # The page currently on screen (pages use this to ignore timer ticks while hidden)
        self.current_page = None
        root.title("Music Player")
        root.protocol("WM_DELETE_WINDOW", self.close)

        container = tk.Frame(root)
        container.pack(fill="both", expand=True)

        # To add a new page: create its class in gui/, import it above,
        # and register it here under a name.
        self.pages = {
            "home": HomePage(container, self),
            "download": DownloadPage(container, self),
            "playlists": PlaylistsPage(container, self),
            "editor": PlaylistEditorPage(container, self),
            "play": PlayPage(container, self),
            "play_single": PlaySinglePage(container, self),
        }
        # All pages sit on top of each other; show_page raises the one we want
        for page in self.pages.values():
            page.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.show_page("home")

    def show_page(self, name, **kwargs):
        """Show a page. Extra keyword arguments are passed on to its on_show()."""
        page = self.pages[name]
        size = WINDOW_SIZES.get(name)
        if size:
            self.root.geometry(size)
        self.current_page = page
        page.tkraise()
        page.on_show(**kwargs)

    def close(self):
        # Let pages clean up, then shut down the audio system once
        for page in self.pages.values():
            on_close = getattr(page, "on_close", None)
            if on_close:
                on_close()
        self.player.shutdown()
        self.root.destroy()