"""Unit tests for the LLM Service layer (prompts and client).

Uses unittest.mock to avoid network calls to Ollama.
"""

from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException

from llm_service.client import OllamaError, chat_with_ollama
from llm_service.main import QueryRequest, ReportRequest, answer_query, generate_report
from llm_service.prompts import build_daily_report_prompt, build_query_prompt


class TestPromptBuilders:
    """Tests for prompt construction in prompts.py."""

    def test_build_daily_report_prompt_returns_messages(self):
        """build_daily_report_prompt returns a list of two dicts (system + user)."""
        kpis = {
            "total": 5,
            "by_type": {"NO_HELMET": 3, "NO_VEST": 2},
            "by_zone": {"Workbench-1": 3, "Workbench-2": 2},
            "by_hour": {f"{h:02d}": 0 for h in range(24)},
            "top_type": "NO_HELMET",
            "top_zone": "Workbench-1",
            "peak_hour": "11:00-12:00",
            "repeat_violators": [{"track_id": 7, "count": 2}],
        }
        kpis["by_hour"]["11"] = 5

        messages = build_daily_report_prompt(kpis)

        assert isinstance(messages, list)
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "NO_HELMET" in messages[1]["content"]
        assert "Workbench-1" in messages[1]["content"]
        assert "11:00-12:00" in messages[1]["content"]
        assert "separate line using a newline" in messages[0]["content"]

    def test_build_daily_report_prompt_with_zero_violations(self):
        """Prompt handles zero-total KPIs without crashing."""
        kpis = {
            "total": 0,
            "by_type": {},
            "by_zone": {},
            "by_hour": {f"{h:02d}": 0 for h in range(24)},
            "top_type": None,
            "top_zone": None,
            "peak_hour": "00:00-01:00",
            "repeat_violators": [],
        }

        messages = build_daily_report_prompt(kpis)

        assert len(messages) == 2
        assert "0 violations" in messages[1]["content"].lower()

    def test_build_query_prompt_returns_messages(self):
        """build_query_prompt returns system + user messages containing query and KPIs."""
        kpis = {
            "total": 3,
            "by_type": {"NO_GLOVES": 3},
            "by_zone": {"Zone-A": 3},
            "by_hour": {f"{h:02d}": 0 for h in range(24)},
            "top_type": "NO_GLOVES",
            "top_zone": "Zone-A",
            "peak_hour": "14:00-15:00",
            "repeat_violators": [],
        }
        kpis["by_hour"]["14"] = 3

        messages = build_query_prompt("How many glove violations?", kpis)

        assert isinstance(messages, list)
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "How many glove violations?" in messages[1]["content"]
        assert "NO_GLOVES" in messages[1]["content"]

    def test_build_query_prompt_instructs_dont_invent(self):
        """Query prompt contains instruction to not invent numbers."""
        kpis = {
            "total": 1,
            "by_type": {"NO_HELMET": 1},
            "by_zone": {"Z": 1},
            "by_hour": {f"{h:02d}": 0 for h in range(24)},
            "top_type": "NO_HELMET",
            "top_zone": "Z",
            "peak_hour": "10:00-11:00",
            "repeat_violators": [],
        }
        kpis["by_hour"]["10"] = 1

        messages = build_query_prompt("Any data on shoes?", kpis)

        user_content = messages[1]["content"].lower()
        assert "don't" in user_content or "do not" in user_content
        assert "invent" in user_content or "make up" in user_content


