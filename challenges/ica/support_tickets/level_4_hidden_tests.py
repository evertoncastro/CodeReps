import unittest

from solution import TicketSystem


class Level4HiddenTests(unittest.TestCase):
    def test_full_cycle_notifications(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 5)
        ts.watch("t1", "alice")
        ts.assign("t1", "a")
        ts.resolve("t1")
        ts.close("t1")
        ts.reopen("t1")
        self.assertEqual(
            ts.notifications("alice"),
            ["t1:in_progress", "t1:resolved", "t1:closed", "t1:open"],
        )

    def test_reopen_notifies_even_though_it_clears_assignee(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 5)
        ts.assign("t1", "a")
        ts.resolve("t1")
        ts.watch("t1", "alice")
        ts.reopen("t1")
        self.assertEqual(ts.notifications("alice"), ["t1:open"])
        self.assertIsNone(ts.get_assignee("t1"))

    def test_watch_late_does_not_backfill(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 5)
        ts.assign("t1", "a")            # before anyone watches
        ts.watch("t1", "alice")
        ts.resolve("t1")
        self.assertEqual(ts.notifications("alice"), ["t1:resolved"])

    def test_unwatch_keeps_past_notifications(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 5)
        ts.watch("t1", "alice")
        ts.assign("t1", "a")
        ts.unwatch("t1", "alice")
        ts.resolve("t1")
        self.assertEqual(ts.notifications("alice"), ["t1:in_progress"])

    def test_agent_watching_multiple_tickets_interleaved(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 5)
        ts.create_ticket("t2", 5)
        ts.watch("t1", "alice")
        ts.watch("t2", "alice")
        ts.assign("t1", "a")   # t1:in_progress
        ts.assign("t2", "b")   # t2:in_progress
        ts.resolve("t1")       # t1:resolved
        self.assertEqual(
            ts.notifications("alice"),
            ["t1:in_progress", "t2:in_progress", "t1:resolved"],
        )

    def test_only_watchers_notified(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 5)
        ts.watch("t1", "alice")
        ts.assign("t1", "bob")   # bob is the assignee but not a watcher
        self.assertEqual(ts.notifications("alice"), ["t1:in_progress"])
        self.assertEqual(ts.notifications("bob"), [])

    def test_watch_after_unwatch_can_resubscribe(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 5)
        ts.watch("t1", "alice")
        self.assertFalse(ts.watch("t1", "alice"))  # duplicate
        ts.unwatch("t1", "alice")
        self.assertTrue(ts.watch("t1", "alice"))    # can subscribe again

    def test_unwatch_unknown_ticket_false(self):
        ts = TicketSystem()
        self.assertFalse(ts.unwatch("ghost", "alice"))

    def test_unwatch_non_subscriber_false(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 5)
        self.assertFalse(ts.unwatch("t1", "alice"))

    def test_watch_and_unwatch_do_not_notify(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 5)
        ts.watch("t1", "alice")
        ts.unwatch("t1", "alice")
        self.assertEqual(ts.notifications("alice"), [])

    def test_notifications_isolated_per_agent(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 5)
        ts.create_ticket("t2", 5)
        ts.watch("t1", "alice")
        ts.watch("t2", "carol")
        ts.assign("t1", "x")
        ts.assign("t2", "y")
        self.assertEqual(ts.notifications("alice"), ["t1:in_progress"])
        self.assertEqual(ts.notifications("carol"), ["t2:in_progress"])

    def test_performance_notification_fanout(self):
        # Many watchers on one ticket: a transition fans out to all of them.
        # Delivery should be linear in the number of watchers, and unrelated
        # transitions on unwatched tickets should not touch them.
        ts = TicketSystem()
        n = 40000
        ts.create_ticket("hot", 5)
        for i in range(n):
            self.assertTrue(ts.watch("hot", f"agent{i:06d}"))
        ts.assign("hot", "worker")
        ts.resolve("hot")
        self.assertEqual(
            ts.notifications("agent000000"), ["hot:in_progress", "hot:resolved"]
        )
        self.assertEqual(
            ts.notifications(f"agent{n - 1:06d}"), ["hot:in_progress", "hot:resolved"]
        )


if __name__ == "__main__":
    unittest.main()
