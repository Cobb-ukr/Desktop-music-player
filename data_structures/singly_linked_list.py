class Node:
    """One element of the list: the data plus a link to the next node."""

    def __init__(self, data):
        self.data = data
        self.next = None


class SinglyLinkedList:
    """A singly linked list that keeps pointers to both its first and last node,
    so adding at the end and removing from the front are both O(1)."""

    def __init__(self):
        self.head = None
        self.tail = None
        self._size = 0

    def __len__(self):
        return self._size

    def is_empty(self):
        return self._size == 0

    def __iter__(self):
        node = self.head
        while node is not None:
            yield node.data
            node = node.next

    def to_list(self):
        return list(self)

    def append(self, data):
        """Add to the end."""
        node = Node(data)
        if self.tail is None:
            self.head = self.tail = node
        else:
            self.tail.next = node
            self.tail = node
        self._size += 1

    def peek_front(self):
        """Return the first item without removing it."""
        if self.head is None:
            raise IndexError("the list is empty")
        return self.head.data

    def pop_front(self):
        """Remove and return the first item."""
        if self.head is None:
            raise IndexError("the list is empty")
        node = self.head
        self.head = node.next
        if self.head is None:
            self.tail = None
        self._size -= 1
        return node.data

    def remove_at(self, position):
        """Remove and return the item at `position` (0-based)."""
        if position < 0 or position >= self._size:
            raise IndexError(f"Position {position} out of range (0 to {self._size - 1})")
        if position == 0:
            return self.pop_front()
        before = self.head
        for _ in range(position - 1):
            before = before.next
        node = before.next
        before.next = node.next
        if node is self.tail:
            self.tail = before
        self._size -= 1
        return node.data

    def clear(self):
        self.head = None
        self.tail = None
        self._size = 0