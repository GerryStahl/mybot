"""FastAPI + HTML front end for MYbot.

Run: .venv/bin/uvicorn app_fastapi:app --app-dir src --port 8000   (then open http://localhost:8000)
The page is src/web/index.html; all chat logic lives in core.py.
"""

import json
import re
import sys
from collections.abc import Iterator
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core  # noqa: E402

WEB_DIR = Path(__file__).resolve().parent / "web"

app = FastAPI(title="MYbot")
sessions: dict[str, dict] = {}  # chats in use, by id; saved to history/ after each answer


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    user: str = core.DEFAULT_USER
    use_memory: bool = True
    use_library: bool = False


class UserRequest(BaseModel):
    name: str


def get_session(session_id: str | None, user: str) -> dict:
    if session_id and not re.fullmatch(r"[\w-]+", session_id):
        raise FileNotFoundError(session_id)  # ids become file names; reject anything else
    if session_id and session_id in sessions:
        return sessions[session_id]
    session = core.load_session(session_id) if session_id else core.new_session(user)
    session.setdefault("user", user)
    sessions[session["id"]] = session
    return session


def event(kind: str, **data) -> bytes:
    return (json.dumps({"type": kind, **data}, ensure_ascii=False) + "\n").encode()


def stream_chat(request: ChatRequest) -> Iterator[bytes]:
    """Newline-delimited JSON events: session, searched, thinking, content, done | error."""
    try:
        session = get_session(request.session_id, core.slug(request.user))
        session["user"] = core.slug(request.user)
        core.load_profile(session["user"])
        yield event("session", id=session["id"], title=session["title"])
        for kind, text in core.chat_turn(
            session, request.message, request.use_memory, request.use_library
        ):
            yield event(kind, text=text)
        last = session["messages"][-1]
        yield event(
            "done",
            title=session["title"],
            sources=last.get("sources", []),
            left=core.MAX_QUESTIONS - core.question_count(session),
        )
    except Exception as error:  # Ollama not running, model missing, chat full, ...
        yield event("error", message=str(error))


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/state")
def state() -> dict:
    core.load_profile(core.DEFAULT_USER)  # make sure there is at least one profile
    return {
        "model": core.MODEL,
        "users": core.list_users(),
        "default_user": core.DEFAULT_USER,
        "library_available": core.library_available(),
        "max_questions": core.MAX_QUESTIONS,
        "sessions": core.list_sessions(),
    }


@app.get("/api/sessions/{session_id}")
def read_session(session_id: str) -> dict:
    try:
        session = get_session(session_id, core.DEFAULT_USER)
    except FileNotFoundError:
        raise HTTPException(404, "No such chat") from None
    return {**session, "left": core.MAX_QUESTIONS - core.question_count(session)}


@app.post("/api/users")
def add_user(request: UserRequest) -> dict:
    name = core.slug(request.name)
    core.load_profile(name)  # creates an empty profile file to edit
    return {"name": name, "users": core.list_users()}


@app.post("/api/chat")
def chat(request: ChatRequest) -> StreamingResponse:
    return StreamingResponse(stream_chat(request), media_type="application/x-ndjson")
