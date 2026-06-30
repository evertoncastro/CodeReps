class Inventory:
    """Warehouse Inventory System.

    Implement the methods required by the current level. The SAME class evolves
    across all 4 levels: in later levels you add methods without renaming or
    breaking the existing ones.
    """

    def __init__(self) -> None:
        self.products = {}

    def add_product(self, product_id: str, name: str) -> bool:
        """Register a product with an initial stock of 0.

        Returns True if registered; False if product_id already exists
        (in that case the existing product is NOT modified).
        """
        if product_id in self.products:
            return False
        self.products[product_id] = dict(name=name, stock=0, archived=False)
        return True

    def add_stock(self, product_id: str, quantity: int):
        """Add `quantity` (>= 0) to the product's stock.

        Returns the new stock total, or None if the product does not exist.
        """
        if not product_id in self.products:
            return None
        if self._is_archived(product_id):
            return None
        self.products[product_id]["stock"] += quantity
        return self.products[product_id]["stock"]

    def get_stock(self, product_id: str):
        """Return the product's current stock, or None if it does not exist."""
        if not product_id in self.products:
            return None
        return self.products[product_id]["stock"]

    def get_product_name(self, product_id: str):
        """Return the product's name, or None if it does not exist."""
        if not product_id in self.products:
            return None
        return self.products[product_id]["name"]
    
    def remove_stock(self, product_id: str, quantity: int) -> int | None:
        if product_id not in self.products:
            return None
        product = self.products[product_id]
        if self._is_archived(product_id):
            return None
        stock = int(product["stock"])
        if quantity > stock:
            return None
        product["stock"] -= quantity
        return product["stock"]

    def archive_product(self, product_id: str) -> bool:
        if product_id not in self.products:
            return False
        product = self.products[product_id]
        if product["archived"] == True:
            return False
        product["archived"] = True
        return True

    def _is_archived(self, product_id: str) -> bool:
        if product_id not in self.products:
            return None
        product = self.products[product_id]
        archived = product["archived"]
        return archived

    def is_archived(self, product_id: str) -> bool:
        return self._is_archived(product_id)

    def restore_product(self, product_id: str) -> bool:
        is_archived = self._is_archived(product_id)
        if not is_archived:
            return False
        product = self.products[product_id]
        product["archived"] = False
        return True

    def total_stock(self) -> int:
        total = 0
        for product in self.products.values():
            stock = product["stock"]
            total += stock
        return total
         
        
