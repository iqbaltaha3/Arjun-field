"""Groq-powered field-report extraction for Arjun Field."""

import json
import time
import requests

from config import LLM_PROVIDER, LLM_MODEL, LLM_API_KEY, LLM_BASE_URL

SYSTEM = """You extract factual field-operation observations from a worker's note.
Do not infer motives, political preferences, demographic traits, persuasion targets,
voter sentiment, or other unstated characteristics. Return only the requested JSON
fields. Preserve uncertainty using words such as approximately. Never invent facts.
The activity_type must be one of: meeting, visit, logistics, event, training, other.
"""

RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}
DEFAULT_GROQ_BASE_URL = "https://api.groq.com/openai/v1"

FIELD_REPORT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "activity_type": {
            "type": "string",
            "enum": ["meeting", "visit", "logistics", "event", "training", "other"],
        },
        "observation": {"type": "string"},
        "attendance_estimate": {"type": ["integer", "null"]},
        "follow_up": {"type": "string"},
    },
    "required": [
        "activity_type",
        "observation",
        "attendance_estimate",
        "follow_up",
    ],
}


def _post_with_retry(url, *, headers, json_body, timeout=60):
    """POST with retries for transient Groq/API failures."""
    last_error = None

    for attempt in range(4):
        try:
            response = requests.post(
                url,
                headers=headers,
                json=json_body,
                timeout=timeout,
            )

            if response.status_code not in RETRYABLE_STATUS:
                response.raise_for_status()
                return response

            last_error = requests.HTTPError(
                f"HTTP {response.status_code} from Groq: {response.text[:500]}",
                response=response,
            )

        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as exc:
            last_error = exc

        if attempt < 3:
            time.sleep(1.5 * (2 ** attempt))

    raise last_error or RuntimeError("Groq request failed.")


def _groq_request(text: str) -> str:
    if not LLM_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured in .env.")

    base_url = LLM_BASE_URL or DEFAULT_GROQ_BASE_URL
    url = base_url.rstrip("/") + "/chat/completions"

    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    body = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": text},
        ],
        # Groq supports JSON Object Mode and Structured Outputs on current
        # GPT-OSS models. A strict schema prevents malformed field reports.
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "arjun_field_report",
                "strict": True,
                "schema": FIELD_REPORT_SCHEMA,
            },
        },
        # Keep extraction latency/cost lower than a high-reasoning request.
        "reasoning_effort": "low",
        "temperature": 0,
    }

    try:
        response = _post_with_retry(
            url,
            headers=headers,
            json_body=body,
            timeout=60,
        )
    except requests.HTTPError as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)

        if status == 401:
            raise RuntimeError("Groq authentication failed. Check GROQ_API_KEY.") from exc
        if status == 403:
            raise RuntimeError("Groq rejected the request. Check your Groq project/API key permissions.") from exc
        if status == 429:
            raise RuntimeError("Groq rate limit reached. Please retry in a moment.") from exc
        if status in {500, 502, 503, 504}:
            raise RuntimeError("Groq is temporarily unavailable. Please retry in a moment.") from exc
        raise RuntimeError(f"Groq request failed (HTTP {status or 'unknown'}).") from exc
    except requests.ConnectionError as exc:
        raise RuntimeError("Arjun could not reach Groq. Check the internet connection and retry.") from exc
    except requests.Timeout as exc:
        raise RuntimeError("Groq took too long to respond. Please retry.") from exc

    try:
        payload = response.json()
        return payload["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Groq returned an unexpected response.") from exc


def extract(text: str):
    """Turn a transcript/typed field note into the controlled report structure."""
    cleaned = (text or "").strip()
    if not cleaned:
        raise ValueError("Empty field note.")

    # Keep the existing safe fallback behavior when no LLM key is configured.
    if not LLM_API_KEY and LLM_PROVIDER != "ollama":
        return {
            "activity_type": "other",
            "observation": cleaned,
            "attendance_estimate": None,
            "follow_up": "",
        }

    provider = (LLM_PROVIDER or "groq").lower()
    if provider != "groq":
        raise RuntimeError(
            f"Arjun Field is configured for Groq, but LLM_PROVIDER='{provider}'. "
            "Set LLM_PROVIDER=groq in .env."
        )

    raw = _groq_request(cleaned)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Groq returned invalid JSON for the field report.") from exc

    attendance = data.get("attendance_estimate")
    if attendance in ("", None):
        attendance = None
    else:
        try:
            attendance = int(attendance)
        except (TypeError, ValueError):
            attendance = None

    activity = str(data.get("activity_type") or "other").strip().lower()
    allowed = {"meeting", "visit", "logistics", "event", "training", "other"}
    if activity not in allowed:
        activity = "other"

    return {
        "activity_type": activity,
        "observation": str(data.get("observation") or cleaned)[:4000],
        "attendance_estimate": attendance,
        "follow_up": str(data.get("follow_up") or "")[:1000],
    }