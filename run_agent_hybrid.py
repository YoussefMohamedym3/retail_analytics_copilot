import json
import logging

import click
from rich import print as rprint

from agent.graph_hybrid import RetailAnalyticsWorkflow
from agent.llm import init_dspy
from agent.schemas import InputRow, OutputRow

# Setup logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("CLI")
logger.setLevel(logging.INFO)


@click.command()
@click.option(
    "--batch",
    default="sample_questions_hybrid_eval.jsonl",
    type=click.Path(exists=True),
    help="Path to the input JSONL file containing questions.",
)
@click.option(
    "--out",
    default="outputs_hybrid.jsonl",
    type=click.Path(),
    help="Path to the output JSONL file to be generated.",
)
def main(batch, out):
    """
    Retail Analytics Copilot CLI Runner.
    Processes questions from a batch file and outputs results according to the Output Contract.
    """
    rprint("[bold green]=== Retail Analytics Copilot CLI ===[/bold green]")

    # 1. Initialize DSPy and Graph
    init_dspy()
    workflow = RetailAnalyticsWorkflow()
    app = workflow.get_graph()
    rprint("[bold blue]✅ Graph Compiled (Full Hybrid Agent)[/bold blue]")

    final_outputs = []

    # 2. Process Questions
    rprint(f"[yellow]📂 Reading from: {batch}[/yellow]")
    rprint(f"[yellow]✍️ Writing to: {out}[/yellow]\n")

    try:
        with open(batch, "r") as f:
            for line in f:
                if not line.strip():
                    continue

                # Validate Input using Pydantic
                data = json.loads(line)
                input_row = InputRow(**data)

                rprint(f"[bold cyan]Question ID: {input_row.id}[/bold cyan]")
                print(f"Query: {input_row.question}")

                # Init State
                initial_state = {
                    "id": input_row.id,
                    "question": input_row.question,
                    "format_hint": input_row.format_hint,
                    "repair_steps": 0,
                    "citations": [],
                }
                config = {"configurable": {"thread_id": input_row.id}}  # Run Graph
                print("⏳ Running Graph...")
                final_state = initial_state.copy()

                # Stream to print intermediate steps
                for step in app.stream(initial_state, config=config):
                    for node_name, update in step.items():
                        rprint(f"[dim] ↳ Finished Node: [bold]{node_name}[/bold][/dim]")
                        final_state.update(update)

                # 3. Assemble and Validate Final Output
                # CRITICAL FIX: Map 'sql_query' from state to 'sql' in output
                output_data = {
                    "id": final_state.get("id"),
                    "final_answer": final_state.get("final_answer"),
                    "sql": final_state.get(
                        "sql_query", ""
                    ),  # <--- CHANGED from 'sql' to 'sql_query'
                    "confidence": final_state.get("confidence", 0.0),
                    "explanation": final_state.get(
                        "explanation", "Could not synthesize explanation."
                    ),
                    "citations": final_state.get("citations", []),
                }

                # Validate against the Output Contract Pydantic model
                final_output_row = OutputRow(**output_data)

                final_outputs.append(final_output_row.model_dump_json())

                rprint(
                    f"✅ Final Result Type: {type(final_output_row.final_answer).__name__}"
                )
                rprint(
                    f"👉 [bold]Answer Preview:[/bold] {final_output_row.final_answer} [dim](Confidence: {final_output_row.confidence:.2f})[/dim]"
                )
                print("-" * 50)

        # 4. Write to JSONL
        with open(out, "w") as outfile:
            for line in final_outputs:
                outfile.write(line + "\n")

        rprint(
            f"\n[bold green]✅ Evaluation Complete. Results written to {out}[/bold green]"
        )

    except Exception as e:
        rprint(
            f"\n[bold red]❌ A Critical Error Occurred during processing: {e}[/bold red]"
        )
        rprint("The agent failed to complete the run. Check logs for details.")


if __name__ == "__main__":
    main()
