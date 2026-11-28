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
ROOT = Path(__file__).resolve().parent.parent
HISTORY_DIR = ROOT / "history"
MEMORY_DIR = ROOT / "memory"
PERSONALITY_DIR = ROOT / "personality"
MODELFILE = ROOT / "Modelfile"
DEFAULT_USER = "Gerry"


def stream_reply(messages: list[dict], model: str = MODEL) -> Iterator[tuple[str, str]]:
    """Yield ("thinking" | "content", text_fragment) as the model generates.

    `messages` holds only role/content dicts; thinking from earlier turns is not resent.
    """
    for chunk in ollama.chat(model=model, messages=messages, stream=True):
        if chunk.message.thinking:
            yield "thinking", chunk.message.thinking
        if chunk.message.content:
            yield "content", chunk.message.content


def new_session(user: str = DEFAULT_USER) -> dict:
    now = datetime.now()
    return {
        "id": f"{now:%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}",
        "model": MODEL,
        "user": user,
        "created": now.isoformat(timespec="seconds"),
        "title": "New chat",
        "messages": [],  # {"role", "content", "thinking"?, "time"}
    }


def add_message(
    session: dict,
    role: str,
    content: str,
    thinking: str = "",
    sources: list[str] | None = None,
    searched_for: str = "",
) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    message = {"role": role, "content": content, "time": now}
    if thinking:
        message["thinking"] = thinking
    if sources:
        message["sources"] = sources  # library documents retrieved for this answer
    if searched_for:
        message["searched_for"] = searched_for  # standalone form of a follow-up question
    session["messages"].append(message)
    if role == "user" and session["title"] == "New chat":
        session["title"] = re.sub(r"\s+", " ", content).strip()[:60] or "New chat"


def model_messages(session: dict, system: str = "") -> list[dict]:
    """Role/content dicts for Ollama, with an optional leading system message."""
    messages = [{"role": m["role"], "content": m["content"]} for m in session["messages"]]
    return [{"role": "system", "content": system}, *messages] if system else messages


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


# --- Memory: self-model, user profiles, and recall of earlier sessions -------------------------

DEFAULT_SELF = {
    "name": "MYbot",
    "description": "A personal AI agent running locally and individualized to this computer.",
    "traits": [],
    "notes": [],
}
DEFAULT_PROFILE = {"description": "", "interests": [], "preferences": [], "notes": []}


def _read_json(path: Path, default: dict) -> dict:
    """Read a JSON file, writing `default` first if it does not exist yet."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(default, indent=2, ensure_ascii=False), encoding="utf-8")
        return dict(default)
    return json.loads(path.read_text(encoding="utf-8"))


def load_self(personality_dir: Path = PERSONALITY_DIR) -> dict:
    return _read_json(personality_dir / "self.json", DEFAULT_SELF)


def load_profile(user: str, memory_dir: Path = MEMORY_DIR) -> dict:
    return _read_json(memory_dir / "profiles" / f"{slug(user)}.json", DEFAULT_PROFILE)


def list_users(memory_dir: Path = MEMORY_DIR) -> list[str]:
    return sorted(p.stem for p in (memory_dir / "profiles").glob("*.json"))


def slug(name: str) -> str:
    """File-safe form of a person's name (case kept so it round-trips through list_users)."""
    return re.sub(r"[^\w-]+", "-", name.strip()).strip("-") or "user"


def base_prompt(modelfile: Path = MODELFILE) -> str:
    """The SYSTEM prompt from the Modelfile.

    Ollama drops the Modelfile SYSTEM when a request carries its own system message, so core
    re-sends it; the Modelfile stays the single place where MYbot's identity is written.
    """
    try:
        match = re.search(r'^SYSTEM """(.*?)"""', modelfile.read_text("utf-8"), re.M | re.S)
    except OSError:
        match = None
    return match.group(1).strip() if match else DEFAULT_SELF["description"]


def _format_fields(title: str, data: dict) -> str:
    lines = [f"{title}:"]
    for key, value in data.items():
        if value:
            lines.append(f"- {key}: {', '.join(value) if isinstance(value, list) else value}")
    return "\n".join(lines)


def recall_sessions(
    current_id: str,
    history_dir: Path = HISTORY_DIR,
    max_sessions: int = 5,
    max_chars: int = 6000,
    max_thinking: int = 300,
) -> str:
    """Condense the most recent earlier sessions (including shortened thinking) into text.

    Newest sessions come first and the text stops at `max_chars` so the context stays small.
    """
    parts, used = [], 0
    for item in list_sessions(history_dir):
        if item["id"] == current_id:
            continue
        if len(parts) >= max_sessions or used >= max_chars:
            break
        session = load_session(item["id"], history_dir)
        lines = [f"[{session['created']}] {session['title']}"]
        for m in session["messages"]:
            if m.get("thinking"):
                lines.append(f"  (thinking) {m['thinking'][:max_thinking].strip()}")
            lines.append(f"  {m['role']}: {m['content']}")
        text = "\n".join(lines)
        parts.append(text[: max_chars - used])
        used += len(text) + 2  # the blank line between sessions
    return "\n\n".join(parts)


