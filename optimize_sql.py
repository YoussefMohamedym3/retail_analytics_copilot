import json
import logging
import math
import random

import dspy
from dspy.teleprompt import BootstrapFewShot

from agent.dspy_signatures import GenerateSQLSignature
from agent.llm import init_dspy
from agent.train_examples import train_examples
from tools.sqlite_tool import execute_sql

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Optimizer")


def sql_metric(example, pred, trace=None):
    """
    Robust Metric: Checks Syntax AND Accuracy against the Gold SQL.
    Returns 1.0 only if the model's query returns the same data as the Gold query.
    """
    predicted_sql = pred.sql_query
    gold_sql = example.sql_query

    # Sanity Checks (The "Anti-Hallucination" Layer)
    if "p.CategoryName" in predicted_sql or "p.Categoryname" in predicted_sql:
        return 0.0  # Fail: Hallucinated column
    if "BETWEWEN" in predicted_sql or "BETWEINTERVAL" in predicted_sql:
        return 0.0  # Fail: Hallucinated keyword

    # Execution & Accuracy Check
    try:

        pred_resp_str = execute_sql(predicted_sql)
        pred_resp = json.loads(pred_resp_str)

        if pred_resp.get("status") == "error":
            return 0.0

        gold_resp_str = execute_sql(gold_sql)
        gold_resp = json.loads(gold_resp_str)

        if gold_resp.get("status") == "error":
            logger.warning(f"⚠️ Gold SQL failed for: {example.question}")
            return 0.0

        pred_data = pred_resp.get("data", [])
        gold_data = gold_resp.get("data", [])

        if pred_data == gold_data:
            return 1.0

        # Float Tolerance Comparison
        # If the result is a single number, allow for tiny rounding differences
        try:
            # Extract values if it's a simple list of 1 dict
            if len(pred_data) == 1 and len(gold_data) == 1:
                val_pred = list(pred_data[0].values())[0]
                val_gold = list(gold_data[0].values())[0]

                # Check if both are numbers
                if isinstance(val_pred, (int, float)) and isinstance(
                    val_gold, (int, float)
                ):
                    # Allow 1% tolerance
                    if math.isclose(val_pred, val_gold, rel_tol=0.01):
                        return 1.0
        except:
            pass

        # If we get here, results didn't match
        logger.info(f"Mismatch! Pred: {pred_data} | Gold: {gold_data}")
        return 0.0

    except Exception:
        return 0.0


def main():
    print("🚀 Initializing DSPy and Model...")
    lm = init_dspy()

    # 1. Define the Module
    class SQLModule(dspy.Module):
        def __init__(self):
            super().__init__()
            self.generate = dspy.ChainOfThought(GenerateSQLSignature)

        def forward(self, question, constraints, format_hint, db_schema):
            return self.generate(
                question=question,
                constraints=constraints,
                format_hint=format_hint,
                db_schema=db_schema,
            )

    # 2. Shuffle Examples
    print(f"📚 Loaded {len(train_examples)} examples.")
    print("🔀 Shuffling examples...")
    random.seed(42)
    random.shuffle(train_examples)

    # 3. Configure Optimizer
    print("⚙️  Configuring Optimizer (BootstrapFewShot)...")
    teleprompter = BootstrapFewShot(
        metric=sql_metric,
        max_bootstrapped_demos=12,
        max_labeled_demos=12,
    )

    # 4. Run Compilation
    print(f"🏋️  Starting Optimization...")
    student = SQLModule()
    optimized_program = teleprompter.compile(student, trainset=train_examples)

    # 5. Save
    output_path = "agent/optimized_sql_module.json"
    optimized_program.save(output_path)

    print(f"\n✅ Optimization Complete!")
    print(f"💾 Saved to: {output_path}")


if __name__ == "__main__":
    main()
