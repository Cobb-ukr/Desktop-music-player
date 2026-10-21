import os

import yt_dlp

from config import SONGS_DIR, AUDIO_FORMAT, AUDIO_QUALITY


def download_audio(url, on_progress=None, on_converting=None, folder=SONGS_DIR):
    """Download audio from a link and convert it to mp3 (needs ffmpeg).

    on_progress(percent): called during the download. percent is a number
        from 0 to 100, or None if the total size isn't known.
    on_converting(): called once when the mp3 conversion starts.
    """
    os.makedirs(folder, exist_ok=True)

    def progress_hook(d):
        if on_progress is None:
            return
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            if total:
                on_progress(d.get("downloaded_bytes", 0) / total * 100)
            else:
                on_progress(None)
        elif d["status"] == "finished":
            on_progress(100)

    def postprocessor_hook(d):
        if (on_converting is not None
                and d["status"] == "started"
                and d["postprocessor"] == "ExtractAudio"):
            on_converting()

    options = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(folder, "%(title)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "progress_hooks": [progress_hook],
        "postprocessor_hooks": [postprocessor_hook],
        "postprocessors": [
            {
                # Convert to mp3 so every song has the same, easily playable format
                "key": "FFmpegExtractAudio",
                "preferredcodec": AUDIO_FORMAT,
                "preferredquality": AUDIO_QUALITY,
            },
            {
                # Embed title/artist info in the mp3 as ID3 tags
                "key": "FFmpegMetadata",
                "add_metadata": True,
            },
        ],
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([url])