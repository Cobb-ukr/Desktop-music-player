"""Quick checks for the circular doubly linked list.
Run from the project folder with:  python test_linked_list.py
"""
from data_structures.circular_doubly_linked_list import CircularDoublyLinkedList


def build(*items):
    playlist = CircularDoublyLinkedList()
    for item in items:
        playlist.append(item)
    return playlist


def expect_index_error(action):
    try:
        action()
    except IndexError:
        return
    raise AssertionError("expected an IndexError")


def test_empty_list():
    p = CircularDoublyLinkedList()
    assert len(p) == 0 and p.is_empty()
    assert p.to_list() == []
    assert p.current() is None and p.next() is None and p.prev() is None
    expect_index_error(lambda: p.remove_at(0))


def test_insert_front_middle_end():
    p = build("B", "D")
    p.insert_at(0, "A")           # front
    p.insert_at(2, "C")           # middle
    p.insert_at(len(p), "E")      # end
    assert p.to_list() == ["A", "B", "C", "D", "E"]
    assert len(p) == 5


def test_insert_out_of_range():
    p = build("A", "B")
    expect_index_error(lambda: p.insert_at(3, "X"))
    expect_index_error(lambda: p.insert_at(-1, "X"))


def test_remove_front_middle_end():
    p = build("A", "B", "C", "D", "E")
    assert p.remove_at(0) == "A"
    assert p.remove_at(1) == "C"        # list is now B, C, D, E
    assert p.remove_at(len(p) - 1) == "E"
    assert p.to_list() == ["B", "D"]
    expect_index_error(lambda: p.remove_at(2))


def test_remove_last_remaining_item():
    p = build("A")
    assert p.remove_at(0) == "A"
    assert p.is_empty() and p.current() is None
    p.append("B")                        # list still works afterwards
    assert p.to_list() == ["B"] and p.current() == "B"


def test_next_wraps_around():
    p = build("A", "B", "C")
    assert p.current() == "A"
    assert [p.next(), p.next(), p.next(), p.next()] == ["B", "C", "A", "B"]


def test_prev_wraps_around():
    p = build("A", "B", "C")
    assert [p.prev(), p.prev(), p.prev()] == ["C", "B", "A"]


def test_single_item_loops_to_itself():
    p = build("A")
    assert p.next() == "A" and p.prev() == "A"


def test_removing_current_moves_pointer_forward():
    p = build("A", "B", "C")
    p.next()                             # current is B
    p.remove_at(1)                       # remove B
    assert p.current() == "C"


def test_links_are_consistent_after_many_operations():
    p = build("A", "B", "C", "D", "E", "F")
    p.insert_at(3, "X")
    p.remove_at(0)
    p.remove_at(len(p) - 1)
    p.insert_at(0, "Y")
    expected = p.to_list()
    # Walk forward and backward around the whole loop and compare
    forward, node = [], p.head
    for _ in range(len(p)):
        forward.append(node.data)
        node = node.next
    assert node is p.head                # circular: back where we started
    backward, node = [], p.head.prev
    for _ in range(len(p)):
        backward.append(node.data)
        node = node.prev
    assert forward == expected
    assert backward == expected[::-1]


def test_reset():
    p = build("A", "B", "C")
    p.next(); p.next()
    p.reset()
    assert p.current() == "A"


def test_set_current_at_and_current_index():
    p = build("A", "B", "C", "D")
    assert p.current_index() == 0
    p.set_current_at(2)
    assert p.current() == "C" and p.current_index() == 2
    assert p.next() == "D" and p.current_index() == 3
    assert p.next() == "A" and p.current_index() == 0     # wraps around
    expect_index_error(lambda: p.set_current_at(4))
    expect_index_error(lambda: p.set_current_at(-1))


def test_current_index_when_empty():
    assert CircularDoublyLinkedList().current_index() is None


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print(f"PASS  {test.__name__}")
    print(f"\nAll {len(tests)} tests passed.")