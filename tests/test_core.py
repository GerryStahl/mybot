import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import core  # noqa: E402


def test_session_roundtrip_keeps_thinking(tmp_path):
    session = core.new_session()
    core.add_message(session, "user", "  What is\n a mixture of experts?  ")
    core.add_message(session, "assistant", "A routed network.", thinking="Let me think.")
    core.save_session(session, tmp_path)

    loaded = core.load_session(session["id"], tmp_path)
    assert loaded["title"] == "What is a mixture of experts?"
    assert loaded["messages"][1]["thinking"] == "Let me think."
    assert core.list_sessions(tmp_path)[0]["id"] == session["id"]


def test_model_messages_drops_thinking_and_time():
    session = core.new_session()
    core.add_message(session, "user", "hi")
    core.add_message(session, "assistant", "hello", thinking="hmm")
    assert core.model_messages(session) == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]
