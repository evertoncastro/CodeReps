import unittest

from solution import Bank


def _bank(deposits):
    bank = Bank()
    for acc, bal in deposits:
        bank.create_account(acc)
        bank.deposit(acc, bal)
    return bank


class Level4HiddenTests(unittest.TestCase):
    def test_schedule_unknown_does_not_consume_id(self):
        bank = _bank([("a", 100), ("b", 0)])
        self.assertIsNone(bank.schedule_transfer("a", "x", 10, 1))
        self.assertEqual(bank.schedule_transfer("a", "b", 10, 1), "t1")

    def test_only_due_transfers_run(self):
        bank = _bank([("a", 100), ("b", 0)])
        bank.schedule_transfer("a", "b", 10, 5)    # t1 due
        bank.schedule_transfer("a", "b", 10, 50)   # t2 not due
        self.assertEqual(bank.process_transfers(10), ["t1"])
        self.assertEqual(bank.get_balance("b"), 10)

    def test_ties_processed_in_creation_order(self):
        bank = _bank([("a", 100), ("b", 0), ("c", 0)])
        bank.schedule_transfer("a", "b", 10, 5)  # t1
        bank.schedule_transfer("a", "c", 10, 5)  # t2 same time
        self.assertEqual(bank.process_transfers(5), ["t1", "t2"])

    def test_insufficient_funds_fails_others_run(self):
        bank = _bank([("a", 50), ("b", 0)])
        bank.schedule_transfer("a", "b", 40, 1)  # t1 ok -> a=10
        bank.schedule_transfer("a", "b", 40, 1)  # t2 insufficient
        self.assertEqual(bank.process_transfers(1), ["t1"])
        self.assertEqual(bank.get_balance("a"), 10)

    def test_failed_transfer_not_retried(self):
        bank = _bank([("a", 0), ("b", 0)])
        bank.schedule_transfer("a", "b", 40, 1)  # fails, a has 0
        self.assertEqual(bank.process_transfers(1), [])
        bank.deposit("a", 100)
        # already failed -> must not run again even now that funds exist
        self.assertEqual(bank.process_transfers(2), [])
        self.assertEqual(bank.get_balance("b"), 0)

    def test_processed_not_repeated(self):
        bank = _bank([("a", 100), ("b", 0)])
        bank.schedule_transfer("a", "b", 30, 1)
        self.assertEqual(bank.process_transfers(1), ["t1"])
        self.assertEqual(bank.process_transfers(5), [])
        self.assertEqual(bank.get_balance("b"), 30)

    def test_self_transfer_scheduled_then_fails(self):
        bank = _bank([("a", 100)])
        bank.schedule_transfer("a", "a", 10, 1)
        self.assertEqual(bank.process_transfers(1), [])
        self.assertEqual(bank.get_balance("a"), 100)

    def test_cancel_already_processed_returns_false(self):
        bank = _bank([("a", 100), ("b", 0)])
        pid = bank.schedule_transfer("a", "b", 30, 1)
        bank.process_transfers(1)
        self.assertFalse(bank.cancel_transfer(pid))

    def test_cancel_twice_returns_false(self):
        bank = _bank([("a", 100), ("b", 0)])
        pid = bank.schedule_transfer("a", "b", 30, 5)
        self.assertTrue(bank.cancel_transfer(pid))
        self.assertFalse(bank.cancel_transfer(pid))

    def test_ids_increment_across_schedules(self):
        bank = _bank([("a", 100), ("b", 0)])
        ids = [bank.schedule_transfer("a", "b", 1, 1) for _ in range(3)]
        self.assertEqual(ids, ["t1", "t2", "t3"])

    def test_processed_affects_top_spenders(self):
        bank = _bank([("a", 100), ("b", 100), ("c", 0)])
        bank.transfer("b", "c", 10)              # b sent 10 now
        bank.schedule_transfer("a", "c", 50, 1)  # a will send 50 when processed
        bank.process_transfers(1)
        self.assertEqual(bank.top_spenders(2), ["a", "b"])

    def test_later_transfer_still_pending(self):
        bank = _bank([("a", 100), ("b", 0)])
        bank.schedule_transfer("a", "b", 10, 100)  # t1 far future
        self.assertEqual(bank.process_transfers(1), [])
        self.assertEqual(bank.process_transfers(100), ["t1"])


if __name__ == "__main__":
    unittest.main()
