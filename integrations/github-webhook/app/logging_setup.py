"""Day 20: structured (JSON) logging.

Every log line becomes one JSON object, for example:
  {"ts": "2026-10-30T11:02:03.123Z", "level": "INFO", "logger": "github-webhook",
   "msg": "PR #42 opened ...", "delivery_id": "abc-1", "event": "pull_request"}

Log tools (CloudWatch, Datadog, Splunk) can then filter on fields: delivery_id = "abc-1".
The delivery ID is attached automatically to every line logged while handling that request.
"""

import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime

# "Context variables": values that belong to the current request only.
delivery_id_var: ContextVar[str] = ContextVar("delivery_id", default="")
event_var: ContextVar[str] = ContextVar("event", default="")

_STANDARD_ATTRS = set(vars(logging.makeLogRecord({}))) | {"message", "asctime"}
_base_factory = logging.getLogRecordFactory()


def _record_factory(*args, **kwargs) -> logging.LogRecord:
    """Stamp the current request's delivery ID and event onto every log record when it is created."""
    record = _base_factory(*args, **kwargs)
    record.delivery_id = delivery_id_var.get()
    record.event = event_var.get()
    return record


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # delivery_id, event and anything passed as extra={...} become top-level fields
        for key, value in vars(record).items():
            if key not in _STANDARD_ATTRS and not key.startswith("_") and value not in ("", None):
                entry[key] = value
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str, ensure_ascii=False)


def setup_logging(level: str = "INFO", fmt: str = "json") -> None:
    """Configure the root logger once. fmt="text" keeps the old human-friendly lines."""
    logging.setLogRecordFactory(_record_factory)
    handler = logging.StreamHandler()
    if fmt == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
    logging.getLogger("httpx").setLevel(logging.WARNING)  # keep library noise down
