import unittest

from solution import FileSystem


class Level3HiddenTests(unittest.TestCase):
    def test_duplicate_user_does_not_reset_state(self):
        fs = FileSystem()
        fs.add_user("u1", 100)
        fs.create_file_by("u1", "/a", 40)
        self.assertFalse(fs.add_user("u1", 5))
        # remaining still 60, not reset to a fresh 100 or 5
        self.assertEqual(fs.create_file_by("u1", "/b", 60), 0)

    def test_exact_capacity_allowed(self):
        fs = FileSystem()
        fs.add_user("u1", 50)
        self.assertEqual(fs.create_file_by("u1", "/a", 50), 0)

    def test_one_over_capacity_rejected(self):
        fs = FileSystem()
        fs.add_user("u1", 50)
        self.assertIsNone(fs.create_file_by("u1", "/a", 51))

    def test_capacity_accumulates_across_files(self):
        fs = FileSystem()
        fs.add_user("u1", 100)
        self.assertEqual(fs.create_file_by("u1", "/a", 30), 70)
        self.assertEqual(fs.create_file_by("u1", "/b", 30), 40)
        self.assertIsNone(fs.create_file_by("u1", "/c", 41))

    def test_create_file_by_taken_path_is_none(self):
        fs = FileSystem()
        fs.add_user("u1", 100)
        fs.create_file("/a", 5)
        self.assertIsNone(fs.create_file_by("u1", "/a", 5))
        # nothing consumed: full capacity still available
        self.assertEqual(fs.create_file_by("u1", "/b", 100), 0)

    def test_delete_unowned_file_does_not_touch_users(self):
        fs = FileSystem()
        fs.add_user("u1", 100)
        fs.create_file("/sys", 10)
        fs.delete("/sys")
        self.assertEqual(fs.create_file_by("u1", "/a", 100), 0)

    def test_move_owned_file_keeps_owner_and_capacity(self):
        fs = FileSystem()
        fs.add_user("u1", 100)
        fs.create_file_by("u1", "/a", 40)
        fs.move_file("/a", "/b")
        # capacity accounting is unchanged by the move: still 40 used, so 61
        # would not fit but 60 fills the user exactly.
        self.assertIsNone(fs.create_file_by("u1", "/c", 61))
        self.assertEqual(fs.create_file_by("u1", "/c", 60), 0)
        # ownership survived the move: deleting the moved file (still owned by
        # u1 at its new path) frees u1's capacity again.
        self.assertEqual(fs.delete("/b"), 40)
        self.assertEqual(fs.create_file_by("u1", "/d", 40), 0)

    def test_delete_after_move_frees_owner(self):
        fs = FileSystem()
        fs.add_user("u1", 100)
        fs.create_file_by("u1", "/a", 40)
        fs.move_file("/a", "/b")
        fs.delete("/b")
        self.assertEqual(fs.create_file_by("u1", "/c", 100), 0)

    def test_merge_transfers_ownership_and_freeing_works(self):
        fs = FileSystem()
        fs.add_user("u1", 100)
        fs.add_user("u2", 50)
        fs.create_file_by("u2", "/u2/b", 20)
        # merge: capacity 150, used 20 -> remaining 130
        self.assertEqual(fs.merge_users("u1", "u2"), 130)
        # deleting u2's old file now frees u1's capacity
        fs.delete("/u2/b")
        self.assertEqual(fs.create_file_by("u1", "/big", 150), 0)

    def test_merge_missing_user_returns_none(self):
        fs = FileSystem()
        fs.add_user("u1", 100)
        self.assertIsNone(fs.merge_users("u1", "ghost"))
        self.assertIsNone(fs.merge_users("ghost", "u1"))

    def test_merge_same_user_returns_none(self):
        fs = FileSystem()
        fs.add_user("u1", 100)
        self.assertIsNone(fs.merge_users("u1", "u1"))

    def test_merged_user_no_longer_exists(self):
        fs = FileSystem()
        fs.add_user("u1", 100)
        fs.add_user("u2", 50)
        fs.merge_users("u1", "u2")
        self.assertIsNone(fs.create_file_by("u2", "/x", 1))

    def test_merge_returns_none_changes_nothing(self):
        fs = FileSystem()
        fs.add_user("u1", 100)
        fs.create_file_by("u1", "/a", 40)
        self.assertIsNone(fs.merge_users("u1", "ghost"))
        # u1 unchanged: 60 remaining
        self.assertEqual(fs.create_file_by("u1", "/b", 60), 0)

    def test_performance_many_users_and_files(self):
        fs = FileSystem()
        n = 40000
        for i in range(n):
            fs.add_user(f"u{i:06d}", 1000)
        for i in range(n):
            self.assertEqual(fs.create_file_by(f"u{i:06d}", f"/u{i:06d}/f", 10), 990)
        self.assertEqual(fs.total_size("/"), 10 * n)


if __name__ == "__main__":
    unittest.main()
