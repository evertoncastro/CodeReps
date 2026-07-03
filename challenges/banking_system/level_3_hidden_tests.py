import unittest

from solution import Bank


def _bank(deposits):
    bank = Bank()
    for acc, bal in deposits:
        bank.create_account(acc)
        bank.deposit(acc, bal)
    return bank


class Level3HiddenTests(unittest.TestCase):
    def test_top_spenders_tie_broken_by_id(self):
        bank = _bank([("b", 100), ("a", 100), ("c", 100)])
        bank.transfer("b", "c", 30)
        bank.transfer("a", "c", 30)  # a and b both sent 30
        self.assertEqual(bank.top_spenders(2), ["a", "b"])

    def test_non_senders_ranked_last_by_id(self):
        bank = _bank([("a", 100), ("z", 100), ("m", 100)])
        bank.transfer("m", "a", 10)  # only m sent
        self.assertEqual(bank.top_spenders(3), ["m", "a", "z"])

    def test_top_spenders_all_when_k_large(self):
        bank = _bank([("a", 100), ("b", 100)])
        bank.transfer("a", "b", 5)
        self.assertEqual(bank.top_spenders(99), ["a", "b"])

    def test_top_spenders_negative_k(self):
        bank = _bank([("a", 100)])
        self.assertEqual(bank.top_spenders(-2), [])

    def test_top_spenders_empty_bank(self):
        self.assertEqual(Bank().top_spenders(3), [])

    def test_total_balance_after_transfers(self):
        bank = _bank([("a", 100), ("b", 50)])
        bank.transfer("a", "b", 40)
        self.assertEqual(bank.total_balance(), 150)

    def test_accounts_below_excludes_threshold_value(self):
        bank = _bank([("a", 50), ("b", 100)])
        self.assertEqual(bank.accounts_below(100), ["a"])
        self.assertEqual(bank.accounts_below(50), [])

    def test_accounts_below_sorted_by_id(self):
        bank = _bank([("c", 1), ("a", 1), ("b", 1)])
        self.assertEqual(bank.accounts_below(5), ["a", "b", "c"])

    def test_accounts_below_none_match(self):
        bank = _bank([("a", 100)])
        self.assertEqual(bank.accounts_below(10), [])

    def test_performance_large_number_of_accounts(self):
        # A correct O(n)/O(n log n) design handles this well within the per-test
        # budget; a quadratic design (e.g. scanning a list per operation/lookup)
        # will exceed it.
        bank = Bank()
        n = 40000
        bank.create_account("hub")
        bank.deposit("hub", 1)
        for i in range(n):
            acc = f"a{i:06d}"
            bank.create_account(acc)
            bank.deposit(acc, 10)
            bank.transfer(acc, "hub", i % 10)
        self.assertEqual(len(bank.top_spenders(5)), 5)
        self.assertEqual(bank.get_total_sent("a000009"), 9)


if __name__ == "__main__":
    unittest.main()
