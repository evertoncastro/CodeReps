# Level 2 Requirements

Paths are hierarchical: the `/` characters split a path into directory segments.
Operations teams now need to reason about **directories** — collections of files
that live under a common path prefix. Extend the **same** `FileSystem` class — do
not rename or break the Level 1 methods.

## Directory membership

A `directory` is a path such as `/docs` or `/docs/2024`. The special directory
`/` is the **root** and contains every file. A file is considered to be **under**
a directory `directory` when:

- `directory` is `/` (root contains all files), **or**
- the file's path starts with `directory + "/"`.

Matching is on whole segments, so `/docs` contains `/docs/a.txt` and
`/docs/2024/q1.txt`, but **not** `/docs2/a.txt` (different segment) and **not** a
file whose path is exactly `/docs` (that is the directory's own name, not a file
under it). You may assume `directory` never has a trailing slash (except root
`/`).

## New methods

### `total_size(directory: str) -> int`

Return the sum of the sizes of all files under `directory` (at any depth).

- Returns `0` when no files are under `directory`.
- `total_size("/")` returns the sum of the sizes of all files in the system.

### `list_files(directory: str) -> list[str]`

Return the paths of all files under `directory` (at any depth), sorted in
ascending lexicographic order.

- Returns an empty list when no files are under `directory`.
- `list_files("/")` returns every file path, sorted.

---

## Hidden Tests Check For

- `total_size` sums files at multiple nesting depths under the directory.
- `total_size("/")` totals every file; an empty system totals `0`.
- Segment-aware matching: `/docs` does **not** include `/docs2/...` or a file
  named exactly `/docs`.
- A directory with no files returns `0` / `[]`.
- `list_files` returns paths sorted lexicographically, restricted to the subtree.
- Aggregation reflects prior `create_file`, `delete`, and `move_file` operations
  (e.g. moving a file out of a directory removes it from that directory's total).
- Root queries include deeply nested files.
