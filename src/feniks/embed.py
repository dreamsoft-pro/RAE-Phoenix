# src/feniks/
from __future__ import annotations
from typing import List, Tuple, Dict, Any

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer

from feniks.types import Chunk

def build_tfidf(chunks: List[Chunk]) -> Tuple[TfidfVectorizer, Any]:
    """
    Zbuduj TF-IDF na tekstach chunków (sparse). Zwraca (vectorizer, matrix).
    """
    corpus = [c.text for c in chunks]
    vec = TfidfVectorizer(
        token_pattern=r"[A-Za-z0-9_#\-$]{2,}",
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
        sublinear_tf=True,
        norm="l2"
    )
    mat = vec.fit_transform(corpus)  # scipy.sparse
    return vec, mat

def get_embedding_model(name: str) -> SentenceTransformer:
    """
    Załaduj model SentenceTransformer po nazwie z configu.
    """
    return SentenceTransformer(name)

def create_dense_embeddings(model: SentenceTransformer, chunks: List[Chunk], max_chars: int = 5000, batch_size: int = 64) -> np.ndarray:
    """
    Dense embeddingi z normalizacją (cosine). Batch + limit znaków na dokument.
    """
    texts = [c.text[:max_chars] for c in chunks]
    embs = model.encode(
        texts,
        normalize_embeddings=True,
        batch_size=batch_size,
        show_progress_bar=False
    )
    return np.asarray(embs, dtype=np.float32)
