import unittest

from solution import TicketSystem


class Level1HiddenTests(unittest.TestCase):
    def test_priority_zero_is_valid(self):
        ts = TicketSystem()
        self.assertTrue(ts.create_ticket("t1", 0))
        self.assertEqual(ts.get_priority("t1"), 0)

    def test_priority_zero_not_confused_with_none(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 0)
        self.assertIsNotNone(ts.get_priority("t1"))

    def test_duplicate_returns_false_repeatedly(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 3)
        self.assertFalse(ts.create_ticket("t1", 4))
        self.assertFalse(ts.create_ticket("t1", 5))
        self.assertEqual(ts.get_priority("t1"), 3)

    def test_next_ticket_strictly_higher_wins_over_earlier(self):
        ts = TicketSystem()
        ts.create_ticket("early", 2)
        ts.create_ticket("late", 8)
        self.assertEqual(ts.next_ticket(), "late")

    def test_next_ticket_earliest_wins_on_tie_regardless_of_id(self):
        ts = TicketSystem()
        ts.create_ticket("z", 7)
        ts.create_ticket("a", 7)
        ts.create_ticket("m", 7)
        self.assertEqual(ts.next_ticket(), "z")

    def test_next_ticket_single(self):
        ts = TicketSystem()
        ts.create_ticket("only", 0)
        self.assertEqual(ts.next_ticket(), "only")

    def test_next_ticket_is_a_peek(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 5)
        ts.create_ticket("t2", 9)
        self.assertEqual(ts.next_ticket(), "t2")
        self.assertEqual(ts.next_ticket(), "t2")
        self.assertEqual(ts.get_status("t2"), "open")

    def test_next_ticket_among_many_priorities(self):
        ts = TicketSystem()
        for i, p in enumerate([3, 1, 4, 1, 5, 9, 2, 6]):
            ts.create_ticket(f"t{i}", p)
        self.assertEqual(ts.next_ticket(), "t5")  # priority 9

    def test_get_status_and_priority_independent_tickets(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 1)
        ts.create_ticket("t2", 2)
        self.assertEqual(ts.get_priority("t1"), 1)
        self.assertEqual(ts.get_priority("t2"), 2)
        self.assertEqual(ts.get_status("t1"), "open")
        self.assertEqual(ts.get_status("t2"), "open")

    def test_large_priority_values(self):
        ts = TicketSystem()
        ts.create_ticket("small", 1)
        ts.create_ticket("huge", 10**9)
        self.assertEqual(ts.next_ticket(), "huge")


if __name__ == "__main__":
    unittest.main()
