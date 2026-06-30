# Level 3 Requirements

Operations teams need to query the inventory. Extend the **same** `Inventory`
class. All query methods below consider **every** product, whether archived or
not (archived products still physically hold stock).

## New methods

### `total_stock() -> int`

Return the sum of `stock` across all products. Returns `0` when there are no
products.

### `top_products(k: int) -> list[str]`

Return the `product_id`s of the `k` products with the highest stock, ordered by
stock **descending**. Ties are broken by `product_id` **ascending** (lexicographic).

- Return at most `k` ids (fewer if there are fewer products).
- Return an empty list if `k <= 0`.

### `low_stock_products(threshold: int) -> list[str]`

Return the `product_id`s whose stock is **strictly less than** `threshold`,
ordered by `product_id` ascending.

### `find_products_by_name_prefix(prefix: str) -> list[str]`

Return the `product_id`s whose **name** starts with `prefix`, ordered by
`product_id` ascending. An empty prefix matches all products.

## Hidden Tests Check For

- `total_stock` over an empty inventory is `0` and includes archived products
- `top_products` orders by stock desc, breaking ties by id ascending
- `top_products(k)` returns at most `k` ids; `k <= 0` returns `[]`; large `k`
  returns all products
- `low_stock_products` uses a strict `<` comparison (threshold value excluded)
- `find_products_by_name_prefix` matches by name (not id) and is order-stable
- empty prefix returns all product ids sorted ascending
- query methods include archived products
- all returned lists are sorted exactly as specified
