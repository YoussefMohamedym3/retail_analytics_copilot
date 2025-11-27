from typing import Any, List, Optional

from pydantic import BaseModel, Field


class InputRow(BaseModel):
    """
    Validates a single line from the input evaluation file.
    Ref: sample_questions_hybrid_eval.jsonl
    """

    id: str = Field(..., description="Unique test case ID")
    question: str = Field(..., description="The natural language query")
    format_hint: str = Field(
        ..., description="Expected output format (e.g., 'int', 'float')"
    )


class OutputRow(BaseModel):
    """
    Enforces the strict Output Contract for the final JSONL file.
    Ref: Output Contract
    """

    id: str
    final_answer: Any
    sql: str
    confidence: float
    explanation: str
    citations: List[str]
