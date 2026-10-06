"""FastAPI application for local AI safety reporting and Q&A."""

import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .analytics import compute_kpis, extract_violations
from .client import OllamaError, chat_with_ollama
from .prompts import build_daily_report_prompt, build_query_prompt

_log = logging.getLogger(__name__)

app = FastAPI(
    title="Smart Lab Safety – LLM Service",
    description="AI incident reporting and natural-language Q&A over safety data.",
    version="0.1.0",
)


class ReportRequest(BaseModel):
    """Request body containing the violations to summarize."""

    violations: list[Any] = Field(default_factory=list)


class QueryRequest(BaseModel):
    """Request body containing a question and its safety data."""

    query: str
    data: list[Any] | dict[str, Any] = Field(default_factory=list)


@app.get("/ping")
def ping() -> dict[str, str]:
    """Return service identity and health status."""
    return {"status": "ok", "service": "llm_service"}


@app.post("/generate_report")
def generate_report(payload: ReportRequest) -> dict[str, Any]:
    """Aggregate violation records and return a report or an offline fallback."""
    violations = extract_violations(payload.violations)
    kpis = compute_kpis(violations)

    if kpis["total"] == 0:
        return {
            "status": "ok",
            "report": "No violations were recorded in the supplied data.",
            "kpis": kpis,
        }

    try:
        report = chat_with_ollama(build_daily_report_prompt(kpis))
    except OllamaError as exc:
        _log.error("Ollama unavailable while generating report: %s", exc)
        return {
            "status": "fallback",
            "report": _unavailable_message(),
            "kpis": kpis,
        }

    return {"status": "ok", "report": report, "kpis": kpis}


@app.post("/answer_query")
def answer_query(payload: QueryRequest) -> dict[str, Any]:
    """Answer a question using aggregate metrics from the supplied data."""
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    violations = extract_violations(payload.data)
    kpis = compute_kpis(violations)
    try:
        answer = chat_with_ollama(build_query_prompt(query, kpis))
    except OllamaError as exc:
        _log.error("Ollama unavailable while answering query: %s", exc)
        return {
            "status": "fallback",
            "answer": _unavailable_message(),
            "kpis": kpis,
        }

    return {"status": "ok", "answer": answer, "kpis": kpis}


def _unavailable_message() -> str:
    """Return the stable client-facing Ollama outage message."""
    return "Ollama is unavailable; make sure Ollama is running and llama3.2 is pulled."
