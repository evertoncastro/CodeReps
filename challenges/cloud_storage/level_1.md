# Cloud File Storage

## Domain Overview

You are building the core of an in-memory cloud file storage service. The system
stores files, each identified by an absolute **path** string such as
`/docs/report.txt`, and tracks the size (in bytes) of each file. Over the next
levels it will grow to support directory-level aggregation, per-user storage
quotas, and time-based file expiration — but for now it only needs to handle
basic file operations.

You implement everything in a single class, `FileSystem`, in `solution.py`.
All sizes are non-negative integers. A path is any non-empty string; you do not
need to validate its shape.

---

## Level 1 Requirements

Implement the `FileSystem` class with the following methods:

### `create_file(path: str, size: int) -> bool`

Create a file at `path` with the given `size` (you may assume `size >= 0`).

- Returns `True` if the file was created.
- Returns `False` if a file already exists at `path`. In that case the existing
  file is **not** modified.

### `get_size(path: str) -> int | None`

Return the size of the file at `path`, or `None` if no file exists there.

### `delete(path: str) -> int | None`

Delete the file at `path`.

- Returns the deleted file's **size**.
- Returns `None` if no file exists at `path` (nothing is deleted).

### `move_file(source: str, dest: str) -> bool`

Move the file at `source` to `dest`, keeping its size.

- Returns `True` on success. After a successful move there is a file at `dest`
  (with the original size) and nothing at `source`.
- Returns `False`, changing nothing, if any of these hold:
  - there is no file at `source`,
  - a file already exists at `dest`, or
  - `source == dest`.

---

## Hidden Tests Check For

- Creating a file returns `True`; a duplicate `create_file` at the same path
  returns `False` and leaves the original size untouched.
- `get_size` returns `None` for an unknown path and the exact size for a known one.
- `delete` returns the size and removes the file; a second `delete` of the same
  path returns `None`.
- Deleting one file does not affect other files.
- `move_file` relocates the size to `dest` and clears `source`.
- `move_file` fails when `source` is missing, when `dest` already exists, or when
  `source == dest`, and in every failure case leaves both paths unchanged.
- Zero-size files behave like any other file.
