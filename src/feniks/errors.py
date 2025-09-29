# src/feniks/errors.py
class FeniksError(Exception):
    """Root exception for Feniks."""

class ConfigError(FeniksError):
    pass

class ParseError(FeniksError):
    pass

class ChunkError(FeniksError):
    pass

class VectorStoreError(FeniksError):
    pass
