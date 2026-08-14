# Level 2 Requirements

The warehouse now needs to remove stock and to take products out of circulation
without deleting them. Extend the **same** `Inventory` class — do not rename or
break the Level 1 methods.

## New methods

### `remove_stock(product_id: str, quantity: int) -> int | None`

Remove `quantity` units from the product's stock. You may assume `quantity >= 0`.

- Returns the **new** stock total after removal.
- Returns `None` if the product does not exist.
- Returns `None` if the product is archived (see below).
- Returns `None` if `quantity` is greater than the current stock (the stock must
  never go negative). In that case the stock is left unchanged.

### `archive_product(product_id: str) -> bool`

Mark a product as archived (out of circulation). Its name and stock are kept.

- Returns `True` if the product was archived.
- Returns `False` if the product does not exist or is already archived.

### `restore_product(product_id: str) -> bool`

Bring an archived product back into circulation.

- Returns `True` if the product was restored.
- Returns `False` if the product does not exist or is not archived.

### `is_archived(product_id: str) -> bool | None`

- Returns `True`/`False` for the product's archived state.
- Returns `None` if the product does not exist.

## Changes to existing behavior

While a product is archived, stock changes are rejected:

- `add_stock` on an archived product returns `None` and leaves the stock unchanged.
- `remove_stock` on an archived product returns `None`.

A newly created product (Level 1) is **not** archived.

## Hidden Tests Check For

- removing more than the available stock is rejected and leaves stock unchanged
- removing exactly the available stock brings it to 0
- remove/add on unknown products return `None` and do not create products
- archiving an already-archived product returns `False`
- restoring a non-archived (or unknown) product returns `False`
- archived products reject both `add_stock` and `remove_stock`
- restoring re-enables stock changes
- `is_archived` returns `None` for unknown products, `False` for fresh products
- archive/restore do not change the product's name or stock
