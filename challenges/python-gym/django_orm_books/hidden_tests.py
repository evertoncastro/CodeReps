"""Hidden tests. Only the method NAME reaches the candidate, so every name states
the exact contract it enforces."""

import unittest

from django.db.models import QuerySet

from gym_harness import (  # first: boots Django before solution is imported
    AUTHORS_B,
    BOOKS_B,
    GymTestCase,
    big_dataset,
)

from solution import (
    Author,
    Book,
    book_titles_by_author,
    books_published_after,
    books_with_authors,
)


class ModelShapeTests(GymTestCase):
    def test_models_declare_the_required_fields(self):
        self.assertEqual(
            {f.name for f in Author._meta.get_fields() if f.concrete},
            {"id", "name", "country"},
        )
        self.assertEqual(
            {f.name for f in Book._meta.get_fields() if f.concrete},
            {"id", "title", "author", "published_year", "pages"},
        )

    def test_book_author_fk_uses_related_name_books_and_cascade(self):
        fk = Book._meta.get_field("author")
        self.assertEqual(fk.related_model, Author)
        self.assertEqual(fk.remote_field.get_accessor_name(), "books")
        self.assertEqual(fk.remote_field.on_delete.__name__, "CASCADE")

    def test_seed_links_each_book_to_its_own_author(self):
        self.seed()
        self.assertEqual(Author.objects.get(name="Ursula Vance").books.count(), 4)
        self.assertEqual(Author.objects.get(name="Dana Okafor").books.count(), 0)
        book = Book.objects.get(title="River of Salt")
        self.assertEqual(book.author.name, "Chen Wei")
        self.assertEqual(book.published_year, 2021)
        self.assertEqual(book.pages, 850)

    def test_seed_stores_the_author_country(self):
        self.seed()
        self.assertEqual(Author.objects.get(name="Chen Wei").country, "CN")


class SecondDatasetTests(GymTestCase):
    """Answers hardcoded from the visible dataset must not survive here."""

    def setUp(self):
        super().setUp()
        self.seed(AUTHORS_B, BOOKS_B)

    def test_books_with_authors_on_a_different_dataset(self):
        self.assertEqual(
            self.counted(1, books_with_authors),
            [
                ("Anvil", "Zoe Adler"),
                ("Borrowed Light", "Zoe Adler"),
                ("Cold Harbor", "Zoe Adler"),
                ("Deep Field", "Ben Carter"),
                ("Ember Road", "Ben Carter"),
                ("Salt", "Marta Ilves"),
                ("Salt and Iron", "Marta Ilves"),
            ],
        )

    def test_books_published_after_excludes_the_boundary_year(self):
        # Three books are from exactly 2010; >= instead of > would include them.
        self.assertEqual(
            self.counted(1, books_published_after, 2010),
            [
                ("Borrowed Light", "Zoe Adler"),
                ("Deep Field", "Ben Carter"),
                ("Ember Road", "Ben Carter"),
            ],
        )

    def test_books_published_after_sorts_by_year_before_title(self):
        # Sorting by title alone would put "Anvil" first; by year it comes last.
        self.assertEqual(
            self.counted(1, books_published_after, 1999),
            [
                ("Anvil", "Zoe Adler"),
                ("Salt", "Marta Ilves"),
                ("Salt and Iron", "Marta Ilves"),
                ("Borrowed Light", "Zoe Adler"),
                ("Deep Field", "Ben Carter"),
                ("Ember Road", "Ben Carter"),
            ],
        )

    def test_book_titles_by_author_matches_the_exact_name_not_a_prefix(self):
        self.assertEqual(
            self.counted(1, book_titles_by_author, "Marta Ilves"),
            ["Salt", "Salt and Iron"],
        )


class EdgeCaseTests(GymTestCase):
    def test_book_titles_by_author_for_an_author_with_no_books_is_empty(self):
        self.seed()
        self.assertEqual(self.counted(1, book_titles_by_author, "Dana Okafor"), [])

    def test_book_titles_by_author_for_an_unknown_author_is_empty(self):
        self.seed()
        self.assertEqual(self.counted(1, book_titles_by_author, "Nobody At All"), [])

    def test_books_published_after_a_year_with_no_matches_is_empty(self):
        self.seed()
        self.assertEqual(self.counted(1, books_published_after, 2100), [])

    def test_books_published_after_a_year_below_all_returns_every_book(self):
        self.seed()
        self.assertEqual(len(self.counted(1, books_published_after, 1900)), 12)

    def test_books_with_authors_returns_tuples_of_two_strings(self):
        self.seed()
        rows = self.counted(1, books_with_authors)
        self.assertTrue(all(isinstance(r, tuple) and len(r) == 2 for r in rows))
        self.assertTrue(all(isinstance(v, str) for r in rows for v in r))

    def test_functions_return_plain_values_never_querysets(self):
        self.seed()
        for func, args in (
            (books_with_authors, ()),
            (books_published_after, (2000,)),
            (book_titles_by_author, ("Chen Wei",)),
        ):
            with self.subTest(function=func.__name__):
                self.assertNotIsInstance(func(*args), QuerySet)


class ScaleTests(GymTestCase):
    def test_no_n_plus_1_with_20_authors_and_100_books(self):
        # Reaching book.author.name row by row costs 101 queries here.
        authors, books = big_dataset(20, 5)
        self.seed(authors, books)
        rows = self.counted(1, books_with_authors)
        self.assertEqual(len(rows), 100)
        self.assertEqual(rows[0], ("Book 00-0", "Author 00"))

    def test_no_n_plus_1_when_filtering_by_year_at_scale(self):
        authors, books = big_dataset(20, 5)
        self.seed(authors, books)
        rows = self.counted(1, books_published_after, 2002)
        self.assertEqual(len(rows), 40)

    def test_no_n_plus_1_when_filtering_by_author_at_scale(self):
        authors, books = big_dataset(20, 5)
        self.seed(authors, books)
        self.assertEqual(len(self.counted(1, book_titles_by_author, "Author 07")), 5)


if __name__ == "__main__":
    unittest.main()
