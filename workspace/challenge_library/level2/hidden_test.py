import unittest

from solution import Inventory


class Level2HiddenTests(unittest.TestCase):
    def setUp(self):
        self.inv = Inventory()
        self.inv.add_product("p1", "Widget")
        self.inv.add_stock("p1", 5)

    def test_remove_too_much_leaves_stock_unchanged(self):
        self.assertIsNone(self.inv.remove_stock("p1", 6))
        self.assertEqual(self.inv.get_stock("p1"), 5)

    def test_remove_zero_keeps_total(self):
        self.assertEqual(self.inv.remove_stock("p1", 0), 5)

    def test_remove_unknown_does_not_create_product(self):
        self.assertIsNone(self.inv.remove_stock("ghost", 1))
        self.assertIsNone(self.inv.get_stock("ghost"))

    def test_sequential_removes_accumulate(self):
        self.assertEqual(self.inv.remove_stock("p1", 2), 3)
        self.assertEqual(self.inv.remove_stock("p1", 3), 0)
        self.assertIsNone(self.inv.remove_stock("p1", 1))

    def test_archive_unknown_returns_false(self):
        self.assertFalse(self.inv.archive_product("missing"))

    def test_archive_already_archived_returns_false(self):
        self.assertTrue(self.inv.archive_product("p1"))
        self.assertFalse(self.inv.archive_product("p1"))

    def test_restore_non_archived_returns_false(self):
        self.assertFalse(self.inv.restore_product("p1"))

    def test_restore_unknown_returns_false(self):
        self.assertFalse(self.inv.restore_product("missing"))

    def test_fresh_product_is_not_archived(self):
        self.inv.add_product("p2", "Gadget")
        self.assertFalse(self.inv.is_archived("p2"))

    def test_archived_add_stock_rejected_and_unchanged(self):
        self.inv.archive_product("p1")
        self.assertIsNone(self.inv.add_stock("p1", 3))
        self.assertEqual(self.inv.get_stock("p1"), 5)

    def test_archive_preserves_name_and_stock(self):
        self.inv.archive_product("p1")
        self.assertEqual(self.inv.get_product_name("p1"), "Widget")
        self.assertEqual(self.inv.get_stock("p1"), 5)

    def test_archive_restore_cycle(self):
        self.assertTrue(self.inv.archive_product("p1"))
        self.assertTrue(self.inv.restore_product("p1"))
        self.assertTrue(self.inv.archive_product("p1"))
        self.assertTrue(self.inv.is_archived("p1"))

    def test_remove_from_archived_returns_none(self):
        self.inv.archive_product("p1")
        self.assertIsNone(self.inv.remove_stock("p1", 1))

    def test_independent_archive_state(self):
        self.inv.add_product("p2", "Gadget")
        self.inv.archive_product("p1")
        self.assertFalse(self.inv.is_archived("p2"))
        self.assertTrue(self.inv.is_archived("p1"))


if __name__ == "__main__":
    unittest.main()
