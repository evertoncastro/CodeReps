# Level 3 Requirements

The bank needs analytics over accounts. Extend the **same** `Bank` class.

## New methods

### `top_spenders(k: int) -> list[str]`

Return the `account_id`s of the `k` accounts that have transferred out the most in
total (by `get_total_sent`), ordered by total sent **descending**. Ties are broken by
`account_id` **ascending** (lexicographic).

- Return at most `k` ids (fewer if there are fewer accounts).
- Return an empty list if `k <= 0`.
- Accounts that have never sent (total sent `0`) are included, ranked last.

### `total_balance() -> int`

Return the sum of the balances of all accounts. Returns `0` when there are no accounts.

### `accounts_below(threshold: int) -> list[str]`

Return the `account_id`s whose balance is **strictly less than** `threshold`, ordered
by `account_id` ascending.

## Hidden Tests Check For

- `top_spenders` orders by total sent desc, breaking ties by id ascending
- `top_spenders(k)` returns at most `k`; `k <= 0` returns `[]`; large `k` returns all
- accounts that never sent are ranked last, ordered by id
- `total_balance` is `0` with no accounts and equals the conserved sum after transfers
- `accounts_below` uses a strict `<` comparison (threshold value excluded)
- all returned lists are sorted exactly as specified
- the analytics stay correct and efficient on a large number of accounts
