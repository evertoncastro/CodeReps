import unittest

from solution import Bank


class Level1PublicTests(unittest.TestCase):
    def test_create_account_starts_at_zero(self):
        bank = Bank()
        self.assertTrue(bank.create_account("a"))
        self.assertEqual(bank.get_balance("a"), 0)

    def test_duplicate_account_returns_false(self):
        bank = Bank()
        bank.create_account("a")
        self.assertFalse(bank.create_account("a"))

    def test_deposit_returns_new_balance(self):
        bank = Bank()
        bank.create_account("a")
        self.assertEqual(bank.deposit("a", 100), 100)
        self.assertEqual(bank.get_balance("a"), 100)

    def test_deposits_accumulate(self):
        bank = Bank()
        bank.create_account("a")
        bank.deposit("a", 100)
        self.assertEqual(bank.deposit("a", 50), 150)

    def test_deposit_unknown_account_returns_none(self):
        bank = Bank()
        self.assertIsNone(bank.deposit("missing", 100))

    def test_balance_unknown_account_returns_none(self):
        bank = Bank()
        self.assertIsNone(bank.get_balance("missing"))

    def test_accounts_are_independent(self):
        bank = Bank()
        bank.create_account("a")
        bank.create_account("b")
        bank.deposit("a", 100)
        self.assertEqual(bank.get_balance("a"), 100)
        self.assertEqual(bank.get_balance("b"), 0)


if __name__ == "__main__":
    unittest.main()
