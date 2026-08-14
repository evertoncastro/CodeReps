import unittest

from solution import FileSystem


class Level4HiddenTests(unittest.TestCase):
    def test_alive_at_exact_creation(self):
        fs = FileSystem()
        fs.create_file_at(100, "/a", 7, 5)
        self.assertEqual(fs.get_size_at(100, "/a"), 7)

    def test_alive_at_last_valid_tick(self):
        fs = FileSystem()
        fs.create_file_at(100, "/a", 7, 5)  # [100, 105)
        self.assertEqual(fs.get_size_at(104, "/a"), 7)

    def test_dead_at_expiry_boundary(self):
        fs = FileSystem()
        fs.create_file_at(100, "/a", 7, 5)  # expires at 105
        self.assertIsNone(fs.get_size_at(105, "/a"))

    def test_ttl_one_lives_single_tick(self):
        fs = FileSystem()
        fs.create_file_at(100, "/a", 7, 1)  # [100, 101)
        self.assertEqual(fs.get_size_at(100, "/a"), 7)
        self.assertIsNone(fs.get_size_at(101, "/a"))

    def test_duplicate_path_even_after_expiry(self):
        fs = FileSystem()
        fs.create_file_at(100, "/a", 7, 5)
        # long after expiry, the path is still reserved
        self.assertFalse(fs.create_file_at(1000, "/a", 99, 5))
        self.assertIsNone(fs.get_size_at(1000, "/a"))

    def test_duplicate_against_permanent_file(self):
        fs = FileSystem()
        fs.create_file("/a", 5)
        self.assertFalse(fs.create_file_at(0, "/a", 9, 100))

    def test_permanent_file_size_at_any_time(self):
        fs = FileSystem()
        fs.create_file("/a", 5)
        self.assertEqual(fs.get_size_at(0, "/a"), 5)
        self.assertEqual(fs.get_size_at(999999, "/a"), 5)

    def test_owned_file_is_permanent_for_at_queries(self):
        fs = FileSystem()
        fs.add_user("u1", 100)
        fs.create_file_by("u1", "/u1/a", 40)
        self.assertEqual(fs.get_size_at(0, "/u1/a"), 40)
        self.assertEqual(fs.get_size_at(10**6, "/u1/a"), 40)

    def test_total_size_at_mixes_permanent_and_temporary(self):
        fs = FileSystem()
        fs.create_file("/data/perm", 100)
        fs.create_file_at(0, "/data/t1", 10, 50)   # [0, 50)
        fs.create_file_at(0, "/data/t2", 20, 100)  # [0, 100)
        self.assertEqual(fs.total_size_at(10, "/data"), 130)
        self.assertEqual(fs.total_size_at(60, "/data"), 120)
        self.assertEqual(fs.total_size_at(150, "/data"), 100)

    def test_total_size_at_segment_aware(self):
        fs = FileSystem()
        fs.create_file_at(0, "/docs/a", 10, 100)
        fs.create_file_at(0, "/docs2/b", 20, 100)
        self.assertEqual(fs.total_size_at(10, "/docs"), 10)

    def test_total_size_at_before_and_after(self):
        fs = FileSystem()
        fs.create_file_at(50, "/a", 10, 10)  # [50, 60)
        self.assertEqual(fs.total_size_at(49, "/"), 0)
        self.assertEqual(fs.total_size_at(50, "/"), 10)
        self.assertEqual(fs.total_size_at(59, "/"), 10)
        self.assertEqual(fs.total_size_at(60, "/"), 0)

    def test_not_yet_alive_excluded(self):
        fs = FileSystem()
        fs.create_file_at(100, "/a", 10, 10)
        self.assertEqual(fs.total_size_at(0, "/"), 0)

    def test_performance_many_temporary_files(self):
        fs = FileSystem()
        n = 40000
        for i in range(n):
            # each alive during [i, i + 100)
            fs.create_file_at(i, f"/tmp/f{i:06d}", 1, 100)
        # at t = n-1, only files created in (n-101, n-1] are alive: at most 100
        alive = fs.total_size_at(n - 1, "/")
        self.assertEqual(alive, 100)
        self.assertEqual(fs.get_size_at(0, "/tmp/f000000"), 1)
        self.assertIsNone(fs.get_size_at(100, "/tmp/f000000"))


if __name__ == "__main__":
    unittest.main()
