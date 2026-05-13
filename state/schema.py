"""
state/schema.py — The shared "project brain"

CONCEPT: In LangGraph, all agents share a single State object.
Think of it as a whiteboard every agent can read and write to.
Each agent picks up where the last one left off.

As we add more agents (Architect, Backend, QA...), we'll add
more fields to this state.
"""

from typing import Annotated, Optional
from pydantic import BaseModel, Field
import operator


# ── Ticket model ─────────────────────────────────────────────────────────────

class Ticket(BaseModel):
    """A single work item, like a Jira ticket."""

    id: str = Field(description="Unique ticket ID, e.g. TICKET-001")
    title: str = Field(description="Short title of the task")
    description: str = Field(description="What needs to be built or done")
    assigned_to: str = Field(
        description="Which agent should handle this: backend_agent, frontend_agent, etc."
    )
    priority: str = Field(
        default="medium",
        description="Priority level: high | medium | low"
    )
    status: str = Field(
        default="open",
        description="Current status: open | in_progress | done"
    )


# ── PRD model ─────────────────────────────────────────────────────────────────

class PRD(BaseModel):
    """Product Requirements Document — the blueprint for what we're building."""

    title: str = Field(description="Name of the product/feature")
    problem_statement: str = Field(description="What problem does this solve?")
    target_users: str = Field(description="Who are we building this for?")
    core_features: list[str] = Field(description="List of key features to build")
    out_of_scope: list[str] = Field(description="Things we are NOT building now")
    success_metrics: list[str] = Field(description="How do we know this is successful?")
    tech_stack: list[str] = Field(description="Recommended technologies")


# ── Main Project State ────────────────────────────────────────────────────────

class ProjectState(BaseModel):
    """
    The central state object shared across all agents.

    LangGraph passes this between nodes (agents). Each agent
    receives the current state, does its work, and returns
    an updated state.

    Annotated[list, operator.add] means lists are MERGED
    rather than replaced — so each agent can append to tickets
    without overwriting another agent's work.
    """

    # The original user request — set once at the start
    user_request: str = Field(
        default="",
        description="The raw user prompt, e.g. 'Build a Stripe subscription dashboard'"
    )

    # PM Agent outputs
    prd: Optional[PRD] = Field(
        default=None,
        description="The Product Requirements Document created by the PM Agent"
    )

    tickets: Annotated[list[Ticket], operator.add] = Field(
        default_factory=list,
        description="Work tickets created by agents — lists are merged, not replaced"
    )

    # Execution log — agents append messages here as they work
    log: Annotated[list[str], operator.add] = Field(
        default_factory=list,
        description="Running log of what each agent has done"
    )

    # Which step we're on (useful for debugging)
    current_step: str = Field(
        default="start",
        description="Which agent/step is currently running"
    )

    # Error tracking
    errors: Annotated[list[str], operator.add] = Field(
        default_factory=list,
        description="Any errors encountered during execution"
    )
