import json
import logging

from rich import print as rprint

from agent.graph_hybrid import RetailAnalyticsWorkflow
from agent.llm import init_dspy
from agent.schemas import InputRow

# Setup logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("CLI")
logger.setLevel(logging.INFO)


def main():
    rprint("[bold green]=== Retail Analytics Copilot CLI ===[/bold green]")

    # 1. Initialize DSPy
    init_dspy()

    # 2. Build Graph
    workflow = RetailAnalyticsWorkflow()
    app = workflow.get_graph()
    rprint("[bold blue]✅ Graph Compiled[/bold blue]")

    # 3. Process Questions
    input_file = "sample_questions_hybrid_eval.jsonl"
    rprint(f"[yellow]📂 Reading from: {input_file}[/yellow]\n")

    try:
        with open(input_file, "r") as f:
            for line in f:
                if not line.strip():
                    continue

                # Validate Input
                data = json.loads(line)
                input_row = InputRow(**data)

                rprint(f"[bold cyan]Question ID: {input_row.id}[/bold cyan]")
                print(f"Query: {input_row.question}")

                # Init State
                state = {
                    "id": input_row.id,
                    "question": input_row.question,
                    "format_hint": input_row.format_hint,
                    "repair_steps": 0,
                    "citations": [],
                }

                print("⏳ Running...")

                # --- CHANGED: Use stream() to see steps ---
                final_state = state.copy()

                # app.stream() yields a dict like: {'router': {'route': 'sql'}}
                for step in app.stream(state):
                    for node_name, update in step.items():
                        rprint(f"[dim] ↳ Finished Node: [bold]{node_name}[/bold][/dim]")
                        rprint(f"[dim]   Update: {update}[/dim]")

                        # Update our local final_state to keep track
                        final_state.update(update)
                # ------------------------------------------

                # Show Result
                route = final_state.get("route", "unknown")
                color = (
                    "green"
                    if route == "sql"
                    else "magenta" if route == "rag" else "yellow"
                )
                rprint(
                    f"👉 [bold]Router Decision:[/bold] [{color}]{route.upper()}[/{color}]"
                )
                print("-" * 50)

    except FileNotFoundError:
        rprint(f"[bold red]❌ File not found: {input_file}[/bold red]")
        print(
            "Please ensure you have created the sample_questions_hybrid_eval.jsonl file."
        )


if __name__ == "__main__":
    main()
