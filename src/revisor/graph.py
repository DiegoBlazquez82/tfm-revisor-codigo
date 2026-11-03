"""Grafo LangGraph: tres agentes en paralelo y un agregador."""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, START, StateGraph

from .agents import StructuredLLM, build_agents, render_diff
from .diff import ChangedFile, parse_diff
from .models import Finding
from .report import aggregate, render_markdown


class ReviewState(TypedDict, total=False):
    files: list[ChangedFile]
    findings: Annotated[list[Finding], operator.add]
    errors: Annotated[list[str], operator.add]
    report: str


def build_graph(llm: StructuredLLM):
    agents = build_agents(llm)

    def aggregator(state: ReviewState) -> dict[str, Any]:
        files = state["files"]
        _, omitted = render_diff(files)
        merged = aggregate(state.get("findings", []))
        return {
            "report": render_markdown(merged, len(files), omitted, state.get("errors", [])),
        }

    graph = StateGraph(ReviewState)
    for name, node in agents.items():
        graph.add_node(name, node)
        graph.add_edge(START, name)
    graph.add_node("aggregate", aggregator)
    graph.add_edge(list(agents), "aggregate")
    graph.add_edge("aggregate", END)
    return graph.compile()


def review_state(diff_text: str, llm: StructuredLLM) -> dict[str, Any]:
    """Ejecuta el grafo y devuelve el estado final (hallazgos crudos, errores e informe)."""
    files = parse_diff(diff_text)
    if not files:
        return {"files": [], "findings": [], "errors": [], "report": render_markdown([], 0)}
    return build_graph(llm).invoke({"files": files, "findings": [], "errors": []})


def review_diff(diff_text: str, llm: StructuredLLM) -> str:
    """Devuelve el comentario en Markdown para un diff unificado."""
    return review_state(diff_text, llm)["report"]
