import unittest

from solution import Bank


def _bank(balances):
    bank = Bank()
    for acc, bal in balances.items():
        bank.create_account(acc)
        if bal:
            bank.deposit(acc, bal)
    return bank


class Level2HiddenTests(unittest.TestCase):
    def test_transfer_conserves_funds(self):
        bank = _bank({"a": 100, "b": 20})
        bank.transfer("a", "b", 30)
        self.assertEqual(bank.get_balance("a") + bank.get_balance("b"), 120)

    def test_insufficient_leaves_both_unchanged(self):
        bank = _bank({"a": 40, "b": 5})
        self.assertFalse(bank.transfer("a", "b", 41))
        self.assertEqual(bank.get_balance("a"), 40)
        self.assertEqual(bank.get_balance("b"), 5)

    def test_rejected_transfer_does_not_count_sent(self):
        bank = _bank({"a": 40, "b": 0})
        bank.transfer("a", "b", 999)   # insufficient
        bank.transfer("a", "a", 10)    # self
        bank.transfer("a", "x", 10)    # unknown
        self.assertEqual(bank.get_total_sent("a"), 0)

    def test_self_transfer_rejected(self):
        bank = _bank({"a": 50})
        self.assertFalse(bank.transfer("a", "a", 10))

    def test_transfer_to_unknown_rejected(self):
        bank = _bank({"a": 50})
        self.assertFalse(bank.transfer("a", "b", 10))
        self.assertEqual(bank.get_balance("a"), 50)

    def test_transfer_from_unknown_rejected(self):
        bank = _bank({"b": 50})
        self.assertFalse(bank.transfer("a", "b", 10))

    def test_receiver_total_sent_unaffected(self):
        bank = _bank({"a": 100, "b": 0})
        bank.transfer("a", "b", 40)
        self.assertEqual(bank.get_total_sent("b"), 0)

    def test_zero_transfer_allowed(self):
        bank = _bank({"a": 10, "b": 0})
        self.assertTrue(bank.transfer("a", "b", 0))
        self.assertEqual(bank.get_total_sent("a"), 0)

    def test_total_sent_accumulates_across_receivers(self):
        bank = _bank({"a": 100, "b": 0, "c": 0})
        bank.transfer("a", "b", 10)
        bank.transfer("a", "c", 25)
        self.assertEqual(bank.get_total_sent("a"), 35)

    def test_full_balance_transfer_to_zero(self):
        bank = _bank({"a": 60, "b": 0})
        self.assertTrue(bank.transfer("a", "b", 60))
        self.assertEqual(bank.get_balance("a"), 0)

    def test_total_sent_unknown_is_none(self):
        bank = _bank({"a": 10})
        self.assertIsNone(bank.get_total_sent("missing"))

    def test_deposit_still_works_after_transfers(self):
        bank = _bank({"a": 100, "b": 0})
        bank.transfer("a", "b", 40)
        self.assertEqual(bank.deposit("a", 10), 70)


if __name__ == "__main__":
    unittest.main()
