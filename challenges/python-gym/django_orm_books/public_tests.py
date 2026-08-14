"""Visible tests. The budgets here are the real ones — nothing is a warm-up."""

import unittest

from gym_harness import GymTestCase  # first: boots Django before solution is imported

from solution import (
    Author,
    Book,
    book_titles_by_author,
    books_published_after,
    books_with_authors,
)


class PublicTests(GymTestCase):
    def test_seed_creates_every_author_and_book(self):
        self.seed()
        self.assertEqual(Author.objects.count(), 5)
        self.assertEqual(Book.objects.count(), 12)

    def test_books_with_authors_pairs_title_and_author_sorted_by_title(self):
        self.seed()
        rows = self.counted(1, books_with_authors)
        self.assertEqual(len(rows), 12)
        self.assertEqual(
            rows[:4],
            [
                ("Anchor and Ash", "Ursula Vance"),
                ("Broken Compass", "Bruno Kessler"),
                ("Delta Winter", "Ada Moreau"),
                ("Echoes in Amber", "Ursula Vance"),
            ],
        )
        self.assertEqual(rows[-1], ("Winter Signals", "Ursula Vance"))

    def test_books_with_authors_uses_at_most_1_query(self):
        # Reading book.author.name row by row costs 13 queries on this dataset.
        self.seed()
        self.counted(1, books_with_authors)

    def test_books_published_after_filters_then_sorts_by_year_and_title(self):
        self.seed()
        rows = self.counted(1, books_published_after, 2010)
        self.assertEqual(len(rows), 8)
        self.assertEqual(
            rows[:3],
            [
                ("Anchor and Ash", "Ursula Vance"),
                ("Delta Winter", "Ada Moreau"),
                ("Broken Compass", "Bruno Kessler"),
            ],
        )

    def test_book_titles_by_author_returns_that_authors_titles_alphabetically(self):
        self.seed()
        self.assertEqual(
            self.counted(1, book_titles_by_author, "Ursula Vance"),
            ["Anchor and Ash", "Echoes in Amber", "The Silent Orbit", "Winter Signals"],
        )

    def test_every_function_works_on_an_empty_database(self):
        self.assertEqual(self.counted(1, books_with_authors), [])
        self.assertEqual(self.counted(1, books_published_after, 2000), [])
        self.assertEqual(self.counted(1, book_titles_by_author, "Ursula Vance"), [])


if __name__ == "__main__":
    unittest.main()
