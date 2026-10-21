import tkinter as tk
from tkinter import ttk


def format_time(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"


class SeekBar(tk.Frame):
    """Elapsed time | slider | total time.

    The page calls set_duration() when a song starts and update_position()
    regularly. When the user clicks or drags the bar, on_seek(seconds) is
    called once they let go.
    """

    SLIDER_MARGIN = 7  # rough half-width of the slider handle, in pixels

    def __init__(self, parent, on_seek):
        super().__init__(parent)
        self.on_seek = on_seek
        self.duration = None
        self.dragging = False

        self.time_label = tk.Label(self, text="0:00", width=5, font=("TkFixedFont", 11))
        self.time_label.pack(side="left")
        self.total_label = tk.Label(self, text="0:00", width=5, font=("TkFixedFont", 11))
        self.total_label.pack(side="right")
        self.scale = ttk.Scale(self, from_=0, to=1, orient="horizontal")
        self.scale.pack(side="left", fill="x", expand=True, padx=6)

        # We handle the mouse ourselves so a click jumps straight to that spot,
        # and dragging doesn't fight with the timer that moves the bar.
        self.scale.bind("<ButtonPress-1>", self._on_press)
        self.scale.bind("<B1-Motion>", self._on_drag)
        self.scale.bind("<ButtonRelease-1>", self._on_release)
        self.reset()

    def reset(self):
        """Back to the empty, disabled state (nothing playing)."""
        self.duration = None
        self.dragging = False
        self.scale.config(to=1)
        self.scale.set(0)
        self.scale.state(["disabled"])
        self.time_label.config(text="0:00")
        self.total_label.config(text="0:00")

    def set_duration(self, duration):
        """A new song started. `duration` is in seconds, or None if unknown."""
        self.dragging = False
        self.duration = duration
        if duration:
            self.scale.config(to=duration)
            self.scale.state(["!disabled"])
            self.total_label.config(text=format_time(duration))
        else:
            self.scale.state(["disabled"])
            self.total_label.config(text="--:--")
        self._display(0)

    def update_position(self, seconds):
        """Move the bar to `seconds` (ignored while the user is dragging it)."""
        if not self.dragging:
            self._display(seconds)

    def _display(self, seconds):
        self.time_label.config(text=format_time(seconds))
        if self.duration:
            self.scale.set(seconds)

    def _on_press(self, event):
        if self.duration:
            self.dragging = True
            self._drag_to(event)
        return "break"  # skip tkinter's default behaviour (small steps per click)

    def _on_drag(self, event):
        if self.dragging:
            self._drag_to(event)
        return "break"

    def _on_release(self, event):
        if self.dragging:
            self.dragging = False
            self.on_seek(self.scale.get())
        return "break"

    def _drag_to(self, event):
        usable_width = max(1, self.scale.winfo_width() - 2 * self.SLIDER_MARGIN)
        fraction = min(1.0, max(0.0, (event.x - self.SLIDER_MARGIN) / usable_width))
        self._display(fraction * self.duration)