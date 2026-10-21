class Node:
    """One element of the list. Holds the data plus links to both neighbours."""

    def __init__(self, data):
        self.data = data
        self.next = None
        self.prev = None


class CircularDoublyLinkedList:
    """A circular doubly linked list.

    - Doubly linked: every node knows its next and previous node.
    - Circular: the last node links back to the first, and the first links
      back to the last, so there is no "end" of the list.

    Positions are 0-based. A "current" pointer marks the node being played,
    and next()/prev() move it around the loop forever.
    """

    def __init__(self):
        self.head = None      # first node (position 0)
        self._current = None  # node currently "playing"
        self._size = 0

    # ---------- basic info ----------

    def __len__(self):
        return self._size

    def is_empty(self):
        return self._size == 0

    def __iter__(self):
        """Yield each item once, from position 0 to the last position."""
        node = self.head
        for _ in range(self._size):
            yield node.data
            node = node.next

    def to_list(self):
        """Return the items as a normal Python list (handy for the GUI)."""
        return list(self)

    # ---------- finding a node ----------

    def _node_at(self, position):
        """Walk to the node at `position`, starting from whichever end is closer."""
        if position < self._size // 2:
            node = self.head
            for _ in range(position):
                node = node.next
        else:
            node = self.head.prev  # the last node, thanks to the circular link
            for _ in range(self._size - 1 - position):
                node = node.prev
        return node

    # ---------- insertion ----------

    def insert_at(self, position, data):
        """Insert `data` so that it ends up at `position`.

        position 0 inserts at the front; position len(list) appends at the end.
        """
        if position < 0 or position > self._size:
            raise IndexError(f"Position {position} out of range (0 to {self._size})")

        new_node = Node(data)

        if self.head is None:
            # First node: it points to itself in both directions
            new_node.next = new_node
            new_node.prev = new_node
            self.head = new_node
            self._current = new_node
        else:
            # Insert the new node just before `target`.
            # Appending at the end means inserting before the head (it's circular).
            target = self.head if position == self._size else self._node_at(position)
            before = target.prev

            before.next = new_node
            new_node.prev = before
            new_node.next = target
            target.prev = new_node

            if position == 0:
                self.head = new_node

        self._size += 1

    def append(self, data):
        """Add to the end of the list."""
        self.insert_at(self._size, data)

    # ---------- removal ----------

    def remove_at(self, position):
        """Remove and return the item at `position`."""
        if position < 0 or position >= self._size:
            raise IndexError(f"Position {position} out of range (0 to {self._size - 1})")

        node = self._node_at(position)

        if self._size == 1:
            self.head = None
            self._current = None
        else:
            node.prev.next = node.next
            node.next.prev = node.prev
            if node is self.head:
                self.head = node.next
            if node is self._current:
                self._current = node.next  # keep playback going on the next song

        self._size -= 1
        return node.data

    # ---------- playback pointer ----------

    def current(self):
        """The item the pointer is on (None if the list is empty)."""
        return self._current.data if self._current else None

    def next(self):
        """Move forward one item, wrapping from the last to the first. Return it."""
        if self._current is None:
            return None
        self._current = self._current.next
        return self._current.data

    def prev(self):
        """Move back one item, wrapping from the first to the last. Return it."""
        if self._current is None:
            return None
        self._current = self._current.prev
        return self._current.data

    def reset(self):
        """Put the pointer back on the first item."""
        self._current = self.head

    def set_current_at(self, position):
        """Move the pointer to the item at `position` (used to jump to a chosen song)."""
        if position < 0 or position >= self._size:
            raise IndexError(f"Position {position} out of range (0 to {self._size - 1})")
        self._current = self._node_at(position)

    def current_index(self):
        """The position of the item the pointer is on (None if the list is empty)."""
        if self._current is None:
            return None
        node = self.head
        for index in range(self._size):
            if node is self._current:
                return index
            node = node.next