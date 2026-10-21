from data_structures.singly_linked_list import SinglyLinkedList


class LinkedQueue:
    """A first-in, first-out queue stored in a singly linked list.

    enqueue adds at the back, dequeue takes from the front.
    (Not called queue.py so it can't clash with Python's built-in queue module.)
    """

    def __init__(self):
        self._items = SinglyLinkedList()

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def is_empty(self):
        return self._items.is_empty()

    def enqueue(self, item):
        self._items.append(item)

    def dequeue(self):
        """Remove and return the item at the front."""
        return self._items.pop_front()

    def peek(self):
        """Look at the front item without removing it."""
        return self._items.peek_front()

    def remove_at(self, position):
        """Remove an item from anywhere in the queue (used by 'remove from queue')."""
        return self._items.remove_at(position)

    def clear(self):
        self._items.clear()

    def to_list(self):
        """The items from front to back, as a normal Python list."""
        return self._items.to_list()