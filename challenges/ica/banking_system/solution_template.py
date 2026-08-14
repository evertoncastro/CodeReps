class Bank:
    """Banking System.

    Implement the methods required by the current level. The SAME class evolves
    across all 4 levels: in later levels you add methods without renaming or
    breaking the existing ones.
    """

    def __init__(self) -> None:
        raise NotImplementedError

    # ----- Level 1 -----

    def create_account(self, account_id: str) -> bool:
        """Open an account with a starting balance of 0.

        Returns True if created; False if account_id already exists
        (the existing account is not modified).
        """
        raise NotImplementedError

    def deposit(self, account_id: str, amount: int):
        """Add `amount` (>= 0) to the account's balance.

        Returns the new balance, or None if the account does not exist.
        """
        raise NotImplementedError

    def get_balance(self, account_id: str):
        """Return the account's current balance, or None if it does not exist."""
        raise NotImplementedError
