"""LLM Service – FastAPI application for AI-powered safety reporting.

Exposes /ping, /generate_report, and /answer_query endpoints.
Runs on port 8001 alongside the main backend API (port 8000).
"""

from fastapi import FastAPI

app = FastAPI(
    title="Smart Lab Safety – LLM Service",
    description="AI incident reporting and natural-language Q&A over safety data.",
    version="0.1.0",
)


@app.get("/ping")
def ping() -> dict:
    """Health-check endpoint. Returns service identity and status."""
    return {"status": "ok", "service": "llm_service"}
