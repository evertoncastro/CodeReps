# Warehouse Inventory System

## Domain Overview

You are building the core of a warehouse inventory system. The system keeps track
of products and how many units of each product are currently in stock. Over the
next levels it will grow to support stock movements, validation, querying, and
historical analytics — but for now it only needs to handle basic registration and
stock additions.

You implement everything in a single class, `Inventory`, in `solution.py`.

---

## Level 1 Requirements

Implement the `Inventory` class with the following methods:

### `add_product(product_id: str, name: str) -> bool`

Register a new product identified by `product_id`, with the given `name` and an
initial stock of `0`.

- Returns `True` if the product was registered.
- Returns `False` if a product with that `product_id` already exists. In that case
  the existing product (its name and stock) must remain unchanged.

### `add_stock(product_id: str, quantity: int) -> int | None`

Add `quantity` units to the product's stock. You may assume `quantity >= 0` at this
level.

- Returns the **new** stock total after the addition.
- Returns `None` if the product does not exist.

### `get_stock(product_id: str) -> int | None`

- Returns the product's current stock.
- Returns `None` if the product does not exist.

### `get_product_name(product_id: str) -> str | None`

- Returns the product's name.
- Returns `None` if the product does not exist.

---

## Public Tests

The visible tests cover, among others:

- Registering a product returns `True`, starts at stock `0`, and stores the name.
- Registering a duplicate `product_id` returns `False` and does not change anything.
- `add_stock` increments the stock and returns the new total.
- Multiple `add_stock` calls accumulate.
- `add_stock` on an unknown product returns `None`.
- `get_stock` / `get_product_name` on an unknown product return `None`.

## Hidden Tests Check For

- duplicate product registration does not reset the existing stock or name
- `add_stock` returns the new total, not the previous one
- adding zero units leaves the stock unchanged
- stock of different products stays independent
- unknown product lookups return `None` (never `0`, never an exception)
- many sequential stock additions accumulate correctly
- large quantities
- product ids are treated as distinct/case-sensitive
