import unittest

from solution import TicketSystem


class Level3PublicTests(unittest.TestCase):
    def test_history_starts_open(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 5)
        self.assertEqual(ts.history("t1"), ["open"])

    def test_history_records_transitions(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 5)
        ts.assign("t1", "a")
        ts.resolve("t1")
        self.assertEqual(ts.history("t1"), ["open", "in_progress", "resolved"])

    def test_history_records_reopen(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 5)
        ts.assign("t1", "a")
        ts.resolve("t1")
        ts.reopen("t1")
        self.assertEqual(ts.history("t1"), ["open", "in_progress", "resolved", "open"])

    def test_history_unknown_is_none(self):
        self.assertIsNone(TicketSystem().history("ghost"))

    def test_tickets_by_status_sorted(self):
        ts = TicketSystem()
        for tid in ["t3", "t1", "t2"]:
            ts.create_ticket(tid, 1)
        ts.assign("t2", "a")
        self.assertEqual(ts.tickets_by_status("open"), ["t1", "t3"])
        self.assertEqual(ts.tickets_by_status("in_progress"), ["t2"])

    def test_agent_workload_counts_in_progress(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 1)
        ts.create_ticket("t2", 1)
        ts.assign("t1", "alice")
        ts.assign("t2", "alice")
        self.assertEqual(ts.agent_workload("alice"), 2)

    def test_agent_workload_drops_after_resolve(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 1)
        ts.assign("t1", "alice")
        ts.resolve("t1")
        self.assertEqual(ts.agent_workload("alice"), 0)

    def test_busiest_agent(self):
        ts = TicketSystem()
        for i in range(3):
            ts.create_ticket(f"a{i}", 1)
            ts.assign(f"a{i}", "alice")
        ts.create_ticket("b0", 1)
        ts.assign("b0", "bob")
        self.assertEqual(ts.busiest_agent(), "alice")

    def test_busiest_agent_none_when_idle(self):
        ts = TicketSystem()
        ts.create_ticket("t1", 1)
        self.assertIsNone(ts.busiest_agent())


if __name__ == "__main__":
    unittest.main()
