"""UI-independent core for MYbot: streaming chat with Ollama and JSON session history.

Any front end (Streamlit, FastAPI, CLI) should only call the functions here.
"""

import json
import re
import uuid
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

import ollama

MODEL = "mybot"
HISTORY_DIR = Path(__file__).resolve().parent.parent / "history"


def stream_reply(messages: list[dict], model: str = MODEL) -> Iterator[tuple[str, str]]:
    """Yield ("thinking" | "content", text_fragment) as the model generates.

    `messages` holds only role/content dicts; thinking from earlier turns is not resent.
    """
    for chunk in ollama.chat(model=model, messages=messages, stream=True):
        if chunk.message.thinking:
            yield "thinking", chunk.message.thinking
        if chunk.message.content:
            yield "content", chunk.message.content


def new_session() -> dict:
    now = datetime.now()
    return {
        "id": f"{now:%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}",
        "model": MODEL,
        "created": now.isoformat(timespec="seconds"),
        "title": "New chat",
        "messages": [],  # {"role", "content", "thinking"?, "time"}
    }


def add_message(session: dict, role: str, content: str, thinking: str = "") -> None:
    now = datetime.now().isoformat(timespec="seconds")
    message = {"role": role, "content": content, "time": now}
    if thinking:
        message["thinking"] = thinking
    session["messages"].append(message)
    if role == "user" and session["title"] == "New chat":
        session["title"] = re.sub(r"\s+", " ", content).strip()[:60] or "New chat"


def model_messages(session: dict) -> list[dict]:
    return [{"role": m["role"], "content": m["content"]} for m in session["messages"]]


def save_session(session: dict, history_dir: Path = HISTORY_DIR) -> Path:
    history_dir.mkdir(parents=True, exist_ok=True)
    path = history_dir / f"{session['id']}.json"
    path.write_text(json.dumps(session, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_session(session_id: str, history_dir: Path = HISTORY_DIR) -> dict:
    return json.loads((history_dir / f"{session_id}.json").read_text(encoding="utf-8"))


def list_sessions(history_dir: Path = HISTORY_DIR) -> list[dict]:
    """Return summaries (id, title, created), newest first."""
    summaries = []
    for path in history_dir.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            summaries.append({"id": data["id"], "title": data["title"], "created": data["created"]})
        except (json.JSONDecodeError, KeyError):
            continue
    return sorted(summaries, key=lambda s: s["created"], reverse=True)
