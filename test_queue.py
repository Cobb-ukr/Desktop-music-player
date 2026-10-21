"""Checks for the singly linked list and the queue built on it.
Run from the project folder with:  python test_queue.py
"""
from data_structures.singly_linked_list import SinglyLinkedList
from data_structures.linked_queue import LinkedQueue


def expect_index_error(action):
    try:
        action()
    except IndexError:
        return
    raise AssertionError("expected an IndexError")


def filled_list(*items):
    linked = SinglyLinkedList()
    for item in items:
        linked.append(item)
    return linked


def test_list_append_and_order():
    s = filled_list("A", "B", "C")
    assert s.to_list() == ["A", "B", "C"] and len(s) == 3
    assert s.tail.data == "C"


def test_list_pop_front_until_empty():
    s = filled_list("A", "B")
    assert s.pop_front() == "A"
    assert s.pop_front() == "B"
    assert s.is_empty() and s.head is None and s.tail is None
    expect_index_error(s.pop_front)
    s.append("C")                         # still usable afterwards
    assert s.to_list() == ["C"] and s.tail.data == "C"


def test_list_remove_at_positions():
    s = filled_list("A", "B", "C", "D")
    assert s.remove_at(1) == "B"          # middle
    assert s.remove_at(2) == "D"          # last: tail must move back
    assert s.tail.data == "C"
    s.append("E")                         # appending still works after removing the tail
    assert s.to_list() == ["A", "C", "E"]
    assert s.remove_at(0) == "A"          # first
    assert s.to_list() == ["C", "E"]
    expect_index_error(lambda: s.remove_at(2))
    expect_index_error(lambda: s.remove_at(-1))


def test_list_remove_only_item():
    s = filled_list("A")
    assert s.remove_at(0) == "A"
    assert s.is_empty() and s.tail is None


def test_list_peek_and_clear():
    s = filled_list("A", "B")
    assert s.peek_front() == "A" and len(s) == 2
    s.clear()
    assert s.is_empty()
    expect_index_error(s.peek_front)


def test_queue_is_first_in_first_out():
    q = LinkedQueue()
    for item in ("A", "B", "C"):
        q.enqueue(item)
    assert [q.dequeue(), q.dequeue(), q.dequeue()] == ["A", "B", "C"]
    assert q.is_empty()


def test_queue_peek_does_not_remove():
    q = LinkedQueue()
    q.enqueue("A"); q.enqueue("B")
    assert q.peek() == "A" and len(q) == 2


def test_queue_empty_errors():
    q = LinkedQueue()
    expect_index_error(q.dequeue)
    expect_index_error(q.peek)


def test_queue_remove_at_and_clear():
    q = LinkedQueue()
    for item in ("A", "B", "C"):
        q.enqueue(item)
    assert q.remove_at(1) == "B"
    assert q.to_list() == ["A", "C"]
    q.clear()
    assert q.is_empty() and q.to_list() == []


def test_queue_interleaved_use():
    q = LinkedQueue()
    q.enqueue("A"); q.enqueue("B")
    assert q.dequeue() == "A"
    q.enqueue("C")
    assert q.to_list() == ["B", "C"]
    assert list(q) == ["B", "C"]


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print(f"PASS  {test.__name__}")
    print(f"\nAll {len(tests)} tests passed.")