# Level 2 Requirements

Money now moves between accounts. Extend the **same** `Bank` class — do not rename or
break the Level 1 methods.

## New methods

### `transfer(from_id: str, to_id: str, amount: int) -> bool`

Move `amount` (you may assume `amount >= 0`) from `from_id` to `to_id`.

- Returns `True` if the transfer happened.
- Returns `False` (and changes nothing) if:
  - either account does not exist,
  - `from_id == to_id` (self-transfer), or
  - `amount` is greater than the sender's current balance (insufficient funds).

On a successful transfer the sender's balance decreases, the receiver's increases,
and the sender's **cumulative amount sent** increases by `amount`.

### `get_total_sent(account_id: str) -> int | None`

- Returns the total amount this account has successfully transferred out over its
  lifetime (a fresh account has `0`).
- Returns `None` if the account does not exist.

## Hidden Tests Check For

- transfers to/from an unknown account are rejected and change nothing
- self-transfers are rejected
- transferring more than the balance is rejected and leaves both balances unchanged
- transferring the full balance is allowed and brings the sender to 0
- balances move by exactly `amount`; funds are conserved
- `get_total_sent` accumulates only successful transfers (not rejected ones)
- `get_total_sent` is `0` for a fresh account and `None` for an unknown one
- a receiver's `get_total_sent` is unaffected by incoming transfers
