import unittest

from solution import Bank


def _bank():
    bank = Bank()
    bank.create_account("a")
    bank.create_account("b")
    bank.create_account("c")
    bank.deposit("a", 100)
    return bank


class Level4PublicTests(unittest.TestCase):
    def test_schedule_returns_incrementing_ids(self):
        bank = _bank()
        self.assertEqual(bank.schedule_transfer("a", "b", 30, 10), "t1")
        self.assertEqual(bank.schedule_transfer("a", "c", 20, 5), "t2")

    def test_schedule_unknown_account_returns_none(self):
        bank = _bank()
        self.assertIsNone(bank.schedule_transfer("a", "x", 10, 5))
        self.assertIsNone(bank.schedule_transfer("x", "a", 10, 5))

    def test_process_runs_due_in_time_order(self):
        bank = _bank()
        bank.schedule_transfer("a", "b", 30, 10)  # t1
        bank.schedule_transfer("a", "c", 20, 5)   # t2 (earlier time)
        self.assertEqual(bank.process_transfers(10), ["t2", "t1"])
        self.assertEqual(bank.get_balance("a"), 50)
        self.assertEqual(bank.get_balance("b"), 30)
        self.assertEqual(bank.get_balance("c"), 20)

    def test_process_only_due(self):
        bank = _bank()
        bank.schedule_transfer("a", "b", 30, 100)
        self.assertEqual(bank.process_transfers(10), [])
        self.assertEqual(bank.get_balance("a"), 100)

    def test_cancel_stops_processing(self):
        bank = _bank()
        pid = bank.schedule_transfer("a", "b", 30, 5)
        self.assertTrue(bank.cancel_transfer(pid))
        self.assertEqual(bank.process_transfers(10), [])
        self.assertEqual(bank.get_balance("a"), 100)

    def test_cancel_unknown_returns_false(self):
        bank = _bank()
        self.assertFalse(bank.cancel_transfer("t99"))

    def test_processed_counts_toward_total_sent(self):
        bank = _bank()
        bank.schedule_transfer("a", "b", 40, 5)
        bank.process_transfers(5)
        self.assertEqual(bank.get_total_sent("a"), 40)


if __name__ == "__main__":
    unittest.main()
