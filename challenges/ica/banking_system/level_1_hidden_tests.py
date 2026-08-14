import unittest

from solution import Bank


class Level1HiddenTests(unittest.TestCase):
    def test_duplicate_creation_keeps_balance(self):
        bank = Bank()
        bank.create_account("a")
        bank.deposit("a", 70)
        self.assertFalse(bank.create_account("a"))
        self.assertEqual(bank.get_balance("a"), 70)

    def test_deposit_returns_new_not_previous(self):
        bank = Bank()
        bank.create_account("a")
        bank.deposit("a", 100)
        self.assertEqual(bank.deposit("a", 25), 125)

    def test_deposit_zero_keeps_balance(self):
        bank = Bank()
        bank.create_account("a")
        bank.deposit("a", 40)
        self.assertEqual(bank.deposit("a", 0), 40)

    def test_new_account_balance_is_zero(self):
        bank = Bank()
        bank.create_account("a")
        self.assertEqual(bank.get_balance("a"), 0)

    def test_unknown_balance_is_none_not_zero(self):
        bank = Bank()
        self.assertIsNone(bank.get_balance("nope"))
        self.assertNotEqual(bank.get_balance("nope"), 0)

    def test_deposit_unknown_does_not_create(self):
        bank = Bank()
        self.assertIsNone(bank.deposit("ghost", 10))
        self.assertIsNone(bank.get_balance("ghost"))

    def test_many_deposits_accumulate(self):
        bank = Bank()
        bank.create_account("a")
        total = 0
        for i in range(1, 51):
            total += i
            self.assertEqual(bank.deposit("a", i), total)

    def test_large_amount(self):
        bank = Bank()
        bank.create_account("a")
        self.assertEqual(bank.deposit("a", 1_000_000_000), 1_000_000_000)

    def test_account_ids_case_sensitive(self):
        bank = Bank()
        self.assertTrue(bank.create_account("A"))
        self.assertTrue(bank.create_account("a"))
        bank.deposit("A", 5)
        self.assertEqual(bank.get_balance("A"), 5)
        self.assertEqual(bank.get_balance("a"), 0)

    def test_independent_across_many_accounts(self):
        bank = Bank()
        for i in range(10):
            bank.create_account(f"a{i}")
            bank.deposit(f"a{i}", i * 10)
        for i in range(10):
            self.assertEqual(bank.get_balance(f"a{i}"), i * 10)


if __name__ == "__main__":
    unittest.main()
