import unittest

from solution import TicketSystem


class Level4PublicTests(unittest.TestCase):
    def setUp(self):
        self.ts = TicketSystem()
        self.ts.create_ticket("t1", 5)

    def test_watch_returns_true(self):
        self.assertTrue(self.ts.watch("t1", "alice"))

    def test_watch_unknown_ticket_false(self):
        self.assertFalse(self.ts.watch("ghost", "alice"))

    def test_watch_duplicate_false(self):
        self.ts.watch("t1", "alice")
        self.assertFalse(self.ts.watch("t1", "alice"))

    def test_watcher_gets_notification(self):
        self.ts.watch("t1", "alice")
        self.ts.assign("t1", "bob")
        self.assertEqual(self.ts.notifications("alice"), ["t1:in_progress"])

    def test_notifications_chronological(self):
        self.ts.watch("t1", "alice")
        self.ts.assign("t1", "bob")
        self.ts.resolve("t1")
        self.ts.close("t1")
        self.assertEqual(
            self.ts.notifications("alice"),
            ["t1:in_progress", "t1:resolved", "t1:closed"],
        )

    def test_multiple_watchers(self):
        self.ts.watch("t1", "alice")
        self.ts.watch("t1", "carol")
        self.ts.assign("t1", "bob")
        self.assertEqual(self.ts.notifications("alice"), ["t1:in_progress"])
        self.assertEqual(self.ts.notifications("carol"), ["t1:in_progress"])

    def test_rejected_transition_no_notification(self):
        self.ts.watch("t1", "alice")
        self.assertFalse(self.ts.resolve("t1"))  # open -> resolved is invalid
        self.assertEqual(self.ts.notifications("alice"), [])

    def test_unwatch_stops_future_notifications(self):
        self.ts.watch("t1", "alice")
        self.ts.assign("t1", "bob")
        self.assertTrue(self.ts.unwatch("t1", "alice"))
        self.ts.resolve("t1")
        self.assertEqual(self.ts.notifications("alice"), ["t1:in_progress"])

    def test_notifications_empty(self):
        self.assertEqual(self.ts.notifications("nobody"), [])


if __name__ == "__main__":
    unittest.main()
