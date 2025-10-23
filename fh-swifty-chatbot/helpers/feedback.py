from __future__ import annotations
import json, os, time
from typing import Any, Optional

FEEDBACK_PATH = os.environ.get("FEEDBACK_PATH", "feedback/feedback.json")

def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())

def save_feedback(
    *,
    kind: str,                    # "up" | "down"
    assistant_message_id: Optional[str],
    assistant_text: str,
    user_expected: Optional[str] = None,
    extra: Optional[dict[str, Any]] = None,
) -> None:
    rec: dict[str, Any] = {
        "ts": _now_iso(),
        "kind": kind,
        "assistant_message_id": assistant_message_id,
        "assistant_text": assistant_text,
        "user_expected": user_expected
    }
    if extra:
        rec.update(extra)

    os.makedirs(os.path.dirname(FEEDBACK_PATH) or ".", exist_ok=True)
    with open(FEEDBACK_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
