class FileSystem:
    """Cloud File Storage.

    Implement the methods required by the current level. The SAME class evolves
    across all 4 levels: in later levels you add methods without renaming or
    breaking the existing ones.

    Files are identified by an absolute path string such as "/docs/report.txt".
    """

    def __init__(self) -> None:
        raise NotImplementedError

    def create_file(self, path: str, size: int) -> bool:
        """Create a file at `path` with the given `size` (>= 0).

        Returns True if created; False if a file already exists at `path`
        (in that case the existing file is NOT modified).
        """
        raise NotImplementedError

    def get_size(self, path: str):
        """Return the size of the file at `path`, or None if none exists."""
        raise NotImplementedError

    def delete(self, path: str):
        """Delete the file at `path`.

        Returns the deleted file's size, or None if no file exists at `path`.
        """
        raise NotImplementedError

    def move_file(self, source: str, dest: str) -> bool:
        """Move the file at `source` to `dest`, keeping its size.

        Returns True on success. Returns False (changing nothing) if there is no
        file at `source`, a file already exists at `dest`, or `source == dest`.
        """
        raise NotImplementedError
