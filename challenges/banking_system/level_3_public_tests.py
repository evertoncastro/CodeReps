import unittest

from solution import Bank


class Level3PublicTests(unittest.TestCase):
    def setUp(self):
        self.bank = Bank()
        for acc in ("a", "b", "c"):
            self.bank.create_account(acc)
            self.bank.deposit(acc, 100)
        self.bank.transfer("a", "b", 50)  # a sent 50
        self.bank.transfer("a", "c", 10)  # a sent 60
        self.bank.transfer("b", "c", 20)  # b sent 20

    def test_top_spenders_orders_by_sent_desc(self):
        self.assertEqual(self.bank.top_spenders(2), ["a", "b"])

    def test_top_spenders_k_zero(self):
        self.assertEqual(self.bank.top_spenders(0), [])

    def test_top_spenders_more_than_accounts(self):
        self.assertEqual(self.bank.top_spenders(9), ["a", "b", "c"])

    def test_total_balance_is_conserved(self):
        self.assertEqual(self.bank.total_balance(), 300)

    def test_total_balance_empty(self):
        self.assertEqual(Bank().total_balance(), 0)

    def test_accounts_below_threshold(self):
        # balances: a=40, b=130, c=130
        self.assertEqual(self.bank.accounts_below(100), ["a"])

    def test_accounts_below_is_strict(self):
        self.assertEqual(self.bank.accounts_below(40), [])


if __name__ == "__main__":
    unittest.main()
