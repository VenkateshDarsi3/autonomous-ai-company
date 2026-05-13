"""
main.py — Entry point for the Autonomous AI Software Company

HOW TO RUN:
    python main.py
    python main.py "Build a Twitter clone with real-time feeds"
    python main.py "Create a recipe recommendation app"

SETUP (one time):
    pip install -r requirements.txt
    cp .env.example .env
    # Edit .env and add your ANTHROPIC_API_KEY
"""

import sys
import os
import json

# Load environment variables from .env file BEFORE anything else
from dotenv import load_dotenv
load_dotenv()

# Rich = beautiful terminal output (colors, tables, panels)
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import print as rprint

from workflows.graph import workflow
from state.schema import ProjectState


console = Console()


# ── Pretty-print helpers ──────────────────────────────────────────────────────

def print_header():
    """Print the app banner."""
    console.print(Panel.fit(
        "[bold cyan]🏢 Autonomous AI Software Company[/bold cyan]\n"
        "[dim]A multi-agent system that builds software from requirements[/dim]",
        border_style="cyan"
    ))
    console.print()


def print_prd(prd):
    """Display the PRD in a readable format."""
    console.print(Panel(
        f"[bold]{prd.title}[/bold]\n\n"
        f"[yellow]Problem:[/yellow] {prd.problem_statement}\n\n"
        f"[yellow]Target Users:[/yellow] {prd.target_users}\n\n"
        f"[yellow]Core Features:[/yellow]\n"
        + "\n".join(f"  • {f}" for f in prd.core_features) + "\n\n"
        f"[yellow]Out of Scope (v1):[/yellow]\n"
        + "\n".join(f"  ✗ {f}" for f in prd.out_of_scope) + "\n\n"
        f"[yellow]Success Metrics:[/yellow]\n"
        + "\n".join(f"  ✓ {m}" for m in prd.success_metrics) + "\n\n"
        f"[yellow]Tech Stack:[/yellow] {', '.join(prd.tech_stack)}",
        title="📋 Product Requirements Document",
        border_style="green"
    ))


def print_tickets(tickets):
    """Display tickets as a table."""
    table = Table(title="🎫 Engineering Tickets", border_style="blue")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="white")
    table.add_column("Assigned To", style="yellow")
    table.add_column("Priority", style="magenta")
    table.add_column("Status", style="green")

    priority_colors = {"high": "red", "medium": "yellow", "low": "dim"}

    for ticket in tickets:
        color = priority_colors.get(ticket.priority, "white")
        table.add_row(
            ticket.id,
            ticket.title,
            ticket.assigned_to,
            f"[{color}]{ticket.priority}[/{color}]",
            ticket.status,
        )

    console.print(table)
    console.print()

    # Also print ticket descriptions
    console.print("[bold]Ticket Details:[/bold]")
    for ticket in tickets:
        console.print(Panel(
            ticket.description,
            title=f"[cyan]{ticket.id}[/cyan] — {ticket.title}",
            border_style="dim"
        ))


def print_log(log_entries):
    """Display the execution log."""
    console.print("\n[bold]📜 Execution Log:[/bold]")
    for entry in log_entries:
        console.print(f"  [dim]{entry}[/dim]")


# ── Main execution ────────────────────────────────────────────────────────────

def main():
    print_header()

    # Get the user request from CLI args, or prompt interactively
    if len(sys.argv) > 1:
        user_request = " ".join(sys.argv[1:])
    else:
        console.print("[bold]What do you want to build?[/bold]")
        console.print("[dim]Examples:[/dim]")
        console.print("  • Build a Stripe subscription dashboard")
        console.print("  • Create a Twitter clone with real-time feeds")
        console.print("  • Build a recipe recommendation app with AI")
        console.print()
        user_request = console.input("[bold cyan]Your idea: [/bold cyan]").strip()

        if not user_request:
            console.print("[red]No input provided. Exiting.[/red]")
            sys.exit(1)

    console.print(f"\n[bold]📌 User Request:[/bold] {user_request}\n")
    console.print("[dim]Starting the AI agent pipeline...[/dim]\n")

    # ── Run the multi-agent workflow ──────────────────────────────────────────
    # workflow.invoke() runs the LangGraph graph from START to END
    # It returns the final ProjectState as a dict
    try:
        final_state = workflow.invoke(
            {"user_request": user_request},
            # config can be used to set thread IDs for memory persistence later
            config={"configurable": {"thread_id": "project-1"}}
        )
    except Exception as e:
        console.print(f"\n[red]❌ Workflow failed: {e}[/red]")
        raise

    # ── Display results ───────────────────────────────────────────────────────
    console.rule("[bold green]✅ Pipeline Complete[/bold green]")
    console.print()

    if final_state.get("prd"):
        print_prd(final_state["prd"])
        console.print()

    if final_state.get("tickets"):
        print_tickets(final_state["tickets"])

    if final_state.get("log"):
        print_log(final_state["log"])

    if final_state.get("errors"):
        console.print("\n[red bold]⚠️  Errors:[/red bold]")
        for err in final_state["errors"]:
            console.print(f"  [red]{err}[/red]")

    console.print()
    console.print(Panel(
        "[bold green]Phase 1 complete![/bold green] 🎉\n\n"
        "The PM Agent has created your PRD and tickets.\n"
        "Next up: [cyan]Architect Agent[/cyan] will design the system architecture.",
        title="🚀 What's Next",
        border_style="green"
    ))


if __name__ == "__main__":
    main()
