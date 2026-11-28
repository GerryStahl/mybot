"""Streamlit chat front end for MYbot. Run: streamlit run src/app_streamlit.py"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
import core  # noqa: E402

st.set_page_config(page_title="MYbot", page_icon="🤖", layout="wide")

if "session" not in st.session_state:
    st.session_state.session = core.new_session()
session = st.session_state.session

with st.sidebar:
    st.title("MYbot")
    st.caption(f"Local model: `{core.MODEL}`")
    if st.button("New chat", use_container_width=True):
        st.session_state.session = core.new_session(session["user"])
        st.rerun()
    core.load_profile(session["user"])  # creates an empty profile file to edit if missing
    users = core.list_users()
    session["user"] = st.selectbox(
        "Talking with", users, index=users.index(core.slug(session["user"]))
    )
    with st.form("add_person", clear_on_submit=True, border=False):
        new_user = st.text_input("Add a person", placeholder="Name")
        if st.form_submit_button("Add") and new_user.strip():
            session["user"] = core.slug(new_user)
            core.load_profile(session["user"])
            st.rerun()
    st.markdown("**Options for your next message**")
    use_memory = st.checkbox(
        "Use memory", value=True, help="Adds MYbot's self-model, your profile and earlier sessions."
    )
    use_library = st.checkbox(
        "Search the ijCSCL and e-library documents",
        value=False,
        disabled=not core.library_available(),
        help="Click here to search the ijCSCL articles and Gerry Stahl's e-library as part of "
        "your question. MYbot then answers from the passages found and cites them.",
    )
    st.divider()
    st.subheader("History")
    for item in core.list_sessions():
        label = item["title"]
        if st.button(label, key=item["id"], use_container_width=True, help=item["created"]):
            st.session_state.session = core.load_session(item["id"])
            st.session_state.session.setdefault("user", core.DEFAULT_USER)
            st.rerun()


def render(message: dict) -> None:
    with st.chat_message(message["role"]):
        if message.get("searched_for"):
            st.caption(f"Searched for: {message['searched_for']}")
        if message.get("thinking"):
            with st.expander("Thinking"):
                st.markdown(message["thinking"])
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("Library sources"):
                st.markdown("\n".join(f"- {source}" for source in message["sources"]))


st.header(session["title"])
for message in session["messages"]:
    render(message)

left = core.MAX_QUESTIONS - core.question_count(session)
if left <= 0:
    st.info(f"This chat has reached {core.MAX_QUESTIONS} questions. Start a new chat to continue.")
elif prompt := st.chat_input(
    f"Message MYbot ({left} question{'s' * (left != 1)} left in this chat)"
):
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        think_slot = st.expander("Thinking", expanded=True).empty()
        answer_slot = st.empty()
        thinking, answer = "", ""
        try:
            with st.spinner("Searching the library..." if use_library else "Thinking..."):
                turn = core.chat_turn(session, prompt, use_memory, use_library)
                kind, text = next(turn, ("", ""))
            if kind == "searched":
                st.caption(f"Searched for: {text}")
            for kind, text in [(kind, text), *turn]:
                if kind == "thinking":
                    thinking += text
                    think_slot.markdown(thinking)
                elif kind == "content":
                    answer += text
                    answer_slot.markdown(answer + "▌")
            answer_slot.markdown(answer)
        except Exception as error:  # Ollama not running, model missing, etc.
            answer_slot.error(f"Could not get a reply from Ollama: {error}")
            st.stop()
    st.rerun()
