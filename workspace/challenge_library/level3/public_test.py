import unittest

from solution import Inventory


class Level3PublicTests(unittest.TestCase):
    def setUp(self):
        self.inv = Inventory()
        for pid, name, qty in [
            ("p1", "Apple", 30),
            ("p2", "Apricot", 10),
            ("p3", "Banana", 20),
        ]:
            self.inv.add_product(pid, name)
            self.inv.add_stock(pid, qty)

    def test_total_stock(self):
        self.assertEqual(self.inv.total_stock(), 60)

    def test_total_stock_empty(self):
        self.assertEqual(Inventory().total_stock(), 0)

    def test_top_products_orders_by_stock_desc(self):
        self.assertEqual(self.inv.top_products(2), ["p1", "p3"])

    def test_top_products_k_zero(self):
        self.assertEqual(self.inv.top_products(0), [])

    def test_top_products_more_than_available(self):
        self.assertEqual(self.inv.top_products(10), ["p1", "p3", "p2"])

    def test_low_stock_strictly_less(self):
        self.assertEqual(self.inv.low_stock_products(20), ["p2"])

    def test_find_by_name_prefix(self):
        self.assertEqual(self.inv.find_products_by_name_prefix("Ap"), ["p1", "p2"])

    def test_find_by_empty_prefix_returns_all(self):
        self.assertEqual(self.inv.find_products_by_name_prefix(""), ["p1", "p2", "p3"])


if __name__ == "__main__":
    unittest.main()
