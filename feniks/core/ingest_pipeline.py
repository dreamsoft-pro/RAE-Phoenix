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
"""
Feniks ingestion pipeline - orchestrates the process of loading code chunks into Qdrant.
"""
from pathlib import Path
from typing import List, Optional

from qdrant_client import QdrantClient

from feniks.adapters.ingest.filters import ChunkFilter, create_default_filter
from feniks.adapters.ingest.jsonl_loader import load_jsonl
from feniks.config.settings import settings
from feniks.core.policies.cost import get_cost_controller
from feniks.embedding import build_tfidf, create_dense_embeddings, get_embedding_model
from feniks.exceptions import FeniksIngestError, FeniksStoreError
from feniks.infra.logging import get_logger
from feniks.infra.metrics import get_metrics_collector
from feniks.store import ensure_collection, upsert_points

log = get_logger("core.ingest")


class IngestPipeline:
    """
    Orchestrates the ingestion pipeline: JSONL → filtering → embeddings → Qdrant.
    """

    def __init__(
        self,
        qdrant_host: Optional[str] = None,
        qdrant_port: Optional[int] = None,
        embedding_model_name: Optional[str] = None,
    ):
        """
        Initialize the ingestion pipeline.

        Args:
            qdrant_host: Qdrant host (defaults to settings)
            qdrant_port: Qdrant port (defaults to settings)
            embedding_model_name: Embedding model name (defaults to settings)
        """
        self.qdrant_host = qdrant_host or settings.qdrant_host
        self.qdrant_port = qdrant_port or settings.qdrant_port
        self.embedding_model_name = embedding_model_name or settings.embedding_model

        log.info(
            f"IngestPipeline initialized: Qdrant={self.qdrant_host}:{self.qdrant_port}, "
            f"Model={self.embedding_model_name}"
        )

    def run(
        self,
        jsonl_path: Path,
        collection_name: str = "code_chunks",
        reset_collection: bool = False,
        chunk_filter: Optional[ChunkFilter] = None,
        skip_errors: bool = False,
        batch_size: int = 512,
    ) -> dict:
        """
        Run the complete ingestion pipeline.

        Args:
            jsonl_path: Path to the JSONL file containing chunks
            collection_name: Name of the Qdrant collection
            reset_collection: Whether to reset the collection before ingestion
            chunk_filter: Optional filter for chunks
            skip_errors: Whether to skip invalid chunks
            batch_size: Batch size for Qdrant upsert

        Returns:
            dict: Statistics about the ingestion process

        Raises:
            FeniksIngestError: If ingestion fails
            FeniksStoreError: If Qdrant operations fail
        """
        stats = {"loaded": 0, "filtered": 0, "ingested": 0, "collection": collection_name, "reset": reset_collection}

        # Start metrics tracking
        metrics_collector = get_metrics_collector() if settings.metrics_enabled else None
        operation = metrics_collector.start_operation("ingest", collection_name) if metrics_collector else None

        # Check budget
        cost_controller = get_cost_controller() if settings.cost_control_enabled else None

        try:
            # Step 1: Load chunks from JSONL
            log.info("Step 1/5: Loading chunks from JSONL...")
            chunks = load_jsonl(jsonl_path, normalize_paths=True, skip_errors=skip_errors)
            stats["loaded"] = len(chunks)
            log.info(f"Loaded {len(chunks)} chunks")

            # Step 2: Filter chunks
            log.info("Step 2/5: Filtering chunks...")
            if chunk_filter is None:
                chunk_filter = create_default_filter()

            chunks = chunk_filter.filter_chunks(chunks)
            stats["filtered"] = stats["loaded"] - len(chunks)
            log.info(f"After filtering: {len(chunks)} chunks remaining")

            if not chunks:
                raise FeniksIngestError("No chunks remaining after filtering")

            # Step 3: Create embeddings
            log.info("Step 3/5: Creating embeddings...")
            embedding_model = get_embedding_model(self.embedding_model_name)
            dense_embeddings = create_dense_embeddings(embedding_model, chunks)
            log.info(f"Created dense embeddings: shape={dense_embeddings.shape}")

            # Build TF-IDF sparse vectors
            tfidf_vectorizer, tfidf_matrix = build_tfidf(chunks)
            log.info(f"Created TF-IDF sparse vectors: shape={tfidf_matrix.shape}")

            # Step 4: Connect to Qdrant and ensure collection exists
            log.info("Step 4/5: Connecting to Qdrant...")
            try:
                qdrant_client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)

                # Test connection
                collections = qdrant_client.get_collections()
                log.info(f"Connected to Qdrant. Existing collections: " f"{[c.name for c in collections.collections]}")

            except Exception as e:
                raise FeniksStoreError(
                    f"Failed to connect to Qdrant at " f"{self.qdrant_host}:{self.qdrant_port}: {e}"
                ) from e

            # Ensure collection exists
            ensure_collection(
                client=qdrant_client, name=collection_name, dim=dense_embeddings.shape[1], reset=reset_collection
            )
            log.info(f"Collection '{collection_name}' ready")

            # Step 5: Upsert points to Qdrant
            log.info("Step 5/5: Upserting points to Qdrant...")
            upsert_points(
                client=qdrant_client,
                collection=collection_name,
                chunks=chunks,
                dense=dense_embeddings,
                X_tfidf=tfidf_matrix,
                vocab=tfidf_vectorizer.vocabulary_,
                batch=batch_size,
            )
            stats["ingested"] = len(chunks)
            log.info(f"Successfully ingested {len(chunks)} chunks to collection '{collection_name}'")

            # Complete metrics tracking
            if operation and metrics_collector:
                metrics_collector.complete_operation(operation, success=True, metadata={"chunks_ingested": len(chunks)})

            # Charge cost
            if cost_controller:
                try:
                    # Check budget first
                    cost_controller.check_budget(collection_name, "ingest", quantity=len(chunks) // 1000 or 1)
                    # Charge actual cost
                    cost_controller.charge_operation(collection_name, "ingest", quantity=len(chunks) // 1000 or 1)
                except Exception as e:
                    log.warning(f"Cost tracking failed: {e}")

            return stats

        except (FeniksIngestError, FeniksStoreError) as e:
            # Complete metrics with error
            if operation and metrics_collector:
                metrics_collector.complete_operation(operation, success=False, error=str(e))
            raise
        except Exception as e:
            # Complete metrics with error
            if operation and metrics_collector:
                metrics_collector.complete_operation(operation, success=False, error=str(e))
            raise FeniksIngestError(f"Ingestion pipeline failed: {e}") from e


def run_ingest(
    jsonl_path: Path,
    collection_name: str = "code_chunks",
    reset_collection: bool = False,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    skip_errors: bool = False,
) -> dict:
    """
    Convenience function to run the ingestion pipeline.

    Args:
        jsonl_path: Path to the JSONL file
        collection_name: Name of the Qdrant collection
        reset_collection: Whether to reset the collection
        include_patterns: File patterns to include
        exclude_patterns: File patterns to exclude
        skip_errors: Whether to skip invalid chunks

    Returns:
        dict: Statistics about the ingestion
    """
    # Create filter
    chunk_filter = (
        ChunkFilter(include_patterns=include_patterns, exclude_patterns=exclude_patterns)
        if (include_patterns or exclude_patterns)
        else create_default_filter()
    )

    # Create and run pipeline
    pipeline = IngestPipeline()
    return pipeline.run(
        jsonl_path=jsonl_path,
        collection_name=collection_name,
        reset_collection=reset_collection,
        chunk_filter=chunk_filter,
        skip_errors=skip_errors,
    )
