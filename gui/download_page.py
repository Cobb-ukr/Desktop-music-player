import threading
import tkinter as tk
from tkinter import ttk

from config import SONGS_DIR
from downloader import download_audio


class DownloadPage(tk.Frame):
    """Paste a link, click Download, an mp3 is saved to the songs folder."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        tk.Label(self, text="Download songs", font=("TkDefaultFont", 14, "bold")).pack(pady=(15, 5))
        tk.Label(self, text="Paste a link:").pack()

        self.link_entry = tk.Entry(self, width=50)
        self.link_entry.pack(padx=15, pady=5)
        self.link_entry.bind("<Return>", lambda event: self.start_download())

        self.download_button = tk.Button(self, text="Download", command=self.start_download)
        self.download_button.pack(pady=5)

        self.progress = ttk.Progressbar(self, length=300, mode="determinate", maximum=100)
        self.progress.pack(pady=5)

        self.status_label = tk.Label(self, text="", wraplength=380)
        self.status_label.pack(pady=5)

        tk.Button(self, text="Back", command=lambda: app.show_page("home")).pack(pady=5)

    def on_show(self):
        self.link_entry.focus()

    def start_download(self):
        url = self.link_entry.get().strip()
        if not url:
            self.status_label.config(text="Please paste a link first.")
            return
        self.download_button.config(state="disabled")
        self.status_label.config(text="Starting download...")
        # Until we know the total size, show a bouncing bar
        self.progress.config(mode="indeterminate", value=0)
        self.progress.start(15)
        # Run in a background thread so the window doesn't freeze
        threading.Thread(target=self.run_download, args=(url,), daemon=True).start()

    def run_download(self, url):
        try:
            download_audio(
                url,
                on_progress=self.report_progress,
                on_converting=self.report_converting,
            )
            message = f"Done! Saved to {SONGS_DIR}"
        except Exception as error:
            message = f"Download failed: {error}"
        self.after(0, self.download_finished, message)

    # --- callbacks called from the download thread: hand work to the main thread ---

    def report_progress(self, percent):
        self.after(0, self.update_progress, percent)

    def report_converting(self):
        self.after(0, self.show_converting)

    # --- GUI updates (main thread only) ---

    def update_progress(self, percent):
        if percent is None:
            return  # size unknown, keep the bouncing bar
        if str(self.progress.cget("mode")) == "indeterminate":
            self.progress.stop()
            self.progress.config(mode="determinate")
        self.progress["value"] = percent
        self.status_label.config(text=f"Downloading... {percent:.0f}%")

    def show_converting(self):
        # Conversion has no measurable progress, so show a bouncing bar
        self.progress.config(mode="indeterminate", value=0)
        self.progress.start(15)
        self.status_label.config(text="Converting to mp3...")

    def download_finished(self, message):
        self.progress.stop()
        self.progress.config(mode="determinate")
        # Show a full bar on success, an empty one on failure
        self.progress["value"] = 100 if message.startswith("Done") else 0
        self.status_label.config(text=message)
        self.download_button.config(state="normal")
        self.link_entry.delete(0, tk.END)