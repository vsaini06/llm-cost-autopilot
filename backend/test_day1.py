import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.table import Table
from providers import send_request
from models.registry import MODEL_REGISTRY

console = Console()

TEST_PROMPTS = [
    "What is the capital of France?",
    "Summarize the key differences between TCP and UDP in two sentences.",
    "Extract all numbers from this text: 'The project had 42 tasks, 7 were completed, and 3 are overdue.'",
    "Write a Python function that returns the nth Fibonacci number using recursion.",
    "Explain the concept of vector embeddings and why they are useful in machine learning.",
    "What are three pros and three cons of using microservices architecture?",
    "Translate this to Spanish: 'The meeting is scheduled for Monday at 3 PM.'",
    "Classify this review as positive, negative, or neutral: 'The product works fine but shipping took two weeks.'",
    "Given a list of integers, describe an algorithm to find all pairs that sum to a target value.",
    "Write a haiku about software debugging.",
]

MODEL_KEYS = ["gpt-4o", "gpt-4o-mini", "claude-sonnet", "claude-haiku", "llama3.2"]


async def test_model(model_key: str, prompt: str, prompt_idx: int):
    config = MODEL_REGISTRY[model_key]
    result = await send_request(prompt=prompt, model_key=model_key, max_tokens=256)
    return {
        "model": config.display_name,
        "prompt_idx": prompt_idx + 1,
        "success": result.success,
        "tokens_in": result.tokens_in,
        "tokens_out": result.tokens_out,
        "cost": result.cost,
        "latency_ms": result.latency_ms,
        "preview": result.output_text[:80].replace("\n", " ") if result.success else f"ERROR: {result.error}",
    }


async def run_all():
    console.print("\n[bold cyan]LLM Cost Autopilot — Day 1 Provider Test[/bold cyan]\n")
    console.print(f"Testing [bold]{len(MODEL_KEYS)}[/bold] models x [bold]{len(TEST_PROMPTS)}[/bold] prompts\n")

    tasks = [
        test_model(model_key, prompt, i)
        for model_key in MODEL_KEYS
        for i, prompt in enumerate(TEST_PROMPTS)
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    table = Table(title="Results", show_lines=True)
    table.add_column("Model", style="cyan", no_wrap=True)
    table.add_column("P#", justify="right")
    table.add_column("OK", justify="center")
    table.add_column("In", justify="right")
    table.add_column("Out", justify="right")
    table.add_column("Cost ($)", justify="right")
    table.add_column("ms", justify="right")
    table.add_column("Preview", max_width=55)

    total_cost = 0.0
    for r in results:
        if isinstance(r, Exception):
            console.print(f"[red]Exception: {r}[/red]")
            continue
        status = "[green]✓[/green]" if r["success"] else "[red]✗[/red]"
        table.add_row(
            r["model"],
            str(r["prompt_idx"]),
            status,
            str(r["tokens_in"]),
            str(r["tokens_out"]),
            f"{r['cost']:.6f}",
            str(r["latency_ms"]),
            r["preview"],
        )
        total_cost += r["cost"]

    console.print(table)

    cost_table = Table(title="Cost Rollup", show_lines=False)
    cost_table.add_column("Model", style="cyan")
    cost_table.add_column("Total Cost ($)", justify="right")
    cost_table.add_column("Avg Latency (ms)", justify="right")
    cost_table.add_column("Success Rate", justify="right")

    for model_key in MODEL_KEYS:
        model_results = [
            r for r in results
            if not isinstance(r, Exception)
            and r["model"] == MODEL_REGISTRY[model_key].display_name
        ]
        if not model_results:
            continue
        m_cost = sum(r["cost"] for r in model_results)
        m_latency = int(sum(r["latency_ms"] for r in model_results) / len(model_results))
        m_success = sum(1 for r in model_results if r["success"])
        cost_table.add_row(
            MODEL_REGISTRY[model_key].display_name,
            f"{m_cost:.6f}",
            str(m_latency),
            f"{m_success}/{len(model_results)}",
        )

    console.print(cost_table)

    gpt4o_hypothetical = sum(
        MODEL_REGISTRY["gpt-4o"].estimate_cost(r["tokens_in"], r["tokens_out"])
        for r in results
        if not isinstance(r, Exception) and r["success"]
    )
    console.print(f"\n[bold]Total cost:[/bold] [green]${total_cost:.6f}[/green]")
    console.print(f"[bold]Hypothetical all-GPT-4o cost:[/bold] [yellow]${gpt4o_hypothetical:.6f}[/yellow]")
    console.print(f"[bold]Savings potential:[/bold] [green]${gpt4o_hypothetical - total_cost:.6f}[/green]\n")


if __name__ == "__main__":
    asyncio.run(run_all())