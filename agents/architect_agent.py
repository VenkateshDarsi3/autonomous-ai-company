"""
agents/architect_agent.py — The Architect Agent

ROLE: The Architect Agent runs after the PM Agent.
It reads the PRD and tickets and produces a detailed
system architecture — the technical blueprint that
Backend and Frontend agents will follow when writing code.

CONCEPT — Context Engineering:
Notice how we pass the PM's PRD and tickets directly
into the Architect's prompt. This is called "context
engineering" — giving the agent exactly the right
information it needs, in the right format.

A bad prompt: "Design a system architecture."
A good prompt: "Here is the PRD: {...} and these tickets: {...}
               Design an architecture that satisfies all requirements."

The richer the context, the smarter the output.
"""

import os
from anthropic import Anthropic

from state.schema import ProjectState, Architecture, APIEndpoint, DatabaseTable


# ── Output schema ─────────────────────────────────────────────────────────────

class ArchitectAgentOutput(Architecture):
    """
    The Architect Agent outputs an Architecture object directly.
    We inherit from Architecture so we reuse the same schema.
    """
    reasoning: str = "Architecture designed based on PRD requirements"


# ── System prompt ─────────────────────────────────────────────────────────────

ARCHITECT_SYSTEM_PROMPT = """You are a Senior Software Architect at a top-tier tech company.

Your job is to take a Product Requirements Document (PRD) and engineering tickets,
and design a complete, production-ready system architecture.

YOUR DELIVERABLES:
1. Database Schema — every table needed, with columns and relationships
2. API Endpoints — every REST endpoint, with method, path, auth, request/response
3. Folder Structure — the exact file/folder layout for the codebase
4. Key Decisions — explain important architectural choices (why this pattern, why this library)
5. Dependencies — all packages/libraries needed

GUIDELINES:
- Be specific — Backend and Frontend agents will BUILD from your output
- Design for the MVP described in the PRD — not over-engineered
- Use industry-standard patterns (RESTful APIs, MVC/layered architecture)
- Every API endpoint that modifies data must require authentication
- Include proper indexing hints in database columns
- Folder structure should separate concerns clearly (controllers, models, routes, services)

IMPORTANT: Return your response as valid JSON matching the schema exactly.
"""


# ── The Architect Agent function ──────────────────────────────────────────────

def run_architect_agent(state: ProjectState) -> dict:
    """
    The Architect Agent node for LangGraph.

    Reads the PM Agent's PRD and tickets from the state,
    then designs the full system architecture.

    Args:
        state: Current ProjectState (contains prd + tickets from PM Agent)

    Returns:
        Dict with updated state fields (architecture, log, current_step)
    """

    print("\n🏗️  Architect Agent is designing the system...\n")

    # Safety check — if PM Agent didn't produce a PRD, we can't proceed
    if not state.prd:
        error = "[Architect Agent] Cannot proceed — no PRD found in state. PM Agent must run first."
        print(f"❌ {error}")
        return {
            "current_step": "architect_agent_error",
            "errors": [error],
            "log": [error],
        }

    client = Anthropic()
    model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

    # ── Build context-rich prompt ─────────────────────────────────────────────
    # We format the PRD and tickets into a readable structure for Claude.
    # This is context engineering — the more structured the input,
    # the more structured and reliable the output.

    prd = state.prd
    tickets_summary = "\n".join([
        f"  - [{t.assigned_to}] {t.id}: {t.title} (priority: {t.priority})"
        for t in state.tickets
    ])

    user_message = f"""
Please design the complete system architecture for this product.

## Product Requirements Document
**Title:** {prd.title}
**Problem:** {prd.problem_statement}
**Target Users:** {prd.target_users}
**Tech Stack:** {", ".join(prd.tech_stack)}

**Core Features:**
{chr(10).join(f"  - {f}" for f in prd.core_features)}

**Out of Scope:**
{chr(10).join(f"  - {f}" for f in prd.out_of_scope)}

## Engineering Tickets to Address
{tickets_summary}

Design an architecture that satisfies ALL the above requirements.
Make it production-ready but appropriate for an MVP.
"""

    try:
        # ── Call Claude with structured output ────────────────────────────────
        response = client.messages.create(
            model=model,
            max_tokens=8192,   # Architect needs more tokens — architecture is detailed
            system=ARCHITECT_SYSTEM_PROMPT,
            tools=[
                {
                    "name": "submit_architecture",
                    "description": "Submit the complete system architecture you have designed",
                    "input_schema": ArchitectAgentOutput.model_json_schema(),
                }
            ],
            tool_choice={"type": "tool", "name": "submit_architecture"},
            messages=[{"role": "user", "content": user_message}],
        )

        # ── Extract structured output ─────────────────────────────────────────
        tool_use_block = next(
            block for block in response.content if block.type == "tool_use"
        )
        raw_output = tool_use_block.input
        arch_output = ArchitectAgentOutput(**raw_output)

        print(f"✅ Architect designed {len(arch_output.database_tables)} database tables")
        print(f"✅ Defined {len(arch_output.api_endpoints)} API endpoints")
        print(f"✅ Planned {len(arch_output.folder_structure)} files in folder structure\n")

        # ── Return state updates ──────────────────────────────────────────────
        return {
            "architecture": Architecture(**arch_output.model_dump(exclude={"reasoning"})),
            "current_step": "architect_agent_done",
            "log": [
                f"[Architect Agent] Designed {len(arch_output.database_tables)} database tables",
                f"[Architect Agent] Defined {len(arch_output.api_endpoints)} API endpoints",
                f"[Architect Agent] Planned folder structure with {len(arch_output.folder_structure)} entries",
                f"[Architect Agent] Key decisions: {len(arch_output.key_decisions)} recorded",
            ],
        }

    except Exception as e:
        error_msg = f"[Architect Agent] Error: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "current_step": "architect_agent_error",
            "errors": [error_msg],
            "log": [error_msg],
        }
