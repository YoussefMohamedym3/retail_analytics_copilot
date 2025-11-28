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


class PlannerSignature(dspy.Signature):
    """
    Review the User Question and the provided Context (definitions/calendars) to extract structured constraints for SQL.

    Goal: Resolve ambiguous terms (like "Summer 1997" or "High Value") into concrete SQL-ready values.

    CRITICAL INSTRUCTIONS:
    1. Output strictly valid JSON.
    2. Keep reasoning BRIEF (max 1 sentence). Do not explain the SQL logic, just extract the filters.
    3. If no specific constraints are found, return "{}".
    """

    question = dspy.InputField()
    context = dspy.InputField(desc="Retrieved definitions from the knowledge base.")

    constraints = dspy.OutputField(desc="JSON-format dictionary of extracted filters.")


class GenerateSQLSignature(dspy.Signature):
    """
    Transform a natural language question into a valid, read-only SQLite query.

    Rules:
    - Use the provided db_schema.
    - Only use SELECT or WITH (CTEs).
    - Never try to UPDATE or DROP.
    - PAY ATTENTION to the 'constraints' field. It contains extracted dates/ids from the docs.

    CRITICAL DOMAIN RULES (Follow these strictly):
    1. Revenue Calculation: Use `SUM(UnitPrice * Quantity * (1 - Discount))` from the `order_items` table.
    2. CostOfGoods Approximation: The database lacks a cost field. ALWAYS use `(UnitPrice * 0.7)` to approximate Cost.
       - Gross Margin = `SUM((UnitPrice - (UnitPrice * 0.7)) * Quantity * (1 - Discount))`
    3. Join Path for Categories: `orders` -> `order_items` -> `products` -> `categories`. Do not join Categories directly to Orders.
    """

    question = dspy.InputField(desc="The data question to answer.")
    db_schema = dspy.InputField(desc="The available database table definitions.")
    constraints = dspy.InputField(
        desc="Extracted filters (e.g., dates) from the Planner."
    )
    format_hint = dspy.InputField(
        desc="Hint for the expected return type (guides the SELECT clause)."
    )

    sql_query = dspy.OutputField(desc="The executable SQLite query string.")


class RepairSQLSignature(dspy.Signature):
    """
    Fix a failing SQL query based on the database error message.

    Strategies:
    1. Syntax Errors: Fix typos (e.g., "BETWEWEN" -> "BETWEEN").
    2. Schema Errors: If a column doesn't exist, check the schema and find the correct column/table.
    3. Logical Errors: If the query returns empty or wrong data, adjust the JOINs or WHERE clauses.

    DOMAIN KNOWLEDGE REFRESHER:
    - CostOfGoods DOES NOT EXIST. Use `UnitPrice * 0.7`.
    - Revenue = `SUM(UnitPrice * Quantity * (1 - Discount))`.
    - Join Path: `orders` -> `order_items` -> `products` -> `categories`.
    """

    question = dspy.InputField(desc="The original user question.")
    bad_query = dspy.InputField(desc="The SQL query that failed.")
    error_message = dspy.InputField(desc="The error returned by SQLite.")
    db_schema = dspy.InputField(
        desc="The database schema to reference for fixing columns."
    )
    constraints = dspy.InputField(
        desc="Extracted filters from Planner (ensure these are preserved)."
    )
    format_hint = dspy.InputField(
        desc="Hint for the expected return type (guides the SELECT clause)."
    )

    fixed_sql = dspy.OutputField(desc="The corrected SQLite query string.")


class SynthesizeAnswerSignature(dspy.Signature):
    """
    Generate a structured final answer based on the provided Context (RAG) or SQL Results.

    Requirements:
    1. 'final_answer': Must strictly match the 'format_hint' (e.g., if hint is 'int', return only the number).
    2. 'citations': List every DB table used (e.g., 'Orders') and every doc chunk ID used (e.g., 'marketing_calendar::chunk0').
    3. 'explanation': Keep it under 2 sentences.
    """

    question = dspy.InputField()
    context = dspy.InputField(desc="Text chunks from RAG (if any).")
    sql_query = dspy.InputField(desc="The SQL that was run (if any).")
    sql_result = dspy.InputField(desc="The rows returned from the DB (if any).")
    format_hint = dspy.InputField(
        desc="The required format for the final answer (e.g., 'float', 'json')."
    )

    final_answer = dspy.OutputField(desc="The precise answer matching format_hint.")
    explanation = dspy.OutputField(desc="Brief justification.")
    citations = dspy.OutputField(desc="Comma-separated list of sources used.")
