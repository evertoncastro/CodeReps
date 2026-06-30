import unittest

from solution import Inventory


class Level1HiddenTests(unittest.TestCase):
    def test_duplicate_registration_keeps_existing_stock(self):
        inv = Inventory()
        inv.add_product("p1", "Widget")
        inv.add_stock("p1", 7)
        self.assertFalse(inv.add_product("p1", "Gadget"))
        self.assertEqual(inv.get_stock("p1"), 7)

    def test_duplicate_registration_keeps_existing_name(self):
        inv = Inventory()
        inv.add_product("p1", "Widget")
        inv.add_product("p1", "Gadget")
        self.assertEqual(inv.get_product_name("p1"), "Widget")

    def test_add_zero_stock_keeps_total(self):
        inv = Inventory()
        inv.add_product("p1", "Widget")
        inv.add_stock("p1", 4)
        self.assertEqual(inv.add_stock("p1", 0), 4)
        self.assertEqual(inv.get_stock("p1"), 4)

    def test_add_stock_returns_new_total_not_previous(self):
        inv = Inventory()
        inv.add_product("p1", "Widget")
        inv.add_stock("p1", 10)
        self.assertEqual(inv.add_stock("p1", 5), 15)

    def test_many_sequential_additions_accumulate(self):
        inv = Inventory()
        inv.add_product("p1", "Widget")
        total = 0
        for i in range(1, 51):
            total += i
            self.assertEqual(inv.add_stock("p1", i), total)
        self.assertEqual(inv.get_stock("p1"), total)

    def test_large_quantity(self):
        inv = Inventory()
        inv.add_product("p1", "Widget")
        self.assertEqual(inv.add_stock("p1", 1_000_000_000), 1_000_000_000)

    def test_unknown_get_stock_is_none_not_zero(self):
        inv = Inventory()
        self.assertIsNone(inv.get_stock("nope"))
        self.assertNotEqual(inv.get_stock("nope"), 0)

    def test_unknown_get_name_is_none(self):
        inv = Inventory()
        self.assertIsNone(inv.get_product_name("nope"))

    def test_add_stock_unknown_does_not_create_product(self):
        inv = Inventory()
        self.assertIsNone(inv.add_stock("ghost", 5))
        self.assertIsNone(inv.get_stock("ghost"))
        self.assertIsNone(inv.get_product_name("ghost"))

    def test_product_ids_are_case_sensitive(self):
        inv = Inventory()
        self.assertTrue(inv.add_product("P1", "Upper"))
        self.assertTrue(inv.add_product("p1", "Lower"))
        self.assertEqual(inv.get_product_name("P1"), "Upper")
        self.assertEqual(inv.get_product_name("p1"), "Lower")

    def test_stock_isolation_across_many_products(self):
        inv = Inventory()
        for i in range(10):
            inv.add_product(f"p{i}", f"name{i}")
            inv.add_stock(f"p{i}", i * 2)
        for i in range(10):
            self.assertEqual(inv.get_stock(f"p{i}"), i * 2)

    def test_new_product_starts_at_zero_before_any_add(self):
        inv = Inventory()
        inv.add_product("p1", "Widget")
        self.assertEqual(inv.get_stock("p1"), 0)

    def test_empty_string_name_is_stored(self):
        inv = Inventory()
        self.assertTrue(inv.add_product("p1", ""))
        self.assertEqual(inv.get_product_name("p1"), "")


if __name__ == "__main__":
    unittest.main()
