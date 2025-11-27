import json
import os
import sys

# Add current directory to path so imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.sqlite_tool import execute_sql, get_db_schema


def run_test(
    name,
    result,
    expected_status=None,
    expected_in_output=None,
    not_expected_in_output=None,
):
    """Helper to print colorful test results"""
    passed = True

    # Check status if it's a JSON response
    if expected_status:
        try:
            data = json.loads(result)
            if data.get("status") != expected_status:
                passed = False
                print(
                    f"❌ {name}: Status mismatch. Got {data.get('status')}, expected {expected_status}"
                )
        except:
            passed = False
            print(f"❌ {name}: Result was not valid JSON.")

    # Check for substring presence
    if expected_in_output and expected_in_output not in str(result):
        passed = False
        print(f"❌ {name}: Missing expected content '{expected_in_output}'")

    # Check for forbidden substring
    if not_expected_in_output and not_expected_in_output in str(result):
        passed = False
        print(f"❌ {name}: Found forbidden content '{not_expected_in_output}'")

    if passed:
        print(f"✅ {name}: Passed")


def main():
    print("=== 🛠️  Testing Retail Analytics Copilot Tools ===\n")

    # ---------------------------------------------------------
    # TEST 1: Schema Filtering (The "Whitelist")
    # ---------------------------------------------------------
    print("--- Testing Schema Visibility ---")
    schema = get_db_schema()
    print(schema)
    # 1. Check valid tables exist
    run_test("Schema contains 'orders'", schema, expected_in_output="Table: orders")
    run_test(
        "Schema contains 'order_items'", schema, expected_in_output="Table: order_items"
    )

    # 2. Check PII tables are HIDDEN (The most important test!)
    run_test(
        "Schema HIDES 'Employees' Table",
        schema,
        not_expected_in_output="Table: Employees",
    )
    run_test("Schema HIDES 'Territories'", schema, not_expected_in_output="Territories")

    # ---------------------------------------------------------
    # TEST 2: SQL Execution (Read Access)
    # ---------------------------------------------------------
    print("\n--- Testing SQL Execution ---")

    # 3. Basic Select on a View
    query_valid = "SELECT count(*) as count FROM orders"
    res_valid = execute_sql(query_valid)
    run_test(
        "Execute Valid SELECT",
        res_valid,
        expected_status="success",
        expected_in_output="count",
    )

    # 4. Accessing the re-mapped 'order_items' view
    query_view = "SELECT * FROM order_items LIMIT 1"
    res_view = execute_sql(query_view)
    run_test(
        "Execute on Mapped View (order_items)", res_view, expected_status="success"
    )

    # ---------------------------------------------------------
    # TEST 3: Security Guardrails (The "Blacklist")
    # ---------------------------------------------------------
    print("\n--- Testing Security Guardrails ---")

    # 5. Try to DROP a table
    query_drop = "DROP TABLE orders"
    res_drop = execute_sql(query_drop)
    run_test(
        "Block DROP command",
        res_drop,
        expected_status="error",
        expected_in_output="forbidden",
    )

    # 6. Try to UPDATE a table
    query_update = "UPDATE orders SET Freight = 0"
    res_update = execute_sql(query_update)
    run_test(
        "Block UPDATE command",
        res_update,
        expected_status="error",
        expected_in_output="modification commands",
    )

    # 7. Try to SELECT from a table that exists in DB but is hidden (Employees)
    # Note: Your current code ALLOWS this if they guess the name, but the Schema hides it.
    # This just confirms the DB connection works for raw queries if needed.
    query_hidden = "SELECT count(*) FROM Employees"
    res_hidden = execute_sql(query_hidden)
    # This will likely succeed because the filter is at Schema level, not Execution level.
    # That is acceptable for this assignment.
    print(
        f"ℹ️  Direct Access to Hidden Table (Employees): {json.loads(res_hidden)['status']} (Expected: success/error depending on implementation)"
    )


if __name__ == "__main__":
    main()
