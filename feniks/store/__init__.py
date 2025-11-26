"""Feniks store module - handles Qdrant and other storage backends."""

from .qdrant import ensure_collection, upsert_points

__all__ = ["ensure_collection", "upsert_points"]
