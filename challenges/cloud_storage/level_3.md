# Level 3 Requirements

The service now has **users**, each with a fixed storage **capacity** (in bytes).
Files can be owned by a user, and a user may only store files up to their
capacity. Extend the **same** `FileSystem` class.

Files created with the Level 1 `create_file` have **no owner** and do not count
against any user's capacity (think of them as system files). Only the new
`create_file_by` method creates user-owned files.

## New methods

### `add_user(user_id: str, capacity: int) -> bool`

Register a user with a total storage `capacity` (you may assume `capacity >= 0`)
and `0` bytes used.

- Returns `True` if the user was created.
- Returns `False` if `user_id` already exists (the existing user is not modified).

### `create_file_by(user_id: str, path: str, size: int) -> int | None`

Create a file at `path` owned by `user_id`, consuming `size` bytes of that user's
remaining capacity.

- On success, returns the user's **remaining capacity** after the file is added
  (i.e. `capacity - used`).
- Returns `None`, creating nothing, if any of these hold:
  - `user_id` does not exist,
  - a file already exists at `path`, or
  - `size` is greater than the user's remaining capacity.

A file created this way still participates in `total_size` / `list_files` exactly
like any other file. Deleting a user-owned file (via `delete`) frees that user's
capacity again. Moving a user-owned file (via `move_file`) keeps its owner and
does not change any capacity.

### `merge_users(user_a: str, user_b: str) -> int | None`

Merge `user_b` into `user_a`: `user_a` absorbs `user_b`'s capacity and used bytes,
and becomes the owner of every file previously owned by `user_b`. Afterwards
`user_b` no longer exists.

- Concretely, `user_a`'s capacity becomes `capacity_a + capacity_b` and its used
  becomes `used_a + used_b`.
- Returns `user_a`'s **remaining capacity** after the merge.
- Returns `None`, changing nothing, if `user_a == user_b`, or if either user does
  not exist.

---

## Hidden Tests Check For

- `add_user` returns `False` for a duplicate id and does not reset capacity/used.
- `create_file_by` returns the remaining capacity and decreases it by `size`.
- `create_file_by` allows a file whose size exactly equals the remaining capacity
  (remaining becomes `0`), but rejects one byte more.
- `create_file_by` returns `None` for an unknown user, a taken path, or an
  over-quota size — and creates nothing in each case.
- `delete` of a user-owned file frees the owner's capacity so more can be stored.
- `move_file` of a user-owned file keeps the owner and leaves capacity unchanged.
- A file created by a user contributes to `total_size` / `list_files`.
- `merge_users` sums both capacities and used bytes and transfers file ownership,
  so the absorbed user's files still count and freeing them frees the merged user.
- `merge_users` returns `None` when a user is missing or when `user_a == user_b`,
  changing nothing.
- After a merge, `user_b` is gone (creating a file by `user_b` returns `None`).
