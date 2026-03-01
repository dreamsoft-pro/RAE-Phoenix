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
from pathlib import Path
from typing import Any, List, Tuple, Optional, cast

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from feniks.core.models.types import Chunk
from feniks.infra.logging import get_logger

try:
    import onnxruntime as ort
    from tokenizers import Tokenizer
except ImportError:
    ort = None
    Tokenizer = None

log = get_logger("adapters.llm.embedding")

class NativeEmbeddingProvider:
    """Embedding provider using local ONNX models (Parity with RAE Core)."""

    def __init__(
        self,
        model_path: str | Path,
        tokenizer_path: str | Path,
        model_name: str = "all-MiniLM-L6-v2",
        max_length: int = 512,
        normalize: bool = True,
        use_gpu: bool = False,
    ):
        if ort is None or Tokenizer is None:
            raise ImportError(
                "onnxruntime and tokenizers are required for native embeddings."
            )

        self.model_path = str(model_path)
        self.tokenizer_path = str(tokenizer_path)
        self.model_name = model_name
        self.max_length = max_length
        self.normalize = normalize

        # Load Tokenizer
        self.tokenizer = Tokenizer.from_file(self.tokenizer_path)
        self.tokenizer.enable_truncation(max_length=max_length)
        self.tokenizer.enable_padding()

        # Load ONNX Model
        providers = ["CPUExecutionProvider"]
        if use_gpu and "CUDAExecutionProvider" in ort.get_available_providers():
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]

        log.info(f"Initializing ONNX session for {model_name} with providers: {providers}")
        self.session = ort.InferenceSession(self.model_path, providers=providers)
        
        # Determine dimension
        dummy_ids = np.array([[1]], dtype=np.int64)
        dummy_mask = np.array([[1]], dtype=np.int64)
        inputs = {"input_ids": dummy_ids, "attention_mask": dummy_mask}
        
        input_names = [i.name for i in self.session.get_inputs()]
        if "token_type_ids" in input_names:
            inputs["token_type_ids"] = np.array([[0]], dtype=np.int64)

        outputs = self.session.run(None, inputs)
        self._dimension = outputs[0].shape[-1]
        log.info(f"Native model {model_name} ready. Dimension: {self._dimension}")

    def _mean_pooling(self, last_hidden_state: np.ndarray, attention_mask: np.ndarray) -> np.ndarray:
        mask_expanded = np.expand_dims(attention_mask, axis=-1).astype(last_hidden_state.dtype)
        sum_embeddings = np.sum(last_hidden_state * mask_expanded, axis=1)
        sum_mask = np.sum(mask_expanded, axis=1)
        sum_mask = np.clip(sum_mask, a_min=1e-9, a_max=None)
        return cast(np.ndarray, sum_embeddings / sum_mask)

    def _normalize_l2(self, vectors: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return cast(np.ndarray, vectors / np.clip(norms, a_min=1e-9, a_max=None))

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        # Preprocessing for Nomic if needed (omitted for MiniLM simplicity)
        encoded = self.tokenizer.encode_batch(texts)
        input_ids = np.array([e.ids for e in encoded], dtype=np.int64)
        attention_mask = np.array([e.attention_mask for e in encoded], dtype=np.int64)

        inputs = {"input_ids": input_ids, "attention_mask": attention_mask}
        input_names = [i.name for i in self.session.get_inputs()]
        if "token_type_ids" in input_names:
            inputs["token_type_ids"] = np.array([e.type_ids for e in encoded], dtype=np.int64)

        outputs = self.session.run(None, inputs)
        embeddings = self._mean_pooling(outputs[0], attention_mask)
        if self.normalize:
            embeddings = self._normalize_l2(embeddings)
        return embeddings

def build_tfidf(chunks: List[Chunk]) -> Tuple[TfidfVectorizer, Any]:
    corpus = [c.text for c in chunks]
    vec = TfidfVectorizer(
        token_pattern=r"[A-Za-z0-9_#\-$]{2,}",
        ngram_range=(1, 2),
        min_df=int(os.getenv("FENIKS_TEST_MIN_DF", 2)),
        max_features=50000,
    )
    matrix_x = vec.fit_transform(corpus)
    return vec, matrix_x

def get_embedding_model(name: str = "all-MiniLM-L6-v2") -> Any:
    """
    Factory for embedding models.
    Attempts to find local ONNX models before falling back.
    """
    # Search paths for models
    possible_paths = [
        Path("models"),
        Path("../RAE-Suite/packages/rae-core/models"),
        Path("/home/grzegorz-lesniowski/cloud/RAE-Suite/packages/rae-core/models"),
    ]
    
    for base_path in possible_paths:
        model_dir = base_path / name
        onnx_path = model_dir / "model.onnx"
        tokenizer_path = model_dir / "tokenizer.json"
        
        if onnx_path.exists() and tokenizer_path.exists():
            log.info(f"Found local ONNX model at {onnx_path}")
            return NativeEmbeddingProvider(
                model_path=onnx_path,
                tokenizer_path=tokenizer_path,
                model_name=name
            )
            
    log.warning(f"Local ONNX model {name} not found. Falling back to zero-vectors.")
    return None

def create_dense_embeddings(model: Any, chunks: List[Chunk]) -> np.ndarray:
    if model is None:
        return np.zeros((len(chunks), 384))
    
    texts = [c.text[:5000] for c in chunks]
    if isinstance(model, NativeEmbeddingProvider):
        return model.embed_batch(texts)
    
    return np.zeros((len(chunks), 384))
