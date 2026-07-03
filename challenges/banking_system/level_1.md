# Banking System

## Domain Overview

You are building the core of an in-memory banking system. It tracks accounts and
their balances, and over the next levels will grow to support transfers, spending
analytics, and scheduled payments. Everything is implemented in a single class,
`Bank`, in `solution.py`. All amounts are non-negative integers.

---

## Level 1 Requirements

Implement the `Bank` class with the following methods:

### `create_account(account_id: str) -> bool`

Open a new account identified by `account_id`, with a starting balance of `0`.

- Returns `True` if the account was created.
- Returns `False` if an account with that `account_id` already exists. In that case
  the existing account must remain unchanged.

### `deposit(account_id: str, amount: int) -> int | None`

Add `amount` (you may assume `amount >= 0`) to the account's balance.

- Returns the **new** balance after the deposit.
- Returns `None` if the account does not exist.

### `get_balance(account_id: str) -> int | None`

- Returns the account's current balance.
- Returns `None` if the account does not exist.

---

## Public Tests

The visible tests cover, among others:

- Creating an account returns `True` and starts at balance `0`.
- Creating a duplicate `account_id` returns `False` and changes nothing.
- `deposit` increases the balance and returns the new total.
- Multiple deposits accumulate.
- `deposit` / `get_balance` on an unknown account return `None`.

## Hidden Tests Check For

- duplicate account creation does not reset the existing balance
- `deposit` returns the new balance, not the previous one
- depositing zero leaves the balance unchanged
- balances of different accounts stay independent
- unknown-account lookups return `None` (never `0`, never an exception)
- many sequential deposits accumulate correctly
- large amounts
- account ids are treated as distinct / case-sensitive
