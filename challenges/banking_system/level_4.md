# Level 4 Requirements

The bank now supports **scheduled transfers** that run later. Extend the **same**
`Bank` class. Times (`at`, `now`) are integer timestamps in arbitrary units.

## New methods

### `schedule_transfer(from_id: str, to_id: str, amount: int, at: int) -> str | None`

Schedule a transfer of `amount` from `from_id` to `to_id` to run at time `at`. This
does **not** move any money now.

- Returns a new payment id, assigned in creation order: `"t1"`, `"t2"`, `"t3"`, ...
- Returns `None` if either account does not exist at scheduling time (and no id is
  consumed).

### `cancel_transfer(payment_id: str) -> bool`

Cancel a scheduled transfer that has not yet run.

- Returns `True` if it was pending and is now cancelled.
- Returns `False` if the id is unknown or the transfer is no longer pending
  (already processed, failed, or cancelled).

### `process_transfers(now: int) -> list[str]`

Run every pending scheduled transfer whose `at` is **less than or equal to** `now`,
in order of `at` ascending (ties broken by creation order). Each one is attempted
using the same rules as `transfer` (both accounts still exist, not a self-transfer,
sufficient funds **at the moment it runs**):

- If it succeeds, the funds move (and it counts toward the sender's total sent, so it
  affects `top_spenders`); it is marked processed.
- If it fails those rules, it is marked failed (and never runs again).

Return the list of payment ids that **executed successfully**, in processing order.
Transfers scheduled for a later time remain pending for a future call.

## Hidden Tests Check For

- ids increment in creation order; `schedule_transfer` on an unknown account returns
  `None` and does not consume an id
- only transfers with `at <= now` run; later ones stay pending
- due transfers run in `at` order, ties by creation order
- a transfer that lacks funds when it runs fails (not in the result) while others still run
- earlier processed transfers can leave a later one with insufficient funds (fails)
- cancelling a pending transfer stops it from running; cancel returns `False` for
  unknown/already-processed/already-cancelled ids
- self-transfers scheduled then processed fail
- processing is not repeated: an already-processed transfer never runs again
- successfully processed transfers count toward `get_total_sent` / `top_spenders`
