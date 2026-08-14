import unittest

from solution import FileSystem


class Level3PublicTests(unittest.TestCase):
    def test_add_user_returns_true(self):
        fs = FileSystem()
        self.assertTrue(fs.add_user("u1", 100))

    def test_add_duplicate_user_returns_false(self):
        fs = FileSystem()
        fs.add_user("u1", 100)
        self.assertFalse(fs.add_user("u1", 999))

    def test_create_file_by_returns_remaining(self):
        fs = FileSystem()
        fs.add_user("u1", 100)
        self.assertEqual(fs.create_file_by("u1", "/u1/a", 30), 70)

    def test_create_file_by_unknown_user_is_none(self):
        fs = FileSystem()
        self.assertIsNone(fs.create_file_by("ghost", "/x", 1))

    def test_create_file_by_over_quota_is_none(self):
        fs = FileSystem()
        fs.add_user("u1", 100)
        self.assertIsNone(fs.create_file_by("u1", "/u1/big", 101))
        self.assertIsNone(fs.get_size("/u1/big"))

    def test_owned_file_counts_in_total_size(self):
        fs = FileSystem()
        fs.add_user("u1", 100)
        fs.create_file_by("u1", "/u1/a", 30)
        self.assertEqual(fs.total_size("/u1"), 30)

    def test_delete_frees_capacity(self):
        fs = FileSystem()
        fs.add_user("u1", 100)
        fs.create_file_by("u1", "/u1/a", 80)
        fs.delete("/u1/a")
        self.assertEqual(fs.create_file_by("u1", "/u1/b", 100), 0)

    def test_merge_users_sums_capacity(self):
        fs = FileSystem()
        fs.add_user("u1", 100)
        fs.add_user("u2", 50)
        fs.create_file_by("u1", "/u1/a", 40)
        fs.create_file_by("u2", "/u2/b", 20)
        # capacity 150, used 60 -> remaining 90
        self.assertEqual(fs.merge_users("u1", "u2"), 90)


if __name__ == "__main__":
    unittest.main()
