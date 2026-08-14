import unittest

from solution import TicketSystem


class Level3HiddenTests(unittest.TestCase):
    def test_history_ignores_rejected_transitions(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 5)
        self.assertFalse(ts.resolve("t1"))   # rejected
        self.assertFalse(ts.close("t1"))     # rejected
        ts.assign("t1", "a")
        self.assertFalse(ts.close("t1"))     # rejected (in_progress -> closed)
        self.assertEqual(ts.history("t1"), ["open", "in_progress"])

    def test_history_full_cycle(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 5)
        ts.assign("t1", "a")
        ts.resolve("t1")
        ts.close("t1")
        ts.reopen("t1")
        self.assertEqual(
            ts.history("t1"),
            ["open", "in_progress", "resolved", "closed", "open"],
        )

    def test_history_is_independent_per_ticket(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 1)
        ts.create_ticket("t2", 1)
        ts.assign("t1", "a")
        self.assertEqual(ts.history("t1"), ["open", "in_progress"])
        self.assertEqual(ts.history("t2"), ["open"])

    def test_tickets_by_status_unknown_status_empty(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 1)
        self.assertEqual(ts.tickets_by_status("banana"), [])

    def test_tickets_by_status_empty_system(self):
        self.assertEqual(TicketSystem().tickets_by_status("open"), [])

    def test_tickets_by_status_moves_between_buckets(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 1)
        self.assertEqual(ts.tickets_by_status("open"), ["t1"])
        ts.assign("t1", "a")
        self.assertEqual(ts.tickets_by_status("open"), [])
        self.assertEqual(ts.tickets_by_status("in_progress"), ["t1"])
        ts.resolve("t1")
        self.assertEqual(ts.tickets_by_status("in_progress"), [])
        self.assertEqual(ts.tickets_by_status("resolved"), ["t1"])

    def test_agent_workload_zero_for_unknown_agent(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 1)
        ts.assign("t1", "alice")
        self.assertEqual(ts.agent_workload("bob"), 0)

    def test_agent_workload_drops_on_reopen(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 1)
        ts.assign("t1", "alice")
        ts.resolve("t1")
        ts.reopen("t1")
        self.assertEqual(ts.agent_workload("alice"), 0)

    def test_agent_workload_only_counts_in_progress(self):
        ts = TicketSystem()
        for i in range(4):
            ts.create_ticket(f"t{i}", 1)
            ts.assign(f"t{i}", "alice")
        ts.resolve("t0")   # no longer in_progress
        ts.resolve("t1")
        ts.close("t1")     # closed
        self.assertEqual(ts.agent_workload("alice"), 2)  # t2, t3

    def test_busiest_agent_tie_broken_by_id(self):
        ts = TicketSystem()
        ts.create_ticket("x", 1)
        ts.create_ticket("y", 1)
        ts.assign("x", "bob")
        ts.assign("y", "alice")
        self.assertEqual(ts.busiest_agent(), "alice")

    def test_busiest_agent_after_workload_changes(self):
        ts = TicketSystem()
        for i in range(3):
            ts.create_ticket(f"a{i}", 1)
            ts.assign(f"a{i}", "alice")
        ts.create_ticket("b0", 1)
        ts.assign("b0", "bob")
        # alice has 3, bob has 1
        self.assertEqual(ts.busiest_agent(), "alice")
        ts.resolve("a0")
        ts.resolve("a1")
        # now alice has 1, bob has 1 -> tie -> alice by id
        self.assertEqual(ts.busiest_agent(), "alice")
        ts.resolve("a2")
        # now only bob has an in_progress ticket
        self.assertEqual(ts.busiest_agent(), "bob")

    def test_performance_many_tickets_and_transitions(self):
        # id lookups and transitions must be roughly O(1); a list-backed store
        # that scans on every get_status/assign becomes O(n^2) and exceeds the
        # per-test time budget.
        ts = TicketSystem()
        n = 40000
        for i in range(n):
            self.assertTrue(ts.create_ticket(f"t{i:06d}", i % 10))
        for i in range(0, n, 2):
            self.assertEqual(ts.get_status(f"t{i:06d}"), "open")
        for i in range(0, n, 2):
            self.assertTrue(ts.assign(f"t{i:06d}", f"agent{i % 50}"))
        self.assertEqual(len(ts.tickets_by_status("in_progress")), n // 2)
        self.assertEqual(len(ts.tickets_by_status("open")), n - n // 2)


if __name__ == "__main__":
    unittest.main()