def build_system_prompt(
    session: dict,
    history_dir: Path = HISTORY_DIR,
    memory_dir: Path = MEMORY_DIR,
    personality_dir: Path = PERSONALITY_DIR,
    modelfile: Path = MODELFILE,
    library: str = "",
    memory: bool = True,
) -> str:
    """Identity, plus (if `memory`) self-model, profile, past sessions, plus library passages."""
    sections = [base_prompt(modelfile)]
    if memory:
        user = session.get("user", DEFAULT_USER)
        sections += [
            _format_fields("Your self-model", load_self(personality_dir)),
            _format_fields(
                f"Profile of the person you are talking with ({user})",
                load_profile(user, memory_dir),
            ),
        ]
        recalled = recall_sessions(session["id"], history_dir)
        if recalled:
            sections.append("Memory of earlier sessions (most recent first):\n" + recalled)
    if library:
        sections.append(library)
    return "\n\n".join(sections)


# --- Library: retrieval from the e-library and ijCSCL index (data/library) ---------------------

LIBRARY_INSTRUCTIONS = (
    "Library passages retrieved for the user's latest question follow. Base your answer on them "
    "where relevant, cite with the in-text citation given for each passage (never invent "
    "citations or page numbers), paraphrase summaries rather than quoting them, and say so if "
    "the passages do not answer the question."
)
_searcher = None


def library_available() -> bool:
    from library_search import INDEX_DIR

    return (INDEX_DIR / "items.jsonl").exists()


def search_library(query: str, books: int = 4, articles: int = 3) -> list[dict]:
    """Hybrid search (dense + BM25 + keyword pages); the model loads on first use."""
    global _searcher
    if _searcher is None:
        from library_search import Searcher

        _searcher = Searcher()
    return _searcher.search(query, books=books, articles=articles, per_doc=2)


def format_library_context(results: list[dict], searched_for: str = "") -> str:
    """Numbered passages with their citations and references, for the system prompt."""
    if not results:
        return ""
    lines = [LIBRARY_INSTRUCTIONS, ""]
    if searched_for:
        lines += [f"(The library was searched for: {searched_for})", ""]
    for n, r in enumerate(results, 1):
        lines.append(f"[{n}] {r['cite']} - {r['reference']}")
        for passage in r["passages"]:
            lines.append(f"    {passage['cite']}: {passage['text']}")
        if r.get("note"):
            lines.append(f"    {r['note']}")
    return "\n".join(lines)


def library_sources(results: list[dict]) -> list[str]:
    return [f"{r['cite']} {r['title']}" for r in results]


# --- Conversation: follow-up questions and one full turn ---------------------------------------

MAX_QUESTIONS = 8  # per chat, as in CSCLbot; keeps the prompt well inside the 32k context
HISTORY_TURNS = 3  # earlier question/answer pairs shown to the query rewriter
HISTORY_ANSWER_CHARS = 1200
REWRITE_SYSTEM = (
    "Rewrite the user's last question as ONE standalone question that can be understood without "
    "the conversation, to search a library on computer-supported collaborative learning. Resolve "
    "references such as 'that', 'it', 'those studies' or 'the second one' using the conversation, "
    "and keep the user's key terms. If the last question is already standalone or starts a new "
    "topic, return it unchanged. Output only the question."
)


class ConversationLimitError(Exception):
    """The chat already holds MAX_QUESTIONS questions."""


def question_count(session: dict) -> int:
    return sum(1 for m in session["messages"] if m["role"] == "user")


def format_history(session: dict, turns: int = HISTORY_TURNS) -> str:
    """The last `turns` question/answer pairs as text."""
    pairs, question = [], None
    for m in session["messages"]:
        if m["role"] == "user":
            question = m["content"]
        elif question is not None:
            pairs.append(f"Q: {question}\nA: {m['content'][:HISTORY_ANSWER_CHARS]}")
            question = None
    return "\n\n".join(pairs[-turns:])


def standalone_question(question: str, session: dict, model: str = MODEL) -> str:
    """Rewrite a follow-up so a search understands it; unchanged for a first question."""
    history = format_history(session)
    if not history:
        return question
    reply = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": REWRITE_SYSTEM},
            {"role": "user", "content": f"Conversation:\n{history}\n\nLast question: {question}"},
        ],
        think=False,
        options={"temperature": 0, "num_predict": 600},  # the model reasons even with think=False
    )
    text = reply.message.content.strip().strip('"')
    return text if 0 < len(text) <= 400 else question


def chat_turn(
    session: dict,
    prompt: str,
    use_memory: bool = True,
    use_library: bool = False,
    model: str = MODEL,
) -> Iterator[tuple[str, str]]:
    """One question and answer, shared by all front ends; saves the session when finished.

    Yields ("searched", standalone_question) if the library is searched, then ("thinking" |
    "content", fragment). If anything fails the session is left as it was, and the error is raised.
    The conversation so far is always sent, so general follow-ups work without the library.
    """
    if question_count(session) >= MAX_QUESTIONS:
        raise ConversationLimitError(
            f"This chat has reached {MAX_QUESTIONS} questions. Please start a new chat."
        )
    library, sources, searched = "", [], ""
    if use_library:
        searched = standalone_question(prompt, session, model)
        yield "searched", searched
        results = search_library(searched)
        library = format_library_context(results, searched if searched != prompt else "")
        sources = library_sources(results)
    add_message(session, "user", prompt)
    thinking, answer = "", ""
    try:
        system = build_system_prompt(session, library=library, memory=use_memory)
        for kind, text in stream_reply(model_messages(session, system), model):
            if kind == "thinking":
                thinking += text
            else:
                answer += text
            yield kind, text
    except BaseException:  # includes a closed connection (GeneratorExit)
        session["messages"].pop()
        raise
    add_message(
        session, "assistant", answer, thinking, sources, searched if searched != prompt else ""
    )
    save_session(session)
