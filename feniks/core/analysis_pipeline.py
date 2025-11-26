"""
Analysis Pipeline - orchestrates system model building and analysis.
Loads chunks from Qdrant, builds system model, detects capabilities, generates reports.
"""
from pathlib import Path
from typing import Optional, List
import json

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from feniks.logger import get_logger
from feniks.config import settings
from feniks.types import Chunk, SystemModel, Dependency, ApiEndpoint, GitInfo
from feniks.exceptions import FeniksError, FeniksStoreError
from feniks.core.system_model_builder import build_system_model
from feniks.core.capability_detector import CapabilityDetector
from feniks.core.report_generator import generate_report
from feniks.core.meta_reflection_engine import generate_meta_reflections, save_meta_reflections
from feniks.integrations.rae_client import create_rae_client, RAEError
from feniks.integrations.rae_formatter import RAEFormatter

log = get_logger("core.analysis")


class AnalysisPipeline:
    """Orchestrates the analysis pipeline."""

    def __init__(
        self,
        qdrant_host: Optional[str] = None,
        qdrant_port: Optional[int] = None
    ):
        """
        Initialize the analysis pipeline.

        Args:
            qdrant_host: Qdrant host (defaults to settings)
            qdrant_port: Qdrant port (defaults to settings)
        """
        self.qdrant_host = qdrant_host or settings.qdrant_host
        self.qdrant_port = qdrant_port or settings.qdrant_port

        log.info(f"AnalysisPipeline initialized: Qdrant={self.qdrant_host}:{self.qdrant_port}")

    def _load_chunks_from_qdrant(
        self,
        collection_name: str,
        limit: Optional[int] = None
    ) -> List[Chunk]:
        """
        Load chunks from Qdrant collection.

        Args:
            collection_name: Name of the Qdrant collection
            limit: Optional limit on number of chunks to load

        Returns:
            List[Chunk]: Loaded chunks

        Raises:
            FeniksStoreError: If loading fails
        """
        log.info(f"Loading chunks from Qdrant collection: {collection_name}")

        try:
            client = QdrantClient(host=self.qdrant_host, port=self.qdrant_port)

            # Get collection info
            collection_info = client.get_collection(collection_name)
            total_points = collection_info.points_count

            log.info(f"Collection has {total_points} points")

            # Scroll through points
            chunks = []
            offset = None
            batch_size = 100

            while True:
                results = client.scroll(
                    collection_name=collection_name,
                    limit=batch_size,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False
                )

                points, next_offset = results

                if not points:
                    break

                # Convert points to chunks
                for point in points:
                    try:
                        chunk = self._point_to_chunk(point.payload, point.id)
                        chunks.append(chunk)
                    except Exception as e:
                        log.warning(f"Failed to convert point {point.id} to chunk: {e}")

                # Check limit
                if limit and len(chunks) >= limit:
                    chunks = chunks[:limit]
                    break

                # Check if we've reached the end
                if next_offset is None:
                    break

                offset = next_offset

            log.info(f"Loaded {len(chunks)} chunks from Qdrant")
            return chunks

        except Exception as e:
            raise FeniksStoreError(f"Failed to load chunks from Qdrant: {e}") from e

    def _point_to_chunk(self, payload: dict, point_id: str) -> Chunk:
        """Convert a Qdrant point payload to a Chunk object."""
        # Parse dependencies
        dependencies = []
        for dep_data in payload.get("dependencies", []):
            if isinstance(dep_data, dict):
                dependencies.append(Dependency(
                    type=dep_data.get("type", ""),
                    value=dep_data.get("value", "")
                ))

        # Parse API endpoints
        api_endpoints = []
        for ep_data in payload.get("api_endpoints", []):
            if isinstance(ep_data, dict):
                api_endpoints.append(ApiEndpoint(
                    url=ep_data.get("url", ""),
                    method=ep_data.get("method", "GET"),
                    dataKeys=ep_data.get("dataKeys", []),
                    paramKeys=ep_data.get("paramKeys", [])
                ))

        # Parse git info
        git_info = None
        git_data = payload.get("git_last_commit")
        if git_data and isinstance(git_data, dict):
            git_info = GitInfo(
                hash=git_data.get("hash", ""),
                author=git_data.get("author", ""),
                date=git_data.get("date", ""),
                summary=git_data.get("summary", "")
            )

        # Create chunk
        chunk = Chunk(
            id=payload.get("id", str(point_id)),
            file_path=payload.get("file_path", ""),
            start_line=payload.get("start_line", 0),
            end_line=payload.get("end_line", 0),
            text=payload.get("text", ""),
            chunk_name=payload.get("chunk_name", ""),
            language=payload.get("language", "javascript"),
            module=payload.get("module"),
            kind=payload.get("kind"),
            ast_node_type=payload.get("ast_node_type"),
            dependencies=dependencies,
            calls_functions=payload.get("calls_functions", []),
            api_endpoints=api_endpoints,
            ui_routes=payload.get("ui_routes", []),
            cyclomatic_complexity=payload.get("cyclomatic_complexity", 0),
            business_tags=payload.get("business_tags", []),
            git_last_commit=git_info
        )

        return chunk

    def _sync_with_rae(self, system_model: SystemModel, meta_reflections: list) -> bool:
        """
        Sync analysis results with RAE.

        Args:
            system_model: The system model
            meta_reflections: List of meta-reflections

        Returns:
            bool: True if sync was successful, False otherwise
        """
        # Create RAE client
        rae_client = create_rae_client()
        if not rae_client:
            log.debug("RAE client not available, skipping sync")
            return False

        try:
            # Format data for RAE
            formatter = RAEFormatter()

            # 1. Store meta-reflections
            if meta_reflections:
                log.info(f"Storing {len(meta_reflections)} meta-reflections to RAE...")
                for reflection in meta_reflections:
                    try:
                        payload = formatter.format_meta_reflection(reflection)
                        rae_client.store_meta_reflection(payload)
                    except RAEError as e:
                        log.warning(f"Failed to store meta-reflection {reflection.id}: {e}")

            # 2. Store system capabilities
            if system_model.capabilities:
                log.info(f"Storing {len(system_model.capabilities)} capabilities to RAE...")
                try:
                    capabilities_payload = formatter.format_system_capabilities(system_model)
                    rae_client.store_system_capabilities(capabilities_payload)
                except RAEError as e:
                    log.warning(f"Failed to store system capabilities: {e}")

            # 3. Store complete system model
            log.info("Storing system model to RAE...")
            try:
                system_model_payload = formatter.format_system_model(system_model)
                rae_client.store_system_model(system_model_payload)
            except RAEError as e:
                log.warning(f"Failed to store system model: {e}")

            log.info("RAE sync completed successfully")
            return True

        except Exception as e:
            log.error(f"RAE sync failed: {e}", exc_info=True)
            return False

    def run(
        self,
        project_id: str,
        collection_name: str = "code_chunks",
        output_path: Optional[Path] = None,
        meta_reflections_output: Optional[Path] = None,
        limit: Optional[int] = None
    ) -> SystemModel:
        """
        Run the complete analysis pipeline.

        Args:
            project_id: Project identifier
            collection_name: Qdrant collection name
            output_path: Optional path to save report
            meta_reflections_output: Optional path to save meta-reflections JSONL
            limit: Optional limit on chunks to analyze

        Returns:
            SystemModel: The constructed system model

        Raises:
            FeniksError: If analysis fails
        """
        stats = {
            "project_id": project_id,
            "collection": collection_name,
            "chunks_loaded": 0,
            "modules": 0,
            "dependencies": 0,
            "capabilities": 0
        }

        try:
            # Step 1: Load chunks from Qdrant
            log.info("Step 1/5: Loading chunks from Qdrant...")
            chunks = self._load_chunks_from_qdrant(collection_name, limit=limit)
            stats["chunks_loaded"] = len(chunks)

            if not chunks:
                raise FeniksError(f"No chunks found in collection '{collection_name}'")

            log.info(f"Loaded {len(chunks)} chunks")

            # Step 2: Build system model
            log.info("Step 2/5: Building system model...")
            system_model = build_system_model(chunks, project_id)
            stats["modules"] = system_model.total_modules
            stats["dependencies"] = len(system_model.dependencies)
            log.info(f"Built system model with {system_model.total_modules} modules")

            # Step 3: Detect capabilities
            log.info("Step 3/5: Detecting capabilities...")
            detector = CapabilityDetector()
            system_model = detector.enrich_system_model(system_model, chunks)
            stats["capabilities"] = len(system_model.capabilities)
            log.info(f"Detected {len(system_model.capabilities)} capabilities")

            # Step 4: Generate meta-reflections
            log.info("Step 4/6: Generating meta-reflections...")
            meta_reflections = generate_meta_reflections(system_model)
            stats["meta_reflections"] = len(meta_reflections)
            log.info(f"Generated {len(meta_reflections)} meta-reflections")

            # Save meta-reflections if output path specified
            if meta_reflections_output:
                save_meta_reflections(meta_reflections, meta_reflections_output, format="jsonl")
                log.info(f"Meta-reflections saved to {meta_reflections_output}")

            # Step 5: Sync with RAE (if enabled)
            log.info("Step 5/7: Syncing with RAE...")
            rae_sync_success = self._sync_with_rae(system_model, meta_reflections)
            if rae_sync_success:
                log.info("Successfully synced data with RAE")
            else:
                log.info("RAE sync skipped (disabled or failed)")

            # Step 6: Generate report (including meta-reflections)
            log.info("Step 6/7: Generating report...")
            report = generate_report(system_model, output_path, meta_reflections=meta_reflections)

            if output_path:
                log.info(f"Report saved to {output_path}")
            else:
                # Print summary to console
                print("\n" + report)

            # Step 7: Statistics
            log.info("Step 7/7: Analysis complete")
            log.info(f"  Project: {stats['project_id']}")
            log.info(f"  Chunks: {stats['chunks_loaded']}")
            log.info(f"  Modules: {stats['modules']}")
            log.info(f"  Dependencies: {stats['dependencies']}")
            log.info(f"  Capabilities: {stats['capabilities']}")

            return system_model

        except (FeniksError, FeniksStoreError):
            raise
        except Exception as e:
            raise FeniksError(f"Analysis pipeline failed: {e}") from e


def run_analysis(
    project_id: str,
    collection_name: str = "code_chunks",
    output_path: Optional[Path] = None,
    meta_reflections_output: Optional[Path] = None,
    limit: Optional[int] = None
) -> SystemModel:
    """
    Convenience function to run the analysis pipeline.

    Args:
        project_id: Project identifier
        collection_name: Qdrant collection name
        output_path: Optional path to save report
        meta_reflections_output: Optional path to save meta-reflections JSONL
        limit: Optional limit on chunks to analyze

    Returns:
        SystemModel: The constructed system model
    """
    pipeline = AnalysisPipeline()
    return pipeline.run(
        project_id=project_id,
        collection_name=collection_name,
        output_path=output_path,
        meta_reflections_output=meta_reflections_output,
        limit=limit
    )
