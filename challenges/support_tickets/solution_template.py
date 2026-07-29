class TicketSystem:
    """Support Ticketing System.

    Implement the methods required by the current level. The SAME class evolves
    across all 4 levels: in later levels you add methods without renaming or
    breaking the existing ones.

    A ticket is identified by a string id and has an integer priority (a higher
    number means higher priority).
    """

    def __init__(self) -> None:
        raise NotImplementedError

    def create_ticket(self, ticket_id: str, priority: int) -> bool:
        """Create a ticket with the given `priority` (>= 0), status "open".

        Returns True if created; False if `ticket_id` already exists (in that
        case the existing ticket is NOT modified).
        """
        raise NotImplementedError

    def get_status(self, ticket_id: str):
        """Return the ticket's current status, or None if it does not exist."""
        raise NotImplementedError

    def get_priority(self, ticket_id: str):
        """Return the ticket's priority, or None if it does not exist."""
        raise NotImplementedError

    def next_ticket(self):
        """Return the id of the highest-priority ticket still "open", without
        changing anything. Ties are broken by creation order (earliest first).
        Returns None if there is no open ticket.
        """
        raise NotImplementedError
