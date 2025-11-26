"""
Feniks custom exceptions for domain-level error handling.
"""


class FeniksError(Exception):
    """Base exception for all Feniks errors."""
    pass


class FeniksConfigError(FeniksError):
    """Raised when there's an issue with Feniks configuration."""
    pass


class FeniksIngestError(FeniksError):
    """Raised when there's an issue during data ingestion."""
    pass


class FeniksStoreError(FeniksError):
    """Raised when there's an issue with the storage backend (e.g., Qdrant)."""
    pass


class FeniksPluginError(FeniksError):
    """Raised when there's an issue with a language plugin."""
    pass
