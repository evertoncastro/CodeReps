"""Django ORM gym — books and authors.

Everything lives in this one file: the models AND the query functions. Django is
already configured by the test harness before this module is imported, against a
private in-memory SQLite database. You never write settings or migrations.

Two rules the harness depends on:

  1. every model needs `class Meta: app_label = "gym"` (already filled in below)
     — without it Django has no app for the model and reverse relations such as
     `author.books` raise FieldError;

  2. never return a QuerySet. Return lists / tuples. A QuerySet is lazy, so its
     SQL would run after the query counter stops — the tests reject it.

Each query function has a QUERY BUDGET (see the task statement). The tests count
the SQL statements you run and fail you for going over, even when the values are
correct. That is the exercise.
"""

from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=2)

    class Meta:
        app_label = "gym"


class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="books")
    published_year = models.IntegerField()
    pages = models.IntegerField()

    class Meta:
        app_label = "gym"


def seed(authors: list[dict], books: list[dict]) -> None:
    """Persist every author and book. Not query-budgeted.

    authors: [{"name": str, "country": str}]      names are unique
    books:   [{"title": str, "author": str,       "author" is a name from `authors`
               "year": int, "pages": int}]        stored in Book.published_year / pages
    """
    raise NotImplementedError


def books_with_authors() -> list[tuple[str, str]]:
    """Every book as (title, author name), sorted by title.

    Budget: 1 query.
    """
    raise NotImplementedError


def books_published_after(year: int) -> list[tuple[str, str]]:
    """Books published STRICTLY after `year`, as (title, author name),
    sorted by published year ascending, then title ascending.

    Budget: 1 query.
    """
    raise NotImplementedError


def book_titles_by_author(author_name: str) -> list[str]:
    """The titles written by `author_name`, sorted alphabetically.
    An unknown author gives an empty list.

    Budget: 1 query.
    """
    raise NotImplementedError
