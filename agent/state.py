from typing import Any, Dict, List, Optional, TypedDict, Union


class AgentState(TypedDict):
    """
    State schema for the Retail Analytics Copilot graph.
    Carries data between nodes (Router -> Planner -> SQL/RAG -> Synth).
    """

    # --- Inputs ---
    id: str
    question: str
    format_hint: str

    # --- Orchestration ---
    route: str

    # --- Planner State ---
    # Stores extracted dates, KPIs, and entities (e.g., {"start_date": "1997-01-01"})
    constraints: Dict[str, Any]

    # --- Retrieval State (RAG) ---
    retrieved_docs: List[Dict[str, Any]]

    # --- SQL State ---
    sql_query: str
    # Result can be a list of rows (dicts) or an error message string
    sql_result: Union[List[Dict[str, Any]], str]
    is_sql_error: bool  # Flag to trigger repair loop

    # --- Output / Synthesis ---
    final_answer: Any  # The typed result matching format_hint
    explanation: str  # Brief reasoning (< 2 sentences)
    confidence: float  # 0.0 to 1.0
    citations: List[str]  # ["Orders", "marketing_calendar::chunk0"]

    # --- Metadata / Control Flow ---
    repair_steps: int  # Counts iterations of the repair loop (max 2)
