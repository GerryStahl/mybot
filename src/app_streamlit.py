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
        st.session_state.session = core.new_session()
        st.rerun()
    st.divider()
    st.subheader("History")
    for item in core.list_sessions():
        label = item["title"]
        if st.button(label, key=item["id"], use_container_width=True, help=item["created"]):
            st.session_state.session = core.load_session(item["id"])
            st.rerun()


def render(message: dict) -> None:
    with st.chat_message(message["role"]):
        if message.get("thinking"):
            with st.expander("Thinking"):
                st.markdown(message["thinking"])
        st.markdown(message["content"])


st.header(session["title"])
for message in session["messages"]:
    render(message)

if prompt := st.chat_input("Message MYbot"):
    core.add_message(session, "user", prompt)
    render(session["messages"][-1])

    thinking, answer = "", ""
    with st.chat_message("assistant"):
        think_box = st.expander("Thinking", expanded=True)
        think_slot = think_box.empty()
        answer_slot = st.empty()
        try:
            for kind, text in core.stream_reply(core.model_messages(session)):
                if kind == "thinking":
                    thinking += text
                    think_slot.markdown(thinking)
                else:
                    answer += text
                    answer_slot.markdown(answer + "▌")
            answer_slot.markdown(answer)
        except Exception as error:  # Ollama not running, model missing, etc.
            answer_slot.error(f"Could not get a reply from Ollama: {error}")
            session["messages"].pop()  # drop the unanswered prompt so history stays consistent
            st.stop()

    core.add_message(session, "assistant", answer, thinking)
    core.save_session(session)
    st.rerun()
