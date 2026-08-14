import unittest

from solution import FileSystem


class Level1PublicTests(unittest.TestCase):
    def test_create_file_returns_true(self):
        fs = FileSystem()
        self.assertTrue(fs.create_file("/a.txt", 100))

    def test_create_duplicate_returns_false(self):
        fs = FileSystem()
        fs.create_file("/a.txt", 100)
        self.assertFalse(fs.create_file("/a.txt", 999))

    def test_duplicate_does_not_overwrite_size(self):
        fs = FileSystem()
        fs.create_file("/a.txt", 100)
        fs.create_file("/a.txt", 999)
        self.assertEqual(fs.get_size("/a.txt"), 100)

    def test_get_size_unknown_is_none(self):
        fs = FileSystem()
        self.assertIsNone(fs.get_size("/missing"))

    def test_delete_returns_size_and_removes(self):
        fs = FileSystem()
        fs.create_file("/a.txt", 42)
        self.assertEqual(fs.delete("/a.txt"), 42)
        self.assertIsNone(fs.get_size("/a.txt"))

    def test_delete_unknown_is_none(self):
        fs = FileSystem()
        self.assertIsNone(fs.delete("/nope"))

    def test_move_file_success(self):
        fs = FileSystem()
        fs.create_file("/a.txt", 7)
        self.assertTrue(fs.move_file("/a.txt", "/b.txt"))
        self.assertEqual(fs.get_size("/b.txt"), 7)
        self.assertIsNone(fs.get_size("/a.txt"))

    def test_move_file_dest_exists_fails(self):
        fs = FileSystem()
        fs.create_file("/a.txt", 7)
        fs.create_file("/b.txt", 9)
        self.assertFalse(fs.move_file("/a.txt", "/b.txt"))
        self.assertEqual(fs.get_size("/a.txt"), 7)
        self.assertEqual(fs.get_size("/b.txt"), 9)


if __name__ == "__main__":
    unittest.main()
