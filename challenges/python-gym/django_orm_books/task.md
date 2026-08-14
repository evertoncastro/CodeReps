# Django ORM — Books and Authors

## The exercise

One file, `solution.py`, holding two models **and** three query functions.

There is no Django project here: the test harness (`gym_harness.py`, readable in the file
explorer) configures Django in memory before your code is imported, and builds one table per
model. You never write settings, migrations or a `manage.py`. The database is a private
SQLite `:memory:` instance that exists only while the tests run.

## Rules the harness enforces

1. Every model needs `class Meta: app_label = "gym"`. It is already in the starter — leave
   it there, or Django will have no app for the model and `author.books` will raise
   `FieldError`.
2. Every query function returns **plain Python** — a list of tuples, a list of strings.
   Returning a QuerySet fails immediately: it is lazy, so its SQL would run after the query
   counter has stopped.
3. Each query function has a **query budget**. The tests count the SQL statements you run
   and fail you for exceeding it, *even when every value is correct*. This is the point of
   the exercise: the naive version of the first function costs 13 queries where one is
   enough.

## The models

Field names and the `related_name` are part of the contract — the tests read them.

| Model | Fields |
|---|---|
| `Author` | `name` (CharField 100), `country` (CharField 2) |
| `Book` | `title` (CharField 200), `author` (FK → `Author`, `on_delete=CASCADE`, `related_name="books"`), `published_year` (IntegerField), `pages` (IntegerField) |

## The functions

| Function | Returns | Budget |
|---|---|---|
| `seed(authors, books)` | `None` | not counted |
| `books_with_authors()` | `[(title, author_name)]`, sorted by title | **1 query** |
| `books_published_after(year)` | `[(title, author_name)]`, year ascending then title | **1 query** |
| `book_titles_by_author(author_name)` | `[title]`, alphabetical | **1 query** |

### `seed(authors, books)`

```python
authors = [{"name": "Ursula Vance", "country": "US"}, ...]   # names are unique
books   = [{"title": "Anchor and Ash", "author": "Ursula Vance",
            "year": 2011, "pages": 280}, ...]                # "author" is a name
```

Persist all of them. `year` goes to `Book.published_year`. Every `books[i]["author"]` is a
name present in `authors`. Not query-budgeted — build it however you like.

### `books_published_after(year)`

Strictly greater than `year`: a book published exactly in `year` is excluded.

### `book_titles_by_author(author_name)`

Matches the name exactly. An author who wrote nothing, and a name that does not exist, both
give `[]`.

## Hidden tests check for

- the same functions against a second, differently shaped dataset
- the boundary year (`>` versus `>=`) and sorting by year before title
- an author with no books, and an unknown author name
- exact name matching where one name is a prefix of another
- the model fields, the foreign key's `related_name` and its `on_delete`
- the budgets again at 20 authors and 100 books, where the naive version needs 101 queries

## Suggested route

`select_related()` for the forward foreign key, `values_list()` to get tuples straight out of
the database, `filter()` with `__gt` and related lookups such as `author__name`, and
`order_by()` for every ordering the statement asks for.
