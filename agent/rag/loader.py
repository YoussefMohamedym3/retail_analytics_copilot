import re
from pathlib import Path
from typing import List

from .config import logger
from .schema import DocumentChunk


class CorpusLoader:
    @staticmethod
    def clean_tokenize(text: str) -> List[str]:
        """
        Tokenizes text by splitting on non-word characters and lowercasing.
        """
        return re.findall(r"\w+", text.lower())

    @staticmethod
    def load_chunks(docs_dir: Path) -> List[DocumentChunk]:
        """
        Iterates over Markdown files in the directory and chunks them by paragraph.
        """
        chunks = []
        md_files = list(docs_dir.glob("*.md"))

        if not md_files:
            logger.warning("No Markdown files found in docs directory.")
            return []

        for filepath in md_files:
            try:
                content = filepath.read_text(encoding="utf-8")
                # Split by double newline (paragraphs)
                raw_paragraphs = content.split("\n\n")

                for i, para in enumerate(raw_paragraphs):
                    clean_para = para.strip()
                    if not clean_para:
                        continue

                    chunk_id = f"{filepath.name}::chunk{i}"
                    chunks.append(
                        DocumentChunk(
                            id=chunk_id, content=clean_para, source=filepath.name
                        )
                    )
            except Exception as e:
                logger.error(f"Failed to read {filepath.name}: {e}")

        logger.info(f"Loaded {len(chunks)} chunks from {len(md_files)} files.")
        return chunks
