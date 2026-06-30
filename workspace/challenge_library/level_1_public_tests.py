import unittest

from solution import Inventory


class Level1PublicTests(unittest.TestCase):
    def test_add_product_returns_true_and_starts_at_zero(self):
        inv = Inventory()
        self.assertTrue(inv.add_product("p1", "Widget"))
        self.assertEqual(inv.get_stock("p1"), 0)
        self.assertEqual(inv.get_product_name("p1"), "Widget")

    def test_duplicate_product_returns_false(self):
        inv = Inventory()
        inv.add_product("p1", "Widget")
        self.assertFalse(inv.add_product("p1", "Gadget"))
        # Name must stay unchanged after a rejected duplicate.
        self.assertEqual(inv.get_product_name("p1"), "Widget")

    def test_add_stock_returns_new_total(self):
        inv = Inventory()
        inv.add_product("p1", "Widget")
        self.assertEqual(inv.add_stock("p1", 5), 5)
        self.assertEqual(inv.get_stock("p1"), 5)

    def test_add_stock_accumulates(self):
        inv = Inventory()
        inv.add_product("p1", "Widget")
        inv.add_stock("p1", 5)
        self.assertEqual(inv.add_stock("p1", 3), 8)
        self.assertEqual(inv.get_stock("p1"), 8)

    def test_add_stock_unknown_product_returns_none(self):
        inv = Inventory()
        self.assertIsNone(inv.add_stock("missing", 5))

    def test_lookups_on_unknown_product_return_none(self):
        inv = Inventory()
        self.assertIsNone(inv.get_stock("missing"))
        self.assertIsNone(inv.get_product_name("missing"))

    def test_products_are_independent(self):
        inv = Inventory()
        inv.add_product("p1", "Widget")
        inv.add_product("p2", "Gadget")
        inv.add_stock("p1", 10)
        self.assertEqual(inv.get_stock("p1"), 10)
        self.assertEqual(inv.get_stock("p2"), 0)


if __name__ == "__main__":
    unittest.main()
