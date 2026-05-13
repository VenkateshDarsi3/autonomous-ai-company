"""
workflows/graph.py — The LangGraph Workflow Engine

CONCEPT — What is LangGraph?
LangGraph is a framework for building multi-agent workflows as a graph:
  - NODES = agents (PM Agent, Architect Agent, etc.)
  - EDGES = the connections between them (who runs after who)
  - STATE = the shared ProjectState passed between all nodes

Think of it like a flowchart where each box is an AI agent.

HOW WE GROW THIS SYSTEM:
Right now we have 1 agent (PM). As we build more agents, we'll:
  1. Import the new agent function
  2. Add it as a node: graph.add_node("architect", run_architect_agent)
  3. Add an edge: graph.add_edge("pm_agent", "architect")
  4. That's it — LangGraph handles the rest!

CURRENT FLOW:
  START → pm_agent → END

FUTURE FLOW:
  START → pm_agent → architect → [backend, frontend] (parallel) → qa → reviewer → deploy → END
"""

from langgraph.graph import StateGraph, START, END

from state.schema import ProjectState
from agents.pm_agent import run_pm_agent


def build_workflow() -> StateGraph:
    """
    Build and compile the multi-agent workflow graph.

    Returns a compiled graph ready to be invoked with:
        graph.invoke({"user_request": "..."})
    """

    # ── Step 1: Create the graph with our state schema ────────────────────────
    # StateGraph knows about ProjectState, so it handles merging automatically
    graph = StateGraph(ProjectState)

    # ── Step 2: Register agents as nodes ─────────────────────────────────────
    # Each node gets a name and the function to call
    # (add more agents here as we build them)
    graph.add_node("pm_agent", run_pm_agent)

    # FUTURE agents to add here:
    # graph.add_node("architect", run_architect_agent)
    # graph.add_node("backend",   run_backend_agent)
    # graph.add_node("frontend",  run_frontend_agent)
    # graph.add_node("qa",        run_qa_agent)
    # graph.add_node("reviewer",  run_reviewer_agent)
    # graph.add_node("devops",    run_devops_agent)

    # ── Step 3: Connect the nodes with edges ──────────────────────────────────
    # START → pm_agent → END
    graph.add_edge(START, "pm_agent")
    graph.add_edge("pm_agent", END)

    # FUTURE edges (sequential):
    # graph.add_edge("pm_agent", "architect")
    # graph.add_edge("architect", "backend")
    # graph.add_edge("backend",   "qa")
    # ...

    # FUTURE parallel edges (backend + frontend at the same time):
    # from langgraph.graph import Send
    # graph.add_conditional_edges("architect", lambda s: ["backend", "frontend"])

    # ── Step 4: Compile the graph ─────────────────────────────────────────────
    # This validates the graph structure and returns a runnable object
    compiled = graph.compile()

    return compiled


# Create a single shared instance of the workflow
# Import this in main.py with: from workflows.graph import workflow
workflow = build_workflow()
