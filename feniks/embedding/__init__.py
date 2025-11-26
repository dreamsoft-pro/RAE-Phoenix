"""Feniks embedding module - handles dense and sparse embeddings."""

from .embed import get_embedding_model, create_dense_embeddings, build_tfidf

__all__ = ["get_embedding_model", "create_dense_embeddings", "build_tfidf"]
