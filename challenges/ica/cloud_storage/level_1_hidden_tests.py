import unittest

from solution import FileSystem


class Level1HiddenTests(unittest.TestCase):
    def test_create_zero_size_file(self):
        fs = FileSystem()
        self.assertTrue(fs.create_file("/empty", 0))
        self.assertEqual(fs.get_size("/empty"), 0)

    def test_get_size_zero_is_not_confused_with_none(self):
        fs = FileSystem()
        fs.create_file("/empty", 0)
        self.assertIsNotNone(fs.get_size("/empty"))
        self.assertEqual(fs.get_size("/empty"), 0)

    def test_duplicate_create_returns_false_repeatedly(self):
        fs = FileSystem()
        fs.create_file("/a", 5)
        self.assertFalse(fs.create_file("/a", 6))
        self.assertFalse(fs.create_file("/a", 7))
        self.assertEqual(fs.get_size("/a"), 5)

    def test_delete_twice_returns_none_second_time(self):
        fs = FileSystem()
        fs.create_file("/a", 5)
        self.assertEqual(fs.delete("/a"), 5)
        self.assertIsNone(fs.delete("/a"))

    def test_delete_only_targeted_file(self):
        fs = FileSystem()
        fs.create_file("/a", 1)
        fs.create_file("/b", 2)
        fs.delete("/a")
        self.assertIsNone(fs.get_size("/a"))
        self.assertEqual(fs.get_size("/b"), 2)

    def test_recreate_after_delete(self):
        fs = FileSystem()
        fs.create_file("/a", 1)
        fs.delete("/a")
        self.assertTrue(fs.create_file("/a", 8))
        self.assertEqual(fs.get_size("/a"), 8)

    def test_move_missing_source_fails(self):
        fs = FileSystem()
        self.assertFalse(fs.move_file("/a", "/b"))
        self.assertIsNone(fs.get_size("/b"))

    def test_move_to_same_path_fails(self):
        fs = FileSystem()
        fs.create_file("/a", 3)
        self.assertFalse(fs.move_file("/a", "/a"))
        self.assertEqual(fs.get_size("/a"), 3)

    def test_move_preserves_size(self):
        fs = FileSystem()
        fs.create_file("/a", 123)
        fs.move_file("/a", "/deep/nested/path")
        self.assertEqual(fs.get_size("/deep/nested/path"), 123)

    def test_move_frees_source_for_recreation(self):
        fs = FileSystem()
        fs.create_file("/a", 3)
        fs.move_file("/a", "/b")
        self.assertTrue(fs.create_file("/a", 4))
        self.assertEqual(fs.get_size("/a"), 4)
        self.assertEqual(fs.get_size("/b"), 3)

    def test_move_dest_exists_leaves_both_unchanged(self):
        fs = FileSystem()
        fs.create_file("/a", 1)
        fs.create_file("/b", 2)
        self.assertFalse(fs.move_file("/a", "/b"))
        self.assertEqual(fs.get_size("/a"), 1)
        self.assertEqual(fs.get_size("/b"), 2)

    def test_delete_after_move_returns_size_at_dest(self):
        fs = FileSystem()
        fs.create_file("/a", 55)
        fs.move_file("/a", "/b")
        self.assertEqual(fs.delete("/b"), 55)
        self.assertIsNone(fs.delete("/a"))


if __name__ == "__main__":
    unittest.main()
