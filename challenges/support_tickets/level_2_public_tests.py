import unittest

from solution import TicketSystem


class Level2PublicTests(unittest.TestCase):
    def setUp(self):
        self.ts = TicketSystem()
        self.ts.create_ticket("t1", 5)

    def test_happy_path(self):
        self.assertTrue(self.ts.assign("t1", "alice"))
        self.assertEqual(self.ts.get_status("t1"), "in_progress")
        self.assertTrue(self.ts.resolve("t1"))
        self.assertEqual(self.ts.get_status("t1"), "resolved")
        self.assertTrue(self.ts.close("t1"))
        self.assertEqual(self.ts.get_status("t1"), "closed")

    def test_assign_records_assignee(self):
        self.ts.assign("t1", "alice")
        self.assertEqual(self.ts.get_assignee("t1"), "alice")

    def test_resolve_on_open_rejected(self):
        self.assertFalse(self.ts.resolve("t1"))
        self.assertEqual(self.ts.get_status("t1"), "open")

    def test_assign_twice_rejected(self):
        self.ts.assign("t1", "alice")
        self.assertFalse(self.ts.assign("t1", "bob"))
        self.assertEqual(self.ts.get_assignee("t1"), "alice")

    def test_reopen_clears_assignee(self):
        self.ts.assign("t1", "alice")
        self.ts.resolve("t1")
        self.assertTrue(self.ts.reopen("t1"))
        self.assertEqual(self.ts.get_status("t1"), "open")
        self.assertIsNone(self.ts.get_assignee("t1"))

    def test_unknown_ticket_transitions_false(self):
        self.assertFalse(self.ts.assign("ghost", "a"))
        self.assertFalse(self.ts.resolve("ghost"))
        self.assertFalse(self.ts.close("ghost"))
        self.assertFalse(self.ts.reopen("ghost"))

    def test_next_ticket_skips_assigned(self):
        self.ts.create_ticket("t2", 3)
        self.ts.assign("t1", "alice")  # t1 (prio 5) leaves the open pool
        self.assertEqual(self.ts.next_ticket(), "t2")

    def test_reopened_ticket_eligible_again(self):
        self.ts.assign("t1", "alice")
        self.ts.resolve("t1")
        self.ts.reopen("t1")
        self.assertEqual(self.ts.next_ticket(), "t1")


if __name__ == "__main__":
    unittest.main()
