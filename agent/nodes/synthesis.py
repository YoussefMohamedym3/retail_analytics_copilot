import ast
import logging
import re

import dspy

from agent.dspy_signatures import SynthesizeAnswerSignature
from agent.state import AgentState

logger = logging.getLogger("SynthesizerNode")

# Initialize module
synth_module = dspy.ChainOfThought(SynthesizeAnswerSignature)


def synthesize_answer_node(state: AgentState) -> dict:
    """
    Finalizes the answer.
    Improvements:
    - Fast-fail if SQL crashed (don't ask LLM to hallucinate).
    - Checks if SQL returned 0 rows (lowers confidence).
    - Robust Regex parsing for numbers.
    """
    question = state["question"]
    docs = state.get("retrieved_docs", [])
    sql_query = state.get("sql_query", "")
    sql_result = state.get("sql_result", [])
    format_hint = state.get("format_hint", "str")
    repair_steps = state.get("repair_steps", 0)
    is_sql_error = state.get("is_sql_error", False)
    route = state.get("route")

    logger.info(f"🎨 Synthesizing answer for: {question[:50]}...")

    # CONFIDENCE CALCULATION STRATEGY
    # Start at 1.0 (Perfect)
    confidence = 1.0

    # Penalty 1: Repairs used (0.1 per step)
    if repair_steps > 0:
        confidence -= repair_steps * 0.1

    # Penalty 2: SQL returned empty results (Big penalty)
    # Only penalize empty SQL if we INTENDED to run SQL
    if route in ["sql", "hybrid"] and isinstance(sql_result, list) and not sql_result:
        confidence -= 0.5
        logger.warning("📉 Confidence penalty: SQL returned 0 rows.")

    # Critical Fail: SQL Crashed
    if is_sql_error:
        confidence = 0.0

    # Clamp confidence between 0.0 and 1.0
    confidence = max(0.0, min(1.0, confidence))

    # If confidence is 0.0 (SQL crashed)
    if is_sql_error:
        return {
            "final_answer": "N/A",
            "explanation": f"I could not answer this because the SQL query failed to execute. Error: {sql_result}",
            "citations": [],
            "confidence": 0.0,
            "sql": sql_query,
        }

    # PREPARE CONTEXT FOR SUCCESS PATH
    # We prioritize SQL results, but include Docs for context/definitions
    doc_context = "\n".join(
        [f"[{r.get('id', 'doc')}] {r.get('content', '')}" for r in docs]
    )

    final_context = (
        f"SQL Query Run: {sql_query}\n"
        f"SQL Result Data: {str(sql_result)}\n\n"
        f"Reference Documents:\n{doc_context}"
    )

    # RUN DSPY GENERATION
    try:
        pred = synth_module(
            question=question,
            context=final_context,
            sql_query=sql_query,
            sql_result=str(sql_result),
            format_hint=format_hint,
        )

        final_answer_raw = pred.final_answer
        explanation = pred.explanation.strip()
        citations_raw = pred.citations
        logger.info(f"📝 Raw Synthesizer Answer: {final_answer_raw}")
        logger.info(f"📝 Raw Explanation: {explanation}")
        logger.info(f"📝 Raw Citations: {citations_raw}")

        # PARSING
        try:
            # Remove Markdown code blocks if the model added them
            clean_ans = (
                final_answer_raw.replace("```json", "").replace("```", "").strip()
            )

            # Handle format hints using Regex for robustness
            if "int" in format_hint.lower():
                # Extract first number found
                numbers = re.findall(r"-?\d+", clean_ans)
                if numbers:
                    final_answer = int(numbers[0])
                else:
                    final_answer = 0

            elif "float" in format_hint.lower():
                # Extract first float found
                numbers = re.findall(r"[-+]?\d*\.\d+|\d+", clean_ans.replace(",", ""))
                if numbers:
                    final_answer = float(numbers[0])
                else:
                    final_answer = 0.0

            elif any(x in format_hint.lower() for x in ["list", "dict", "{", "["]):
                # Use AST for complex structures
                final_answer = ast.literal_eval(clean_ans)

            else:
                # Default string
                final_answer = clean_ans

        except Exception as e:
            logger.warning(f"⚠️ Parsing failed for '{clean_ans}' ({format_hint}): {e}")
            final_answer = clean_ans  # Fallback to raw string

        # Clean Citations: Ensure they are a list of strings
        if isinstance(citations_raw, str):
            citations = [c.strip() for c in citations_raw.split(",") if c.strip()]
        else:
            citations = []

    except Exception as e:
        logger.error(f"❌ Synthesis LLM Error: {e}")
        final_answer = "Error"
        explanation = "Model failed to synthesize response."
        citations = []
        confidence = 0.0

    return {
        "final_answer": final_answer,
        "explanation": explanation,
        "citations": citations,
        "confidence": confidence,
        "sql": sql_query,
    }
