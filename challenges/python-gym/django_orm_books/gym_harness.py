"""Django bootstrap, fixtures and the shared TestCase for this exercise.

Importing this module configures Django, and that MUST happen before `solution`
is imported: model classes are built at import time and Django refuses to build
one before settings exist. To make the order impossible to get wrong, this
module imports `solution` itself — a test module only has to import this one
first.

Why the ceremony:

* INSTALLED_APPS must contain the app the models belong to, or reverse relations
  (`author.books`) silently fail with FieldError. There is no app on disk, so an
  empty module named "gym" is injected. `__path__ = []` stops Django from
  autodiscovering an apps.py/models.py out of the challenge folder, and
  `__file__` is set only because AppConfig insists every app has a filesystem
  location (a bare ModuleType raises ImproperlyConfigured).

* THE DATABASE IS PRIVATE TO THIS CHALLENGE. It is SQLite in memory, created
  inside the test subprocess and gone when it exits, so a solution can never
  reach the app's own state (challenges/progress.db) or leave anything behind
  between runs. Moving to a real server later means changing DATABASES here and
  nothing else.

* CaptureQueriesContext turns on a debug cursor by itself, so counting queries
  does not depend on DEBUG.
"""

from __future__ import annotations

import os
import sys
import types

import django
from django.conf import settings

APP_LABEL = "gym"


def _bootstrap() -> None:
    """Configure Django exactly once per process. Idempotent."""
    if settings.configured:
        return
    app = types.ModuleType(APP_LABEL)
    app.__path__ = []                          # a package with nowhere to look
    app.__file__ = os.path.abspath(__file__)   # AppConfig demands a location
    sys.modules.setdefault(APP_LABEL, app)
    settings.configure(
        DEBUG=True,
        USE_TZ=False,
        INSTALLED_APPS=[APP_LABEL],
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
        DATABASES={
            "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
        },
    )
    django.setup()


_bootstrap()

# Everything below needs a configured Django — the placement is deliberate.
import unittest  # noqa: E402
from types import GeneratorType  # noqa: E402

from django.apps import apps  # noqa: E402
from django.db import connection  # noqa: E402
from django.db.models import QuerySet  # noqa: E402
from django.test.utils import CaptureQueriesContext  # noqa: E402

import solution  # noqa: E402  — declares the models; importable only after setup


# ----- fixtures -----
# Sized so the naive/optimised gap cannot be luck. Measured on Django 6.1:
# reading book.author.name per row costs 13 queries here, select_related costs 1.
#
# Nothing sits in a helpful order: authors are inserted neither alphabetically
# nor by book count, each author's books are inserted out of alphabetical order,
# one author has no books at all, and two authors tie on book count.

AUTHORS = [
    {"name": "Bruno Kessler", "country": "DE"},
    {"name": "Dana Okafor", "country": "NG"},      # writes nothing
    {"name": "Ursula Vance", "country": "US"},
    {"name": "Chen Wei", "country": "CN"},
    {"name": "Ada Moreau", "country": "FR"},
]

BOOKS = [
    {"title": "The Silent Orbit", "author": "Ursula Vance", "year": 2001, "pages": 320},
    {"title": "Quiet Machines", "author": "Ada Moreau", "year": 1998, "pages": 210},
    {"title": "Broken Compass", "author": "Bruno Kessler", "year": 2015, "pages": 150},
    {"title": "Mountain of Glass", "author": "Chen Wei", "year": 2019, "pages": 900},
    {"title": "Anchor and Ash", "author": "Ursula Vance", "year": 2011, "pages": 280},
    {"title": "Delta Winter", "author": "Ada Moreau", "year": 2011, "pages": 190},
    {"title": "Nightfall Protocol", "author": "Bruno Kessler", "year": 2003, "pages": 160},
    {"title": "River of Salt", "author": "Chen Wei", "year": 2021, "pages": 850},
    {"title": "Echoes in Amber", "author": "Ursula Vance", "year": 2019, "pages": 300},
    {"title": "Paper Tigers", "author": "Ada Moreau", "year": 2021, "pages": 400},
    {"title": "Glass Harvest", "author": "Bruno Kessler", "year": 2019, "pages": 140},
    {"title": "Winter Signals", "author": "Ursula Vance", "year": 1998, "pages": 250},
]

