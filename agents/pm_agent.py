"""
agents/pm_agent.py — The Product Manager Agent

ROLE: The PM Agent is the first agent to run in every project.
It takes the user's raw idea and turns it into:
  1. A structured PRD (Product Requirements Document)
  2. A list of Tickets for the other agents to work on

CONCEPT — Structured Outputs:
Instead of asking Claude to return free-form text, we give it
a Pydantic model (schema) and tell it: "respond ONLY in this
exact JSON shape." This is called structured output, and it's
critical for agent systems because downstream agents need
reliable, machine-readable data — not paragraphs of prose.

CONCEPT — System Prompt Engineering:
The system prompt defines the agent's persona, rules, and
output format. Good system prompts make agents predictable
and reliable.
"""

import json
import os
from anthropic import Anthropic
from pydantic import BaseModel, Field

from state.schema import ProjectState, PRD, Ticket


# ── Output schema for the PM Agent ───────────────────────────────────────────

class PMAgentOutput(BaseModel):
    """
    Structured output from the PM Agent.
    Claude must return EXACTLY this shape — no extra fields, no missing fields.
    """
    prd: PRD
    tickets: list[Ticket]
    reasoning: str = Field(
        description="Brief explanation of the PM's key decisions"
    )


# ── System prompt ─────────────────────────────────────────────────────────────

PM_SYSTEM_PROMPT = """You are an expert Product Manager at a top-tier software company.

Your job is to take a user's product idea and transform it into:
1. A clear, structured PRD (Product Requirements Document)
2. A prioritized list of engineering tickets for the dev team

GUIDELINES:
- Be specific and actionable — vague tickets are useless
- Think about MVP first — what's the smallest thing that delivers value?
- Assign tickets to the right agents:
    * backend_agent  → APIs, database, server logic
    * frontend_agent → UI components, pages, user interactions
    * devops_agent   → deployment, CI/CD, infrastructure
    * qa_agent       → test plans, test cases, quality checks
- Use ticket IDs like: TICKET-001, TICKET-002, etc.
- Keep ticket priorities realistic: not everything is "high"
- Out of scope = things explicitly NOT in v1 (helps the team focus)

IMPORTANT: Return your response as valid JSON matching the schema exactly.
"""


# ── The PM Agent function ─────────────────────────────────────────────────────

def run_pm_agent(state: ProjectState) -> dict:
    """
    The PM Agent node for LangGraph.

    CONCEPT — LangGraph nodes:
    In LangGraph, each agent is a "node" — a Python function that:
      - receives the current ProjectState
      - does its work (calls Claude, processes data, etc.)
      - returns a DICT with only the fields it wants to update

    LangGraph merges the returned dict back into the state automatically.
    You never return the full state — just what changed.

    Args:
        state: The current ProjectState (shared project brain)

    Returns:
        A dict with updated state fields (prd, tickets, log, current_step)
    """

    print("\n🧠 PM Agent is thinking...\n")

    # Initialize the Anthropic client
    # It automatically reads ANTHROPIC_API_KEY from your .env file
    client = Anthropic()
    model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

    # Build the user message — inject the user's request into the prompt
    user_message = f"""
Please create a PRD and engineering tickets for the following product idea:

"{state.user_request}"

Remember to think MVP-first. Break the work into clear, actionable tickets
assigned to the correct agents.
"""

    try:
        # ── Step 1: Call Claude with structured output ────────────────────────
        # We use tool_use to force Claude to return structured JSON.
        # This is the most reliable way to get structured outputs from Claude.

        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=PM_SYSTEM_PROMPT,
            tools=[
                {
                    "name": "submit_pm_output",
                    "description": "Submit the PRD and tickets you have created",
                    "input_schema": PMAgentOutput.model_json_schema(),
                }
            ],
            tool_choice={"type": "tool", "name": "submit_pm_output"},
            messages=[{"role": "user", "content": user_message}],
        )

        # ── Step 2: Extract the structured output ─────────────────────────────
        # Claude will always call our tool (because of tool_choice above)
        # The tool input IS our structured PMAgentOutput
        tool_use_block = next(
            block for block in response.content if block.type == "tool_use"
        )
        raw_output = tool_use_block.input

        # Parse and validate with Pydantic
        pm_output = PMAgentOutput(**raw_output)

        print(f"✅ PM Agent produced PRD: '{pm_output.prd.title}'")
        print(f"✅ Created {len(pm_output.tickets)} tickets\n")

        # ── Step 3: Return state updates ──────────────────────────────────────
        # Only return what changed — LangGraph merges this into the full state
        return {
            "prd": pm_output.prd,
            "tickets": pm_output.tickets,   # operator.add will append these
            "current_step": "pm_agent_done",
            "log": [
                f"[PM Agent] Created PRD: '{pm_output.prd.title}'",
                f"[PM Agent] Generated {len(pm_output.tickets)} tickets",
                f"[PM Agent] Reasoning: {pm_output.reasoning}",
            ],
        }

    except Exception as e:
        # If something goes wrong, log the error and don't crash the whole system
        error_msg = f"[PM Agent] Error: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "current_step": "pm_agent_error",
            "errors": [error_msg],
            "log": [error_msg],
        }
