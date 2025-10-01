import os
from pathlib import Path
import sys

try:
    from dotenv import load_dotenv
    # Load environment variables from a .env file if it exists
    load_dotenv()
except ModuleNotFoundError:
    print("WARNING: python-dotenv not found. Skipping .env file loading.", file=sys.stderr)

class Settings:
    """
    Centralized configuration for the Feniks knowledge base builder.
    Reads settings from environment variables with sensible defaults.
    """
    # The root directory of the project.
    PROJECT_ROOT: Path = Path(__file__).parent.parent

    # Path to the frontend source code to be indexed.
    # Can be overridden by the FENIKS_FRONTEND_ROOT environment variable.
    FRONTEND_ROOT: Path = Path(os.getenv(
        "FENIKS_FRONTEND_ROOT", 
        PROJECT_ROOT / "frontend-master"
    ))

    # Directory where all output artifacts will be stored.
    # Can be overridden by the FENIKS_OUTPUT_DIR environment variable.
    OUTPUT_DIR: Path = Path(os.getenv(
        "FENIKS_OUTPUT_DIR", 
        PROJECT_ROOT / "output"
    ))

    # Path to the Node.js indexer script.
    NODE_INDEXER_PATH: Path = PROJECT_ROOT / "scripts" / "js_html_indexer.mjs"

    # --- Qdrant Settings ---
    QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "feniks_kb_test")
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", 6333))

    # --- Embedding Model Settings ---
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Create a single, importable instance of the settings.
settings = Settings()
