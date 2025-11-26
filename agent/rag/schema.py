from typing import Optional

from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """
    Represents a single segment of text from the knowledge base.
    """

    chunk_id: str = Field(
        ..., alias="id"
    )  # Alias 'id' to match assignment requirements
    content: str
    source: str
    score: Optional[float] = 0.0

    class Config:
        populate_by_name = True
