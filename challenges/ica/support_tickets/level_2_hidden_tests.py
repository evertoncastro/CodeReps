import unittest

from solution import TicketSystem


def _t(priority=5, tid="t1"):
    ts = TicketSystem()
    ts.create_ticket(tid, priority)
    return ts


class Level2HiddenTests(unittest.TestCase):
    def test_close_on_open_rejected(self):
        ts = _t()
        self.assertFalse(ts.close("t1"))
        self.assertEqual(ts.get_status("t1"), "open")

    def test_close_on_in_progress_rejected(self):
        ts = _t()
        ts.assign("t1", "a")
        self.assertFalse(ts.close("t1"))
        self.assertEqual(ts.get_status("t1"), "in_progress")

    def test_assign_on_in_progress_rejected(self):
        ts = _t()
        ts.assign("t1", "a")
        self.assertFalse(ts.assign("t1", "b"))
        self.assertEqual(ts.get_status("t1"), "in_progress")

    def test_assign_on_resolved_rejected(self):
        ts = _t()
        ts.assign("t1", "a")
        ts.resolve("t1")
        self.assertFalse(ts.assign("t1", "b"))
        self.assertEqual(ts.get_status("t1"), "resolved")

    def test_assign_on_closed_rejected(self):
        ts = _t()
        ts.assign("t1", "a")
        ts.resolve("t1")
        ts.close("t1")
        self.assertFalse(ts.assign("t1", "b"))
        self.assertEqual(ts.get_status("t1"), "closed")

    def test_resolve_on_resolved_rejected(self):
        ts = _t()
        ts.assign("t1", "a")
        ts.resolve("t1")
        self.assertFalse(ts.resolve("t1"))

    def test_reopen_on_open_rejected(self):
        ts = _t()
        self.assertFalse(ts.reopen("t1"))
        self.assertEqual(ts.get_status("t1"), "open")

    def test_reopen_on_in_progress_rejected(self):
        ts = _t()
        ts.assign("t1", "a")
        self.assertFalse(ts.reopen("t1"))
        self.assertEqual(ts.get_status("t1"), "in_progress")

    def test_reopen_from_resolved(self):
        ts = _t()
        ts.assign("t1", "a")
        ts.resolve("t1")
        self.assertTrue(ts.reopen("t1"))
        self.assertEqual(ts.get_status("t1"), "open")

    def test_reopen_from_closed(self):
        ts = _t()
        ts.assign("t1", "a")
        ts.resolve("t1")
        ts.close("t1")
        self.assertTrue(ts.reopen("t1"))
        self.assertEqual(ts.get_status("t1"), "open")

    def test_reassign_after_reopen_to_new_agent(self):
        ts = _t()
        ts.assign("t1", "alice")
        ts.resolve("t1")
        ts.reopen("t1")
        self.assertTrue(ts.assign("t1", "bob"))
        self.assertEqual(ts.get_assignee("t1"), "bob")

    def test_get_assignee_open_is_none(self):
        ts = _t()
        self.assertIsNone(ts.get_assignee("t1"))

    def test_get_assignee_unknown_is_none(self):
        ts = _t()
        self.assertIsNone(ts.get_assignee("ghost"))

    def test_full_cycle_twice(self):
        ts = _t()
        for _ in range(2):
            self.assertTrue(ts.assign("t1", "a"))
            self.assertTrue(ts.resolve("t1"))
            self.assertTrue(ts.close("t1"))
            self.assertTrue(ts.reopen("t1"))
        self.assertEqual(ts.get_status("t1"), "open")

    def test_next_ticket_ignores_all_non_open(self):
        ts = TicketSystem()
        ts.create_ticket("hi", 10)
        ts.create_ticket("lo", 1)
        ts.assign("hi", "a")  # highest priority now in_progress
        self.assertEqual(ts.next_ticket(), "lo")
        ts.assign("lo", "b")
        self.assertIsNone(ts.next_ticket())


if __name__ == "__main__":
    unittest.main()
