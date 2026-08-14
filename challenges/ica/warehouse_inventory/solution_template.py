class Inventory:
    """Warehouse Inventory System.

    Implement the methods required by the current level. The SAME class evolves
    across all 4 levels: in later levels you add methods without renaming or
    breaking the existing ones.
    """

    def __init__(self) -> None:
        raise NotImplementedError

    def add_product(self, product_id: str, name: str) -> bool:
        """Register a product with an initial stock of 0.

        Returns True if registered; False if product_id already exists
        (in that case the existing product is NOT modified).
        """
        raise NotImplementedError

    def add_stock(self, product_id: str, quantity: int):
        """Add `quantity` (>= 0) to the product's stock.

        Returns the new stock total, or None if the product does not exist.
        """
        raise NotImplementedError

    def get_stock(self, product_id: str):
        """Return the product's current stock, or None if it does not exist."""
        raise NotImplementedError

    def get_product_name(self, product_id: str):
        """Return the product's name, or None if it does not exist."""
        raise NotImplementedError
