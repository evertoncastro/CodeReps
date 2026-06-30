import unittest

from solution import Inventory


class Level4HiddenTests(unittest.TestCase):
    def setUp(self):
        self.inv = Inventory()
        self.inv.add_product("p1", "Widget")
        self.inv.add_stock("p1", 10)

    def test_snapshot_ids_increase_by_one(self):
        ids = [self.inv.snapshot() for _ in range(4)]
        self.assertEqual(ids, [1, 2, 3, 4])

    def test_restore_reverts_removed_stock(self):
        sid = self.inv.snapshot()
        self.inv.remove_stock("p1", 4)
        self.assertTrue(self.inv.restore(sid))
        self.assertEqual(self.inv.get_stock("p1"), 10)

    def test_restore_reverts_restore_of_archive(self):
        self.inv.archive_product("p1")
        sid = self.inv.snapshot()
        self.inv.restore_product("p1")
        self.assertFalse(self.inv.is_archived("p1"))
        self.assertTrue(self.inv.restore(sid))
        self.assertTrue(self.inv.is_archived("p1"))

    def test_restore_unknown_changes_nothing(self):
        self.inv.add_stock("p1", 5)
        self.assertFalse(self.inv.restore(42))
        self.assertEqual(self.inv.get_stock("p1"), 15)

    def test_restore_older_after_newer(self):
        s1 = self.inv.snapshot()          # stock 10
        self.inv.add_stock("p1", 10)      # stock 20
        s2 = self.inv.snapshot()          # stock 20
        self.inv.add_stock("p1", 10)      # stock 30
        self.assertTrue(self.inv.restore(s2))
        self.assertEqual(self.inv.get_stock("p1"), 20)
        self.assertTrue(self.inv.restore(s1))
        self.assertEqual(self.inv.get_stock("p1"), 10)

    def test_snapshots_independent(self):
        s1 = self.inv.snapshot()
        self.inv.add_stock("p1", 5)
        s2 = self.inv.snapshot()
        self.inv.restore(s1)
        self.assertEqual(self.inv.get_stock("p1"), 10)
        self.inv.restore(s2)
        self.assertEqual(self.inv.get_stock("p1"), 15)

    def test_changes_after_restore_work(self):
        sid = self.inv.snapshot()
        self.inv.add_stock("p1", 5)
        self.inv.restore(sid)
        self.assertEqual(self.inv.add_stock("p1", 2), 12)
        self.assertEqual(self.inv.remove_stock("p1", 1), 11)

    def test_restore_exact_product_set(self):
        self.inv.add_product("p2", "Gadget")
        sid = self.inv.snapshot()
        self.inv.add_product("p3", "Gizmo")
        self.inv.restore(sid)
        self.assertEqual(self.inv.get_product_name("p2"), "Gadget")
        self.assertIsNone(self.inv.get_product_name("p3"))
        self.assertEqual(self.inv.get_product_name("p1"), "Widget")

    def test_restore_reverts_name_only_state(self):
        sid = self.inv.snapshot()
        self.inv.add_product("p2", "Temp")
        self.inv.add_stock("p2", 3)
        self.inv.restore(sid)
        self.assertIsNone(self.inv.get_stock("p2"))

    def test_snapshot_id_not_reset_by_restore(self):
        s1 = self.inv.snapshot()
        self.inv.restore(s1)
        self.assertEqual(self.inv.snapshot(), 2)

    def test_restore_does_not_consume_snapshot(self):
        sid = self.inv.snapshot()
        self.assertTrue(self.inv.restore(sid))
        self.assertTrue(self.inv.restore(sid))

    def test_deep_copy_isolation(self):
        # Mutating stock after a snapshot must not retroactively change it.
        sid = self.inv.snapshot()
        self.inv.add_stock("p1", 100)
        self.inv.restore(sid)
        self.assertEqual(self.inv.get_stock("p1"), 10)


if __name__ == "__main__":
    unittest.main()