class TestOllamaClient:
    """Tests for chat_with_ollama with mocked HTTP calls."""

    @patch("llm_service.client.requests.post")
    def test_chat_with_ollama_success(self, mock_post):
        """Successful Ollama response returns assistant content."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"message": {"content": "Test response"}}
        mock_post.return_value = mock_resp

        result = chat_with_ollama([{"role": "user", "content": "Hello"}])

        assert result == "Test response"
        mock_post.assert_called_once()

    @patch("llm_service.client.requests.post")
    def test_chat_with_ollama_connection_error(self, mock_post):
        """ConnectionError raises OllamaError with helpful message."""
        import requests

        mock_post.side_effect = requests.ConnectionError("Connection refused")

        with pytest.raises(OllamaError) as exc_info:
            chat_with_ollama([{"role": "user", "content": "Hello"}])

        assert "Cannot reach Ollama" in str(exc_info.value)
        assert "ollama serve" in str(exc_info.value)

    @patch("llm_service.client.requests.post")
    def test_chat_with_ollama_timeout(self, mock_post):
        """Timeout raises OllamaError with timeout info."""
        import requests

        mock_post.side_effect = requests.Timeout("Read timed out")

        with pytest.raises(OllamaError) as exc_info:
            chat_with_ollama([{"role": "user", "content": "Hello"}])

        assert "timed out" in str(exc_info.value).lower()

    @patch("llm_service.client.requests.post")
    def test_chat_with_ollama_http_error(self, mock_post):
        """Non-200 HTTP status raises OllamaError."""
        mock_resp = Mock()
        mock_resp.status_code = 500
        mock_resp.text = "Internal Server Error"
        mock_post.return_value = mock_resp

        with pytest.raises(OllamaError) as exc_info:
            chat_with_ollama([{"role": "user", "content": "Hello"}])

        assert "500" in str(exc_info.value)

    @patch("llm_service.client.requests.post")
    def test_chat_with_ollama_invalid_json(self, mock_post):
        """Invalid JSON response raises OllamaError."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.side_effect = ValueError("Expecting value")
        mock_resp.text = "not json"
        mock_post.return_value = mock_resp

        with pytest.raises(OllamaError) as exc_info:
            chat_with_ollama([{"role": "user", "content": "Hello"}])

        assert "invalid json" in str(exc_info.value).lower()

    @patch("llm_service.client.requests.post")
    def test_chat_with_ollama_empty_reply(self, mock_post):
        """Empty content in response raises OllamaError."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"message": {"content": ""}}
        mock_post.return_value = mock_resp

        with pytest.raises(OllamaError) as exc_info:
            chat_with_ollama([{"role": "user", "content": "Hello"}])

        assert "empty reply" in str(exc_info.value).lower()


class TestEndpoints:
    """Tests for HTTP request validation and endpoint response contracts."""

    @patch("llm_service.main.chat_with_ollama")
    def test_generate_report_zero_violations_skips_ollama(self, mock_chat):
        """An empty report request returns the fixed message without inference."""
        response = generate_report(ReportRequest(violations=[]))

        assert response["status"] == "ok"
        assert "No violations" in response["report"]
        assert response["kpis"]["total"] == 0
        mock_chat.assert_not_called()

    @patch("llm_service.main.chat_with_ollama", return_value="5 incidents summarized.")
    def test_generate_report_calls_llm_with_aggregates(self, mock_chat):
        """A non-empty report sends KPI prompts and returns the generated text."""
        records = [
            {
                "camera_id": 0,
                "zone": "Workbench-1",
                "track_id": 7,
                "violation_type": "NO_HELMET",
                "timestamp": "2026-10-01T11:42:10",
                "confidence": 0.87,
            }
        ]
        response = generate_report(ReportRequest(violations=records))

        assert response["report"] == "5 incidents summarized."
        assert response["kpis"]["by_type"] == {"NO_HELMET": 1}
        prompt = mock_chat.call_args.args[0]
        assert "Workbench-1" in prompt[1]["content"]
        assert "camera_id" not in prompt[1]["content"]

    @patch(
        "llm_service.main.chat_with_ollama",
        side_effect=OllamaError("connection refused"),
    )
    def test_generate_report_returns_fallback(self, mock_chat):
        """An Ollama outage degrades to the documented fallback response."""
        response = generate_report(
            ReportRequest(violations=[{"violation_type": "NO_HELMET"}])
        )

        assert response["status"] == "fallback"
        assert "make sure Ollama is running" in response["report"]
        mock_chat.assert_called_once()

    @patch("llm_service.main.chat_with_ollama", return_value="Two violations.")
    def test_answer_query_accepts_plain_list_data(self, mock_chat):
        """Query requests accept a direct violation list in the data field."""
        response = answer_query(
            QueryRequest(
                query="How many violations?",
                data=[{"violation_type": "NO_HELMET"}, {"zone": "A"}],
            )
        )

        assert response["answer"] == "Two violations."
        assert response["kpis"]["total"] == 2
        mock_chat.assert_called_once()

    @patch("llm_service.main.chat_with_ollama")
    def test_answer_query_rejects_blank_query(self, mock_chat):
        """Whitespace-only questions return HTTP 400 without inference."""
        request = QueryRequest(query="  ", data=[])

        with pytest.raises(HTTPException) as exc_info:
            answer_query(request)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Query cannot be empty"
        mock_chat.assert_not_called()

    @patch("llm_service.client.requests.post")
    def test_chat_with_ollama_missing_message_key(self, mock_post):
        """Missing 'message' key in response raises OllamaError."""
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"done": True}
        mock_post.return_value = mock_resp

        with pytest.raises(OllamaError) as exc_info:
            chat_with_ollama([{"role": "user", "content": "Hello"}])

        assert "empty reply" in str(exc_info.value).lower()
