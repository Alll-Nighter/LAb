"""Prompt templates for the LLM Service.

Builds structured (system + user) message payloads for Ollama chat completions.
Strictly grounds the LLM on provided safety KPIs to prevent hallucinated numbers.
"""

import json


def _format_kpis_for_prompt(kpis: dict) -> str:
    """Format KPI dictionary into a clean, human-readable JSON string."""
    return json.dumps(kpis, indent=2)


def build_daily_report_prompt(kpis: dict) -> list[dict]:
    """Build system and user messages for daily safety report generation.

    The model is instructed to write a concise 5-7 line plain-language summary
    covering:
    - Total violations count
    - Most violated zone (top_zone)
    - Most common violation type (top_type)
    - Peak violation hour window (peak_hour)
    - Repeat violators summary
    - Exactly one actionable, practical safety recommendation

    Args:
        kpis: Aggregated metrics dictionary from compute_kpis().

    Returns:
        List of message dicts with "role" and "content".
    """
    system_message = (
        "You are an expert industrial safety officer and compliance analyst in an engineering lab.\n"
        "Your task is to generate a concise, professional daily safety incident report from the provided KPI metrics.\n\n"
        "Strict Guidelines:\n"
        "1. Rely ONLY on the provided KPI metrics. Do NOT invent, assume, or hallucinate any numbers or facts.\n"
        "2. Write 5 to 7 short lines of clear, plain language. Put each line on a separate line using a newline.\n"
        "3. Explicitly state: total violations, top violated zone, most common violation type, peak hour, and repeat violators.\n"
        "4. Conclude with exactly ONE practical, actionable safety recommendation based on the top violation or zone.\n"
        "5. Do not include markdown headers or greetings; output the summary lines directly."
    )

    kpi_text = _format_kpis_for_prompt(kpis)
    total = kpis.get("total", 0)
    if total == 0:
        user_message = (
            "Generate the daily safety report for the following lab safety metrics "
            "(0 violations recorded):\n\n"
            f"{kpi_text}"
        )
    else:
        user_message = (
            f"Generate the daily safety report for the following lab safety metrics "
            f"({total} violations recorded):\n\n"
            f"{kpi_text}"
        )

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


def build_query_prompt(query: str, kpis: dict) -> list[dict]:
    """Build system and user messages for natural-language Q&A over safety data.

    The model is instructed to answer user questions using only the provided
    metrics. If the data does not contain the answer, it must explicitly state:
    "I don't have that information in the provided safety data."

    Args:
        query: The user's natural language question.
        kpis: Aggregated metrics dictionary from compute_kpis().

    Returns:
        List of message dicts with "role" and "content".
    """
    system_message = (
        "You are an AI safety assistant analyzing lab safety compliance data.\n"
        "Your job is to answer the user's question accurately using ONLY the provided KPI data.\n\n"
        "Strict Guidelines:\n"
        "1. Answer based strictly on the provided KPI metrics. Never fabricate data or extrapolate beyond what is given.\n"
        "2. If the data does not contain sufficient information to answer the question, reply with:\n"
        '   "I don\'t have that information in the provided safety data."\n'
        "3. Be concise, direct, and factual."
    )

    kpi_text = _format_kpis_for_prompt(kpis)
    user_message = (
        f"Lab Safety KPI Data:\n{kpi_text}\n\n"
        f"User Question: {query}\n\n"
        f"Answer using ONLY the data above. Do not invent numbers or facts. "
        f"If the data cannot answer the question, respond with: "
        f'"I don\'t have that information in the provided safety data."'
    )

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]
