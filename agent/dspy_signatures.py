import dspy


class RouterSignature(dspy.Signature):
    """
    Classify the incoming user question into one of three distinct execution paths: 'rag', 'sql', or 'hybrid'.

    DEFINITIONS:
    1. 'rag': Questions involving text-based knowledge, policies, definitions, or the marketing calendar.
       - Keywords: "policy", "return", "notes", "calendar", "definition", "terms".
       - Example: "What is the return policy for beverages?"

    2. 'sql': Questions requiring database aggregation (SUM, COUNT, AVG) where ALL constraints (dates, ids) are explicitly provided in the question.
       - Keywords: "revenue", "how many", "top customers", "inventory".
       - Example: "Total sales in May 1997?" (Date is explicit).

    3. 'hybrid': Questions asking for database metrics but using 'Named Entities' or 'Time Periods' defined in the docs.
       - Logic: If you need to look up a date range (e.g., "Summer 1997") or a formula (e.g., "Gross Margin") from docs BEFORE running SQL.
       - Example: "Total sales during 'Summer Beverages 1997'?" (Must look up dates for 'Summer Beverages' first).
    """

    question = dspy.InputField(desc="The user's natural language query.")
    classification = dspy.OutputField(
        desc="The routing decision. MUST be exactly one of: ['rag', 'sql', 'hybrid']."
    )
