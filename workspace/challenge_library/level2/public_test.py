import unittest

from solution import Inventory


class Level2PublicTests(unittest.TestCase):
    def setUp(self):
        self.inv = Inventory()
        self.inv.add_product("p1", "Widget")
        self.inv.add_stock("p1", 10)

    def test_remove_stock_returns_new_total(self):
        self.assertEqual(self.inv.remove_stock("p1", 4), 6)
        self.assertEqual(self.inv.get_stock("p1"), 6)

    def test_remove_more_than_available_is_rejected(self):
        self.assertIsNone(self.inv.remove_stock("p1", 11))
        self.assertEqual(self.inv.get_stock("p1"), 10)

    def test_remove_exact_brings_to_zero(self):
        self.assertEqual(self.inv.remove_stock("p1", 10), 0)

    def test_remove_unknown_product_returns_none(self):
        self.assertIsNone(self.inv.remove_stock("missing", 1))

    def test_archive_and_is_archived(self):
        self.assertFalse(self.inv.is_archived("p1"))
        self.assertTrue(self.inv.archive_product("p1"))
        self.assertTrue(self.inv.is_archived("p1"))

    def test_archived_product_rejects_stock_changes(self):
        self.inv.archive_product("p1")
        self.assertIsNone(self.inv.add_stock("p1", 5))
        self.assertIsNone(self.inv.remove_stock("p1", 1))
        self.assertEqual(self.inv.get_stock("p1"), 10)

    def test_restore_reenables_stock_changes(self):
        self.inv.archive_product("p1")
        self.assertTrue(self.inv.restore_product("p1"))
        self.assertFalse(self.inv.is_archived("p1"))
        self.assertEqual(self.inv.add_stock("p1", 5), 15)

    def test_is_archived_unknown_returns_none(self):
        self.assertIsNone(self.inv.is_archived("missing"))


if __name__ == "__main__":
    unittest.main()
