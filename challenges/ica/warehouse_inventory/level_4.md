# Level 4 Requirements

The warehouse needs point-in-time snapshots so it can roll back after mistakes.
Extend the **same** `Inventory` class.

A snapshot captures the **entire** state of the inventory at the moment it is
taken: which products exist, and for each product its name, stock, and archived
flag.

## New methods

### `snapshot() -> int`

Capture the current full state and return a snapshot id. Ids are assigned in
increasing order starting at `1` (the first snapshot is `1`, the next `2`, ...).

### `restore(snapshot_id: int) -> bool`

Restore the inventory to exactly the state captured by `snapshot_id`:

- Every product's name, stock, and archived flag returns to the snapshotted value.
- Products that were created **after** the snapshot are removed.
- Returns `True` on success.
- Returns `False` if `snapshot_id` was never issued.

A snapshot may be restored more than once. Taking or restoring snapshots does not
invalidate previously issued snapshot ids. Restoring does **not** change the next
snapshot id that will be issued.

## Hidden Tests Check For

- snapshot ids start at 1 and increase by 1 each call
- restore reverts stock changes made after the snapshot
- restore removes products created after the snapshot
- restore reverts archived/restored state changes
- restore with an unknown id returns `False` and changes nothing
- a snapshot can be restored multiple times
- restoring an older snapshot after a newer one works
- snapshots are independent of each other (restoring one does not corrupt others)
- changes after a restore behave normally (e.g. add/remove stock still works)
- restore returns the product set to exactly the snapshotted set
