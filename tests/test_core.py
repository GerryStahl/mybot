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


def _chat(history_dir, title, created, reply="ok", thinking=""):
    session = core.new_session()
    session["created"] = created
    core.add_message(session, "user", title)
    core.add_message(session, "assistant", reply, thinking=thinking)
    core.save_session(session, history_dir)
    return session


def test_recall_skips_current_orders_newest_first_and_includes_thinking(tmp_path):
    old = _chat(tmp_path, "old topic", "2026-01-01T10:00:00")
    new = _chat(tmp_path, "new topic", "2026-02-01T10:00:00", thinking="pondering " * 100)
    current = _chat(tmp_path, "current topic", "2026-03-01T10:00:00")

    text = core.recall_sessions(current["id"], tmp_path, max_thinking=20)
    assert "current topic" not in text
    assert text.index("new topic") < text.index("old topic")
    assert "(thinking) pondering" in text and "pondering " * 5 not in text
    assert old["id"] != new["id"]


def test_recall_respects_char_budget(tmp_path):
    for i in range(5):
        _chat(tmp_path, f"topic {i}", f"2026-01-0{i + 1}T10:00:00", reply="x" * 500)
    assert len(core.recall_sessions("none", tmp_path, max_chars=700)) <= 700


def test_system_prompt_combines_identity_profile_self_and_memory(tmp_path):
    modelfile = tmp_path / "Modelfile"
    modelfile.write_text('FROM x\nSYSTEM """You are MYbot."""\n')
    memory, personality, history = tmp_path / "memory", tmp_path / "personality", tmp_path / "h"
    (memory / "profiles").mkdir(parents=True)
    (memory / "profiles" / "Ann.json").write_text('{"interests": ["Go", "chess"]}')
    _chat(history, "earlier question", "2026-01-01T10:00:00")

    session = core.new_session("Ann")
    prompt = core.build_system_prompt(session, history, memory, personality, modelfile)

    assert prompt.startswith("You are MYbot.")
    assert "(Ann)" in prompt and "interests: Go, chess" in prompt
    assert "earlier question" in prompt
    assert (personality / "self.json").exists()  # default self-model is created for editing
    assert core.list_users(memory) == ["Ann"]


def test_model_messages_prepends_system_only_when_given():
    session = core.new_session()
    core.add_message(session, "user", "hi")
    assert core.model_messages(session, "ctx")[0] == {"role": "system", "content": "ctx"}
    assert core.model_messages(session)[0]["role"] == "user"


def test_library_context_numbers_passages_and_lists_sources():
    results = [
        {
            "cite": "(Stahl, 2026, p. 3)",
            "title": "Group Cognition",
            "reference": "Stahl, G. (2026). Group Cognition.",
            "passages": [{"cite": "(Stahl, 2026, p. 3)", "text": "Groups can think."}],
            "note": "Search note: x",
        }
    ]
    context = core.format_library_context(results)
    assert "[1] (Stahl, 2026, p. 3) - Stahl, G. (2026). Group Cognition." in context
    assert "Groups can think." in context and "Search note: x" in context
    assert core.library_sources(results) == ["(Stahl, 2026, p. 3) Group Cognition"]
    assert core.format_library_context([]) == ""


def test_system_prompt_without_memory_keeps_identity_and_library(tmp_path):
    modelfile = tmp_path / "Modelfile"
    modelfile.write_text('SYSTEM """You are MYbot."""\n')
    prompt = core.build_system_prompt(
        core.new_session(), tmp_path, tmp_path, tmp_path, modelfile, library="LIB", memory=False
    )
    assert prompt == "You are MYbot.\n\nLIB"


def test_sources_are_saved_on_the_message_only_when_given():
    session = core.new_session()
    core.add_message(session, "assistant", "a", sources=["(Stahl, 2026) X"])
    core.add_message(session, "assistant", "b")
    assert session["messages"][0]["sources"] == ["(Stahl, 2026) X"]
    assert "sources" not in session["messages"][1]


def _fake_turn(monkeypatch, fail=False):
    """Replace Ollama and the library search; return the prompts and queries they received."""
    seen = {"messages": [], "queries": []}

    def fake_stream(messages, model=core.MODEL):
        seen["messages"].append(messages)
        if fail:
            raise ConnectionError("no ollama")
        yield "thinking", "hmm"
        yield "content", "An answer."

    def fake_search(query, **kwargs):
        seen["queries"].append(query)
        return [
            {
                "cite": "(Stahl, 2026, p. 1)",
                "title": "T",
                "reference": "R",
                "passages": [{"cite": "(Stahl, 2026, p. 1)", "text": "passage"}],
            }
        ]

    monkeypatch.setattr(core, "stream_reply", fake_stream)
    monkeypatch.setattr(core, "search_library", fake_search)
    return seen


def test_chat_turn_follow_up_is_rewritten_for_search_and_saved(monkeypatch):
    saved = []
    seen = _fake_turn(monkeypatch)
    monkeypatch.setattr(core, "save_session", lambda s: saved.append(s["id"]))
    monkeypatch.setattr(core, "standalone_question", lambda q, s, m=core.MODEL: "standalone " + q)
    session = core.new_session()
    core.add_message(session, "user", "first")
    core.add_message(session, "assistant", "reply")

    events = list(core.chat_turn(session, "and why?", use_memory=False, use_library=True))

    assert events[0] == ("searched", "standalone and why?")
    assert seen["queries"] == ["standalone and why?"]
    system = seen["messages"][0][0]
    assert system["role"] == "system" and "passage" in system["content"]
    assert [m["content"] for m in seen["messages"][0][1:]] == ["first", "reply", "and why?"]
    last = session["messages"][-1]
    assert last["searched_for"] == "standalone and why?" and last["sources"]
    assert last["thinking"] == "hmm" and saved == [session["id"]]


def test_chat_turn_failure_leaves_session_unchanged(monkeypatch):
    _fake_turn(monkeypatch, fail=True)
    session = core.new_session()
    try:
        list(core.chat_turn(session, "hi", use_memory=False))
    except ConnectionError:
        pass
    assert session["messages"] == []


def test_chat_turn_stops_at_question_limit(monkeypatch):
    _fake_turn(monkeypatch)
    session = core.new_session()
    for i in range(core.MAX_QUESTIONS):
        core.add_message(session, "user", f"q{i}")
        core.add_message(session, "assistant", "a")
    try:
        list(core.chat_turn(session, "one more", use_memory=False))
        raise AssertionError("expected ConversationLimitError")
    except core.ConversationLimitError:
        assert core.question_count(session) == core.MAX_QUESTIONS


def test_standalone_question_skips_the_model_without_history(monkeypatch):
    monkeypatch.setattr(core.ollama, "chat", lambda **kw: (_ for _ in ()).throw(AssertionError))
    assert core.standalone_question("What is X?", core.new_session()) == "What is X?"


def test_format_history_keeps_only_last_pairs():
    session = core.new_session()
    for i in range(5):
        core.add_message(session, "user", f"q{i}")
        core.add_message(session, "assistant", f"a{i}")
    text = core.format_history(session, turns=2)
    assert "q3" in text and "a4" in text and "q2" not in text
