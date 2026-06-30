import unittest

from solution import Inventory


def _stocked(pairs):
    inv = Inventory()
    for pid, name, qty in pairs:
        inv.add_product(pid, name)
        inv.add_stock(pid, qty)
    return inv


class Level3HiddenTests(unittest.TestCase):
    def test_total_stock_includes_archived(self):
        inv = _stocked([("p1", "A", 5), ("p2", "B", 7)])
        inv.archive_product("p1")
        self.assertEqual(inv.total_stock(), 12)

    def test_top_products_tie_broken_by_id_asc(self):
        inv = _stocked([("b", "X", 10), ("a", "Y", 10), ("c", "Z", 5)])
        self.assertEqual(inv.top_products(2), ["a", "b"])

    def test_top_products_all_when_k_large(self):
        inv = _stocked([("p1", "A", 1), ("p2", "B", 2)])
        self.assertEqual(inv.top_products(99), ["p2", "p1"])

    def test_top_products_negative_k(self):
        inv = _stocked([("p1", "A", 1)])
        self.assertEqual(inv.top_products(-3), [])

    def test_top_products_empty_inventory(self):
        self.assertEqual(Inventory().top_products(3), [])

    def test_top_products_includes_archived(self):
        inv = _stocked([("p1", "A", 100), ("p2", "B", 1)])
        inv.archive_product("p1")
        self.assertEqual(inv.top_products(1), ["p1"])

    def test_low_stock_excludes_threshold_value(self):
        inv = _stocked([("p1", "A", 5), ("p2", "B", 10)])
        self.assertEqual(inv.low_stock_products(10), ["p1"])
        self.assertEqual(inv.low_stock_products(5), [])

    def test_low_stock_sorted_by_id(self):
        inv = _stocked([("p3", "A", 1), ("p1", "B", 1), ("p2", "C", 1)])
        self.assertEqual(inv.low_stock_products(5), ["p1", "p2", "p3"])

    def test_low_stock_empty(self):
        self.assertEqual(Inventory().low_stock_products(100), [])

    def test_find_prefix_matches_name_not_id(self):
        inv = _stocked([("x1", "Alpha", 1), ("x2", "Beta", 1), ("x3", "Alfa", 1)])
        self.assertEqual(inv.find_products_by_name_prefix("Al"), ["x1", "x3"])

    def test_find_prefix_no_match(self):
        inv = _stocked([("p1", "Apple", 1)])
        self.assertEqual(inv.find_products_by_name_prefix("Z"), [])

    def test_find_prefix_case_sensitive(self):
        inv = _stocked([("p1", "Apple", 1), ("p2", "apple", 1)])
        self.assertEqual(inv.find_products_by_name_prefix("a"), ["p2"])

    def test_find_prefix_includes_archived(self):
        inv = _stocked([("p1", "Apple", 1)])
        inv.archive_product("p1")
        self.assertEqual(inv.find_products_by_name_prefix("App"), ["p1"])

    def test_find_empty_prefix_sorted(self):
        inv = _stocked([("p2", "B", 1), ("p1", "A", 1)])
        self.assertEqual(inv.find_products_by_name_prefix(""), ["p1", "p2"])


if __name__ == "__main__":
    unittest.main()
