# Copyright 2025 Grzegorz Leśniowski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
from typing import Any, List, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer

from feniks.core.models.types import Chunk


def build_tfidf(chunks: List[Chunk]) -> Tuple[TfidfVectorizer, Any]:
    """
    Builds a TF-IDF vectorizer and transforms the chunk texts.
    """
    corpus = [c.text for c in chunks]
    vec = TfidfVectorizer(
        token_pattern=r"[A-Za-z0-9_#\-$]{2,}",
        ngram_range=(1, 2),
        min_df=int(os.getenv("FENIKS_TEST_MIN_DF", 2)),
        max_features=50000,
    )
    matrix_x = vec.fit_transform(corpus)  # csr_matrix
    return vec, matrix_x


def get_embedding_model(name: str) -> SentenceTransformer:
    """
    Loads and returns a SentenceTransformer model.
    """
    return SentenceTransformer(name)


def create_dense_embeddings(model: SentenceTransformer, chunks: List[Chunk]) -> np.ndarray:
    """
    Creates dense embeddings for a list of chunks.
    """
    texts = [c.text[:5000] for c in chunks]  # Protect memory
    # normalize_embeddings=True makes embeddings cosine-comparable
    embs = model.encode(texts, normalize_embeddings=True, batch_size=64, show_progress_bar=True)
    return np.array(embs)
