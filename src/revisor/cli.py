"""Línea de comandos: `revisor review --diff-file x.diff` o `--repo owner/name --pr 12 --post`."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from langchain_ollama import ChatOllama

from .github import DEFAULT_AUTHORS, GitHubClient
from .graph import review_diff
from .models import LLMFindings


def build_llm():
    model = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b-instruct")
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    chat = ChatOllama(model=model, base_url=base_url, temperature=0)
    return chat.with_structured_output(LLMFindings)


def main(argv: list[str] | None = None) -> int:
    # El informe lleva emojis; en consolas Windows (cp1252) fallaría al imprimir.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="revisor")
    sub = parser.add_subparsers(dest="command", required=True)
    review = sub.add_parser("review", help="Revisa un diff y genera el informe")
    review.add_argument("--diff-file", type=Path, help="Diff unificado en un fichero")
    review.add_argument("--repo", help="owner/nombre del repositorio")
    review.add_argument("--pr", type=int, help="Número del pull request")
    review.add_argument("--post", action="store_true", help="Publica el informe en el PR")
    args = parser.parse_args(argv)

    github: GitHubClient | None = None
    if args.diff_file:
        diff_text = args.diff_file.read_text(encoding="utf-8")
    elif args.repo and args.pr:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            parser.error("Falta la variable de entorno GITHUB_TOKEN")
        authors = os.environ.get("REVISOR_COMMENT_AUTHORS")
        github = GitHubClient(
            token,
            args.repo,
            authors=[a.strip() for a in authors.split(",")] if authors else DEFAULT_AUTHORS,
        )
        diff_text = github.get_pr_diff(args.pr)
    else:
        parser.error("Indica --diff-file o bien --repo y --pr")

    report = review_diff(diff_text, build_llm())
    print(report)
    if args.post:
        if github is None or args.pr is None:
            parser.error("--post requiere --repo y --pr")
        github.upsert_comment(args.pr, report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
