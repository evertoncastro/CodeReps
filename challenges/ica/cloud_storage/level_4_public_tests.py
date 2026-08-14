import unittest

from solution import FileSystem


class Level4PublicTests(unittest.TestCase):
    def test_alive_within_window(self):
        fs = FileSystem()
        fs.create_file_at(100, "/tmp/a", 30, 10)  # alive [100, 110)
        self.assertEqual(fs.get_size_at(100, "/tmp/a"), 30)
        self.assertEqual(fs.get_size_at(109, "/tmp/a"), 30)

    def test_expired_returns_none(self):
        fs = FileSystem()
        fs.create_file_at(100, "/tmp/a", 30, 10)
        self.assertIsNone(fs.get_size_at(110, "/tmp/a"))

    def test_before_creation_returns_none(self):
        fs = FileSystem()
        fs.create_file_at(100, "/tmp/a", 30, 10)
        self.assertIsNone(fs.get_size_at(99, "/tmp/a"))

    def test_create_at_duplicate_returns_false(self):
        fs = FileSystem()
        fs.create_file_at(100, "/tmp/a", 30, 10)
        self.assertFalse(fs.create_file_at(200, "/tmp/a", 99, 10))

    def test_permanent_file_alive_any_time(self):
        fs = FileSystem()
        fs.create_file("/perm", 5)
        self.assertEqual(fs.get_size_at(0, "/perm"), 5)
        self.assertEqual(fs.get_size_at(10**9, "/perm"), 5)

    def test_total_size_at_excludes_expired(self):
        fs = FileSystem()
        fs.create_file("/perm", 5)
        fs.create_file_at(100, "/tmp/a", 30, 10)
        self.assertEqual(fs.total_size_at(105, "/"), 35)
        self.assertEqual(fs.total_size_at(200, "/"), 5)

    def test_total_size_at_directory_scope(self):
        fs = FileSystem()
        fs.create_file_at(0, "/docs/a", 10, 100)
        fs.create_file_at(0, "/images/b", 20, 100)
        self.assertEqual(fs.total_size_at(50, "/docs"), 10)


if __name__ == "__main__":
    unittest.main()
