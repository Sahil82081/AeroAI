"""
Structured Audit Logger for the AeroAI Unified AI Agent.

Logs every agent interaction:
- User request
- Selected tools
- Tool execution parameters, timings, and status
- Failures and error context
- Final response generation summary

Security:
- Automatically scrubs sensitive data (API keys, passwords, bearer tokens, secrets).
"""

import re
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pathlib import Path
from collections import deque

from app.core.logger import logger

# Regex patterns for sensitive information redaction
SENSITIVE_PATTERNS = [
    re.compile(r'(?i)(api[_-]?key|token|secret|password|auth|bearer)\s*[:=]\s*["\']?([^"\'\s,;]+)["\']?'),
    re.compile(r'(?i)bearer\s+[a-zA-Z0-9_\-\.]{10,}'),
    re.compile(r'(?i)AIza[0-9A-Za-z-_]{35}'),  # Google API key format
    re.compile(r'(?i)sk-[a-zA-Z0-9]{20,}'),     # OpenAI / standard key format
]

LOGS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "logs"
AUDIT_LOG_FILE = LOGS_DIR / "agent_audit.jsonl"


def scrub_sensitive_text(val: Any) -> Any:
    """Recursively traverses strings, dicts, and lists to redact sensitive data."""
    if isinstance(val, str):
        scrubbed = val
        for pat in SENSITIVE_PATTERNS:
            def _repl(m):
                if m.lastindex and m.lastindex >= 1:
                    return f"{m.group(1)}: [REDACTED]"
                return "[REDACTED]"
            scrubbed = pat.sub(_repl, scrubbed)
        return scrubbed
    elif isinstance(val, dict):
        new_dict = {}
        for k, v in val.items():
            if any(s in k.lower() for s in ["key", "secret", "token", "password", "auth"]):
                new_dict[k] = "[REDACTED]"
            else:
                new_dict[k] = scrub_sensitive_text(v)
        return new_dict
    elif isinstance(val, list):
        return [scrub_sensitive_text(item) for item in val]
    return val


class AgentAuditLogger:
    """Audit logger capturing structured agent traces and scrubbing secrets."""

    def __init__(self, max_in_memory: int = 100):
        self._history: deque = deque(maxlen=max_in_memory)
        self._ensure_log_file()

    def _ensure_log_file(self):
        try:
            LOGS_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not create agent audit log directory {LOGS_DIR}: {e}")

    def log_interaction(
        self,
        user_request: str,
        selected_tools: List[str],
        tool_executions: List[Dict[str, Any]],
        failures: List[Dict[str, Any]],
        response_summary: str,
        execution_duration_ms: float,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates and stores a sanitized audit trace for an agent interaction.
        """
        trace_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        sanitized_request = scrub_sensitive_text(user_request)
        sanitized_executions = scrub_sensitive_text(tool_executions)
        sanitized_failures = scrub_sensitive_text(failures)
        sanitized_summary = scrub_sensitive_text(response_summary)

        audit_entry = {
            "trace_id": trace_id,
            "session_id": session_id or "default",
            "timestamp": timestamp,
            "user_request": sanitized_request,
            "selected_tools": selected_tools,
            "tool_executions": sanitized_executions,
            "failures": sanitized_failures,
            "failure_count": len(failures),
            "final_response_summary": sanitized_summary[:300],
            "execution_duration_ms": round(execution_duration_ms, 2)
        }

        # Store in-memory
        self._history.append(audit_entry)

        # Log via standard logging
        logger.info(
            f"[AgentAudit] Trace={trace_id[:8]} | Tools={selected_tools} | "
            f"Failures={len(failures)} | Duration={execution_duration_ms:.1f}ms | "
            f"Query='{sanitized_request[:60]}...'"
        )

        # Append to persistent JSONL file
        try:
            with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(audit_entry) + "\n")
        except Exception as e:
            logger.warning(f"Could not write to audit log file {AUDIT_LOG_FILE}: {e}")

        return audit_entry

    def get_recent_traces(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Returns recent sanitized traces from memory."""
        items = list(self._history)
        return items[-limit:][::-1]


# Singleton audit logger
agent_audit_logger = AgentAuditLogger()