# A differently shaped dataset: answers hardcoded from the visible tests die here.
# "Salt" is a prefix of "Salt and Iron", and three books share the boundary year.
AUTHORS_B = [
    {"name": "Zoe Adler", "country": "US"},
    {"name": "Marta Ilves", "country": "EE"},
    {"name": "Noor Haddad", "country": "JO"},      # writes nothing
    {"name": "Ben Carter", "country": "GB"},
]

BOOKS_B = [
    {"title": "Salt and Iron", "author": "Marta Ilves", "year": 2010, "pages": 500},
    {"title": "Salt", "author": "Marta Ilves", "year": 2010, "pages": 120},
    {"title": "Anvil", "author": "Zoe Adler", "year": 2010, "pages": 90},
    {"title": "Borrowed Light", "author": "Zoe Adler", "year": 2016, "pages": 95},
    {"title": "Cold Harbor", "author": "Zoe Adler", "year": 1999, "pages": 80},
    {"title": "Deep Field", "author": "Ben Carter", "year": 2016, "pages": 700},
    {"title": "Ember Road", "author": "Ben Carter", "year": 2020, "pages": 640},
]


def big_dataset(n_authors: int = 20, per_author: int = 5) -> tuple[list[dict], list[dict]]:
    """Large enough that an N+1 solution cannot hide: 101 queries against 1."""
    authors = [{"name": f"Author {i:02d}", "country": "XX"} for i in range(n_authors)]
    books = [
        {
            "title": f"Book {i:02d}-{j}",
            "author": f"Author {i:02d}",
            "year": 2000 + j,
            "pages": 100 + j,
        }
        for i in range(n_authors)
        for j in range(per_author)
    ]
    return authors, books


# ----- schema + wipe -----

_TABLES_READY = False


def gym_models() -> list:
    """The candidate's models, in declaration order."""
    return list(apps.get_app_config(APP_LABEL).get_models())


def ensure_tables() -> None:
    """Create one table per model, once per process."""
    global _TABLES_READY
    if _TABLES_READY:
        return
    models = gym_models()
    if not models:
        raise RuntimeError(
            "solution.py declared no models in the 'gym' app — every model needs "
            "class Meta: app_label = 'gym'"
        )
    existing = set(connection.introspection.table_names())
    with connection.schema_editor() as editor:
        for model in models:
            if model._meta.db_table not in existing:
                editor.create_model(model)
    _TABLES_READY = True


def wipe() -> None:
    """Empty every table. Reverse declaration order keeps foreign keys happy."""
    for model in reversed(gym_models()):
        model.objects.all().delete()


class GymTestCase(unittest.TestCase):
    """Bootstrapped, wiped-between-tests base for this exercise.

    Tables are created from setUp, not setUpClass: the project's test harness
    runs each test case individually (for definition order and a per-case time
    budget), which bypasses unittest's class-level fixtures. `ensure_tables` is
    guarded, so the cost after the first call is one boolean check.
    """

    def setUp(self) -> None:
        ensure_tables()
        wipe()
        self.last_queries: list[str] = []

    def seed(self, authors: list[dict] | None = None, books: list[dict] | None = None) -> None:
        """Load a dataset through the candidate's seed(). Never query-counted."""
        solution.seed(
            AUTHORS if authors is None else authors,
            BOOKS if books is None else books,
        )

    def counted(self, budget: int, func, *args, **kwargs):
        """Call `func` under a query budget and return its result.

        assertLessEqual, never assertEqual: fewer queries is never a failure, and
        an empty table legitimately costs zero.
        """
        with CaptureQueriesContext(connection) as ctx:
            result = func(*args, **kwargs)
        self.last_queries = [q["sql"] for q in ctx.captured_queries]
        name = getattr(func, "__name__", "function")
        self.assertNotIsInstance(
            result,
            QuerySet,
            f"{name}() returned a QuerySet. Return plain Python values — a lazy "
            "QuerySet runs its SQL after the counter stops, so it proves nothing.",
        )
        self.assertNotIsInstance(
            result, GeneratorType, f"{name}() returned a generator; return a list."
        )
        used = len(self.last_queries)
        self.assertLessEqual(
            used,
            budget,
            f"{name}() ran {used} SQL queries, the budget is {budget}. "
            "Queries executed:\n  " + "\n  ".join(self.last_queries),
        )
        return result
