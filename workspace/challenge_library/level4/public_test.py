import unittest

from solution import Inventory


class Level4PublicTests(unittest.TestCase):
    def setUp(self):
        self.inv = Inventory()
        self.inv.add_product("p1", "Widget")
        self.inv.add_stock("p1", 10)

    def test_snapshot_ids_start_at_one(self):
        self.assertEqual(self.inv.snapshot(), 1)
        self.assertEqual(self.inv.snapshot(), 2)

    def test_restore_reverts_stock(self):
        sid = self.inv.snapshot()
        self.inv.add_stock("p1", 5)
        self.assertEqual(self.inv.get_stock("p1"), 15)
        self.assertTrue(self.inv.restore(sid))
        self.assertEqual(self.inv.get_stock("p1"), 10)

    def test_restore_removes_products_added_after(self):
        sid = self.inv.snapshot()
        self.inv.add_product("p2", "Gadget")
        self.assertTrue(self.inv.restore(sid))
        self.assertIsNone(self.inv.get_stock("p2"))
        self.assertEqual(self.inv.get_stock("p1"), 10)

    def test_restore_reverts_archive(self):
        sid = self.inv.snapshot()
        self.inv.archive_product("p1")
        self.assertTrue(self.inv.restore(sid))
        self.assertFalse(self.inv.is_archived("p1"))

    def test_restore_unknown_id_returns_false(self):
        self.assertFalse(self.inv.restore(999))
        self.assertEqual(self.inv.get_stock("p1"), 10)

    def test_restore_can_be_repeated(self):
        sid = self.inv.snapshot()
        self.inv.add_stock("p1", 7)
        self.assertTrue(self.inv.restore(sid))
        self.inv.add_stock("p1", 3)
        self.assertTrue(self.inv.restore(sid))
        self.assertEqual(self.inv.get_stock("p1"), 10)


if __name__ == "__main__":
    unittest.main()
