import unittest

from solution import FileSystem


def _fs(pairs):
    fs = FileSystem()
    for path, size in pairs:
        fs.create_file(path, size)
    return fs


class Level2HiddenTests(unittest.TestCase):
    def test_segment_aware_does_not_match_prefix_sibling(self):
        fs = _fs([("/docs/a", 1), ("/docs2/b", 100)])
        self.assertEqual(fs.total_size("/docs"), 1)
        self.assertEqual(fs.list_files("/docs"), ["/docs/a"])

    def test_directory_own_name_not_counted_as_child(self):
        fs = _fs([("/docs", 50), ("/docs/a", 1)])
        self.assertEqual(fs.total_size("/docs"), 1)
        self.assertEqual(fs.list_files("/docs"), ["/docs/a"])

    def test_root_includes_file_at_directory_name(self):
        fs = _fs([("/docs", 50), ("/docs/a", 1)])
        self.assertEqual(fs.total_size("/"), 51)

    def test_deeply_nested_counted(self):
        fs = _fs([("/a/b/c/d/e.txt", 9)])
        self.assertEqual(fs.total_size("/a"), 9)
        self.assertEqual(fs.total_size("/a/b/c/d"), 9)

    def test_total_size_reflects_delete(self):
        fs = _fs([("/docs/a", 10), ("/docs/b", 20)])
        fs.delete("/docs/a")
        self.assertEqual(fs.total_size("/docs"), 20)

    def test_total_size_reflects_move_out(self):
        fs = _fs([("/docs/a", 10), ("/docs/b", 20)])
        fs.move_file("/docs/a", "/other/a")
        self.assertEqual(fs.total_size("/docs"), 20)
        self.assertEqual(fs.total_size("/other"), 10)

    def test_total_size_reflects_move_in(self):
        fs = _fs([("/tmp/x", 7)])
        fs.move_file("/tmp/x", "/docs/x")
        self.assertEqual(fs.total_size("/docs"), 7)
        self.assertEqual(fs.total_size("/tmp"), 0)

    def test_list_files_only_subtree(self):
        fs = _fs([("/a/1", 1), ("/a/2", 1), ("/b/1", 1)])
        self.assertEqual(fs.list_files("/a"), ["/a/1", "/a/2"])

    def test_list_files_empty_when_no_match(self):
        fs = _fs([("/a/1", 1)])
        self.assertEqual(fs.list_files("/z"), [])

    def test_total_size_zero_size_files(self):
        fs = _fs([("/a/x", 0), ("/a/y", 0)])
        self.assertEqual(fs.total_size("/a"), 0)
        self.assertEqual(fs.list_files("/a"), ["/a/x", "/a/y"])

    def test_root_of_empty_system_is_empty_list(self):
        self.assertEqual(FileSystem().list_files("/"), [])

    def test_performance_large_tree(self):
        # A dict-backed store makes create/delete/lookups O(1) and a single
        # aggregation O(n). A quadratic design (scanning a list per operation)
        # exceeds the per-test time budget.
        fs = FileSystem()
        n = 40000
        for i in range(n):
            fs.create_file(f"/dir{i % 100}/file{i:06d}.dat", i % 50)
        # Many point lookups (would be O(n^2) total on a list-backed store).
        for i in range(0, n, 100):
            self.assertEqual(fs.get_size(f"/dir{i % 100}/file{i:06d}.dat"), i % 50)
        self.assertEqual(fs.total_size("/"), sum(i % 50 for i in range(n)))
        self.assertEqual(len(fs.list_files("/dir0")), n // 100)


if __name__ == "__main__":
    unittest.main()
