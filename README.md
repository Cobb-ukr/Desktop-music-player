# Music Player

A desktop music player that can download audio from a URL, keep a local library of MP3 files, organize songs into playlists, and play them back through a GUI.

## Overview

This project combines a few core ideas:

- download audio from a web source using `yt-dlp` (checkout https://github.com/yt-dlp/yt-dlp )
- save downloaded tracks in a local `songs/` directory
- convert tracks to MP3 format for consistent playback
- manage playlists in a JSON-backed playlist store
- play songs through `pygame` while tracking play state and queue behavior
- expose the app through a Tkinter-based GUI

The app is split into a few layers:

- configuration and file paths
- download and library management
- playlist persistence and track ordering
- playback logic
- user interface

## Features

- Download audio from a URL
- Convert downloaded audio to MP3
- Store downloaded songs in a `songs/` folder
- View available songs in the local library
- Create, rename, delete, and reorder playlists
- Add songs to playlists and remove them later
- Play songs in order or from a queue
- Skip/rewind/seek within songs
- Track playback position and volume
- Save playlist state between runs using `playlists.json`

## Requirements

Python dependencies are listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

Current dependencies:

- `yt-dlp` — downloads audio
- `pygame` — audio playback engine
- `pytest` — test runner for project tests

### System requirement: FFmpeg

The project also depends on FFmpeg being installed on the machine, because the downloader converts media files to MP3 using `FFmpegExtractAudio` and uses `ffprobe` to read audio duration.

On Linux, install it with something like:

```bash
sudo apt install ffmpeg
```

or on Arch:

```bash
sudo pacman -S ffmpeg
```

## Project structure

```text
Music_player/
├── config.py
├── downloader.py
├── library.py
├── main.py
├── player.py
├── play_session.py
├── playlist_manager.py
├── playlists.json
├── requirements.txt
├── README.md
├── .gitignore
├── data_structures/
│   ├── circular_doubly_linked_list.py
│   ├── linked_queue.py
│   ├── singly_linked_list.py
│   └── __init__.py
├── gui/
│   ├── app.py
│   ├── download_page.py
│   ├── home_page.py
│   ├── play_page.py
│   ├── play_single_page.py
│   ├── playlist_editor_page.py
│   ├── playlists_page.py
│   ├── seek_bar.py
│   └── __init__.py
├── songs/
└── tests (various pytest files)
```

## Core files and their role

### `config.py`

Defines the app’s global paths and settings.

- `BASE_DIR` = project root
- `SONGS_DIR` = where downloaded music is stored
- `AUDIO_FORMAT = "mp3"`
- `AUDIO_QUALITY = "192"`
- `PLAYLISTS_FILE` = location of the playlist JSON file

This file acts as the configuration source for the rest of the project.

### `downloader.py`

Handles fetching a song from a URL and saving it locally.

Responsibilities:

- creates the `songs/` folder if needed
- downloads audio via `yt_dlp`
- tracks download progress using a callback hook
- converts songs to MP3 with FFmpeg
- adds metadata to the final file

The `download_audio()` function is the main entry point.

### `library.py`

Provides helpers for working with the downloaded audio folder.

Functions:

- `get_songs()` — returns all `.mp3` files in the library
- `song_path(filename)` — resolves a full file path for a song
- `display_name(filename)` — strips the file extension for UI display

This is the layer used to discover what music is available to play.

### `player.py`

This is the actual playback engine.

It uses `pygame.mixer` to:

- load a song
- start playback
- pause and resume
- stop playback
- seek to a time position
- read volume and playback progress

It also includes:

- `get_duration(path)` using `ffprobe` when available
- `PlayerError` for playback failures
- state tracking so playback can distinguish between “stopped” and “paused”

This file is the core audio player used by the UI.

### `play_session.py`

Manages the session logic for a playlist.

This class decides what should play next based on both:

- the current playlist order
- a queue of songs selected to play next

It keeps track of:

- the current playing track
- whether the track came from the playlist or the queue
- the current playlist pointer

The class does not play sound itself; it just decides which song is next.

### `playlist_manager.py`

Responsible for creating and saving playlists.

Features:

- create new playlists
- rename or delete playlists
- list all playlist names
- add/remove songs inside a playlist
- move song positions around
- persist playlists to `playlists.json`
- restore playlists when the program starts

It validates that a song actually exists in the `songs/` folder before adding it to a playlist.

### `main.py`

Main entry point for the application.

This file creates the Tkinter root window and starts the GUI application:

```python
root = tk.Tk()
App(root)
root.mainloop()
```

### `data_structures/singly_linked_list.py`

A custom singly linked list implementation.

Used to support:

- queue behavior
- insertion/removal operations
- iteration and front-end access

### `data_structures/linked_queue.py`

A FIFO queue built on top of the singly linked list.

This is used by the play session to allow songs to be queued for immediate playback.

### `data_structures/circular_doubly_linked_list.py`

This is the main playlist data structure.

It is a circular doubly linked list, which means:

- each node knows the previous and next element
- the list wraps around at the end
- the current song pointer can move forward and backward endlessly in a loop

This is ideal for playlist playback because songs can continue in a cycle without requiring special boundary handling.

## How the application works

The general flow is:

1. The app starts in `main.py`.
2. The GUI loads the library and playlist data.
3. The user can download songs with `downloader.py`.
4. Downloaded songs are stored in `songs/`.
5. Playlist manager stores playlist order in `playlists.json`.
6. `PlaySession` chooses the next song based on playlist order and queue state.
7. `AudioPlayer` loads and plays the chosen MP3 file.
8. Playback state is updated while the GUI shows progress, volume, and controls.

## Notes

- The `gui/` folder contains the graphical interface and hooks into the logic above.
- The `test_*.py` files validate the core behavior of the linked-list, queue, playlist manager, and playback logic.
- The project is structured so the UI does not directly manipulate playlist internals; instead, it uses the manager and session layers.

## Getting started

1. Clone the project.
2. Create a virtual environment if desired.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Install FFmpeg on your system.
5. Run the application:

```bash
python main.py
```

## Summary

This project is a lightweight music player with:

- download support
- local music library management
- playlist persistence
- circular playback logic
- audio playback engine
- Tkinter-based user interface

It is a good example of a small desktop app built from modular components, with logic separated from the UI and data structures deliberately implemented by hand rather than relying on external libraries.
