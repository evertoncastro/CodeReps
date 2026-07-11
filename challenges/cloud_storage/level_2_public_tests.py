import unittest

from solution import FileSystem


class Level2PublicTests(unittest.TestCase):
    def setUp(self):
        self.fs = FileSystem()
        for path, size in [
            ("/docs/a.txt", 10),
            ("/docs/b.txt", 20),
            ("/docs/2024/q1.txt", 5),
            ("/images/logo.png", 100),
        ]:
            self.fs.create_file(path, size)

    def test_total_size_directory(self):
        self.assertEqual(self.fs.total_size("/docs"), 35)

    def test_total_size_root_sums_everything(self):
        self.assertEqual(self.fs.total_size("/"), 135)

    def test_total_size_nested_directory(self):
        self.assertEqual(self.fs.total_size("/docs/2024"), 5)

    def test_total_size_unknown_directory_is_zero(self):
        self.assertEqual(self.fs.total_size("/nope"), 0)

    def test_total_size_empty_system(self):
        self.assertEqual(FileSystem().total_size("/"), 0)

    def test_list_files_sorted(self):
        self.assertEqual(
            self.fs.list_files("/docs"),
            ["/docs/2024/q1.txt", "/docs/a.txt", "/docs/b.txt"],
        )

    def test_list_files_root(self):
        self.assertEqual(
            self.fs.list_files("/"),
            [
                "/docs/2024/q1.txt",
                "/docs/a.txt",
                "/docs/b.txt",
                "/images/logo.png",
            ],
        )

    def test_list_files_unknown_directory_empty(self):
        self.assertEqual(self.fs.list_files("/nope"), [])


if __name__ == "__main__":
    unittest.main()
