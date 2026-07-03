import unittest

from solution import Bank


class Level2PublicTests(unittest.TestCase):
    def setUp(self):
        self.bank = Bank()
        self.bank.create_account("a")
        self.bank.create_account("b")
        self.bank.deposit("a", 100)

    def test_transfer_moves_funds(self):
        self.assertTrue(self.bank.transfer("a", "b", 30))
        self.assertEqual(self.bank.get_balance("a"), 70)
        self.assertEqual(self.bank.get_balance("b"), 30)

    def test_transfer_tracks_total_sent(self):
        self.bank.transfer("a", "b", 30)
        self.bank.transfer("a", "b", 20)
        self.assertEqual(self.bank.get_total_sent("a"), 50)

    def test_insufficient_funds_rejected(self):
        self.assertFalse(self.bank.transfer("a", "b", 101))
        self.assertEqual(self.bank.get_balance("a"), 100)
        self.assertEqual(self.bank.get_balance("b"), 0)

    def test_self_transfer_rejected(self):
        self.assertFalse(self.bank.transfer("a", "a", 10))
        self.assertEqual(self.bank.get_balance("a"), 100)

    def test_unknown_account_rejected(self):
        self.assertFalse(self.bank.transfer("a", "missing", 10))
        self.assertFalse(self.bank.transfer("missing", "b", 10))
        self.assertEqual(self.bank.get_balance("a"), 100)

    def test_total_sent_fresh_and_unknown(self):
        self.assertEqual(self.bank.get_total_sent("b"), 0)
        self.assertIsNone(self.bank.get_total_sent("missing"))

    def test_transfer_full_balance(self):
        self.assertTrue(self.bank.transfer("a", "b", 100))
        self.assertEqual(self.bank.get_balance("a"), 0)
        self.assertEqual(self.bank.get_total_sent("a"), 100)


if __name__ == "__main__":
    unittest.main()
