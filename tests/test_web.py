import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import app_fastapi  # noqa: E402
import core  # noqa: E402


def test_chat_streams_events_and_rejects_bad_session_ids(monkeypatch):
    monkeypatch.setattr(
        core, "stream_reply", lambda messages, model=core.MODEL: iter([("content", "Hi there")])
    )
    monkeypatch.setattr(core, "save_session", lambda s: None)
    client = TestClient(app_fastapi.app)

    response = client.post("/api/chat", json={"message": "hello", "use_memory": False})
    events = [json.loads(line) for line in response.text.splitlines()]
    assert [e["type"] for e in events] == ["session", "content", "done"]
    assert events[-1]["left"] == core.MAX_QUESTIONS - 1

    assert client.get("/api/sessions/..%2Fsecret").status_code == 404
    assert client.get("/").status_code == 200
