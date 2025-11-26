import logging
from pathlib import Path

# Setup professional logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("RAG")

# Dynamic Path Resolution
# logic: this file is in agent/rag/, so parens is agent/rag -> agent -> root
Current_File = Path(__file__).resolve()
ROOT_DIR = Current_File.parent.parent.parent
DOCS_DIR = ROOT_DIR / "docs"


def validate_paths():
    if not DOCS_DIR.exists():
        logger.warning(f"Docs directory not found at: {DOCS_DIR}")
    else:
        logger.info(f"Docs directory verified at: {DOCS_DIR}")
