from data_structures.linked_queue import LinkedQueue


class PlaySession:
    """Decides what plays next while a playlist is being played.

    - The playlist (a circular doubly linked list) provides the looping order.
    - The queue holds songs the user lined up with "Play next". They jump ahead:
      when a song ends, queued songs play first, and only when the queue is
      empty does playback go back to the playlist.

    While a queued song plays, the playlist pointer stays where it was, so once
    the queue is empty playback carries on with the song after that one.

    This class only decides *which* song; it never plays any audio.
    """

    def __init__(self, playlist):
        self.playlist = playlist
        self.queue = LinkedQueue()
        self.now_playing = None   # filename of the current song
        self.from_queue = False   # True if the current song came from the queue

    def start(self):
        """Begin at the first song of the playlist and return it."""
        self.playlist.reset()
        self.from_queue = False
        self.now_playing = self.playlist.current()
        return self.now_playing

    def next(self):
        """Move to the next song: the queue first, otherwise the next playlist song."""
        if not self.queue.is_empty():
            self.now_playing = self.queue.dequeue()
            self.from_queue = True
        else:
            self.now_playing = self.playlist.next()
            self.from_queue = False
        return self.now_playing

    def prev(self):
        """Move to the previous song.

        From a playlist song, that's the one before it in the playlist.
        From a queued song, it goes back to the playlist song we were on.
        """
        if self.from_queue:
            self.from_queue = False
            self.now_playing = self.playlist.current()
        else:
            self.now_playing = self.playlist.prev()
        return self.now_playing

    def jump_to(self, position):
        """Play the playlist song at `position` (0-based) right now."""
        self.playlist.set_current_at(position)
        self.from_queue = False
        self.now_playing = self.playlist.current()
        return self.now_playing

    def playing_index(self):
        """Playlist position of the song playing now (None if it's a queued song)."""
        if self.from_queue:
            return None
        return self.playlist.current_index()

    # ---------- queue ----------

    def queue_song(self, filename):
        self.queue.enqueue(filename)

    def remove_from_queue(self, position):
        return self.queue.remove_at(position)

    def clear_queue(self):
        self.queue.clear()