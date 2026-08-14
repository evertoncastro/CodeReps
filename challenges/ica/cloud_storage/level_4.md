# Level 4 Requirements

Some files are temporary: they exist only for a limited lifetime and then expire.
Extend the **same** `FileSystem` class. Times (`timestamp`) are integer values in
arbitrary units.

A file created with a **time-to-live** (`ttl`) at time `t` is **alive** at any
time `q` with `t <= q < t + ttl` — i.e. it exists from its creation timestamp
(inclusive) until `t + ttl` (exclusive), after which it has expired.

Files created earlier with `create_file` / `create_file_by` have **no expiration**
and are alive at every timestamp. The Level 1–3 methods (`get_size`, `delete`,
`total_size`, `list_files`, ...) are **time-agnostic**: they operate on the full
storage regardless of any file's `ttl`. Only the new `*_at` methods below take a
timestamp into account.

## New methods

### `create_file_at(timestamp: int, path: str, size: int, ttl: int) -> bool`

Create a file at `path` with the given `size` that is alive during
`[timestamp, timestamp + ttl)` (you may assume `size >= 0` and `ttl >= 1`).

- Returns `True` if the file was created.
- Returns `False` if a file already exists at `path` (regardless of whether that
  existing file is currently alive or already expired) — nothing is modified.

### `get_size_at(timestamp: int, path: str) -> int | None`

Return the size of the file at `path` **if it is alive at `timestamp`**, else
`None`.

- A file with no expiration is alive at every timestamp.
- A file with a `ttl` is alive only within its `[created, created + ttl)` window;
  outside that window this returns `None` even though the path is still occupied.

### `total_size_at(timestamp: int, directory: str) -> int`

Return the sum of the sizes of all files under `directory` (same membership rule
as Level 2) that are **alive at `timestamp`**.

- Files that have expired or are not yet alive at `timestamp` are excluded.
- Non-expiring files are always included.
- `total_size_at(timestamp, "/")` totals every alive file at that time.

---

## Hidden Tests Check For

- A file is alive at its creation timestamp and up to (but not including)
  `created + ttl`; `get_size_at` returns `None` at and after `created + ttl`, and
  before `created`.
- `create_file_at` returns `False` for an already-occupied path, including when
  the occupying file has already expired (the path stays reserved).
- `get_size_at` returns the size for non-expiring files (from `create_file` /
  `create_file_by`) at any timestamp.
- `total_size_at` includes only files alive at the given timestamp, mixing
  expiring and non-expiring files under the directory.
- `total_size_at` respects the same segment-aware directory membership as Level 2.
- Boundary timestamps (`created`, `created + ttl - 1`, `created + ttl`) are handled
  exactly.
- `total_size_at("/", ...)` at a time when all temporary files have expired equals
  the total of only the permanent files.
