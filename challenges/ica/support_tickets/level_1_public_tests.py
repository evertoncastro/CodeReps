import unittest

from solution import TicketSystem


class Level1PublicTests(unittest.TestCase):
    def test_create_ticket_returns_true(self):
        ts = TicketSystem()
        self.assertTrue(ts.create_ticket("t1", 5))

    def test_create_duplicate_returns_false(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 5)
        self.assertFalse(ts.create_ticket("t1", 9))

    def test_duplicate_does_not_change_priority(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 5)
        ts.create_ticket("t1", 9)
        self.assertEqual(ts.get_priority("t1"), 5)

    def test_new_ticket_is_open(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 5)
        self.assertEqual(ts.get_status("t1"), "open")

    def test_get_status_unknown_is_none(self):
        ts = TicketSystem()
        self.assertIsNone(ts.get_status("nope"))

    def test_get_priority_unknown_is_none(self):
        ts = TicketSystem()
        self.assertIsNone(ts.get_priority("nope"))

    def test_next_ticket_highest_priority(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 1)
        ts.create_ticket("t2", 9)
        ts.create_ticket("t3", 5)
        self.assertEqual(ts.next_ticket(), "t2")

    def test_next_ticket_tie_broken_by_creation_order(self):
        ts = TicketSystem()
        ts.create_ticket("b", 5)
        ts.create_ticket("a", 5)
        self.assertEqual(ts.next_ticket(), "b")

    def test_next_ticket_empty_is_none(self):
        self.assertIsNone(TicketSystem().next_ticket())


if __name__ == "__main__":
    unittest.main()
