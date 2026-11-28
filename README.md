# MYbot

This project creates a local chatbot on my M5 MacBook laptop

The project includes: 
- setting up a local small LLM with open weights.
- defining multiple forms of memory
- post-training or fine-tuning the model with documents from ijCSCL and my eLibrary, as well as philosophy texts
- studying its reasoning
- saving its interactions to memory
- post-training or fine-tuning with its history of interactions so it learns and grows continuously
- investigating the model's thinking in order to compare human cognition, group cognition and agent cognition

## Project Goals

**Primary Objective:** 
- This project creates a chatbot running lcally. It includes experimental memory features that are included in its reasoning context.

- MYbot is downloaded from:

- MYbot's reasoning is permanently included in its memories of interactions.

- MYbot is post-trained or fine-tuning on my writings (300 essays) and on ijCSCL articles (300 articles) and on philosophy texts.

- MYbot learns from its interactions and is post-trained periodically on its past interactions.

- MYbot has models of itself, its past interactions, its users

**Key Targets:**
- Capture history of MYbots interactions
- Capture history of MYbots special post-trainings, and other experimental features added.

**Commentary & Notes:**
- MYbot is a "personal AI agent," not a universal one. It is based on a commercial LLM model that is universal. But then it is personalized to a specific user or user community -- those who use the particular computer that MYbot runs on.

- This particular bot started with the universal training common to the commercial model it started from. But it is open-weights, which means its parameters, which store its knowledge, can be changed, so that it is no longer identical to other models based on the same commercial model. All the experimental aspects of. MYbot are specific to the version running on this computer. For instance, weights are changed by post-training and other forms of continued learning, such as additional on-going training using the history of query/response interactions.

- MYbot is individualized and growing (learning, aging).

## Plan

**Goal and users:**
- a locally run LLM, that can replace some functions of Claude locally, avoiding charges for tokens.
- a chat agent based on it, that can answer my queries and assist in VSCode, etc.
- a platform for experimental research on AI agent cognition

**Concrete behaviors:** 
- post-training or fine-tuning of LLM on pdfs of writings that are relevant to me. Alternatively, RAG access to a library of pdfs (including from my other projects).
- analog of self-consciousness, 
- analog of continuous temporal awareness across sessions, 
- analog of theory-of-mind awareness of profiles of me and other people,
- analog of memory of all previous sessions, including queries and <thinking>
- analog of records of reasoning

**Constraints:** 
- run entirely locally on Mac Pro M5 with 32GB RAM and 4 TB storage

**Structure:** 
- File folders are defined in ~AI/mybot/
- Storage of session memory, etc in JSON/PKL files, synchronized for efficiencly and human-readability
 - End of development sessions: clean up code, tests of code, update documentation, upload to GitHub and commit

**Tests:**
          Request and facilitate user testing as appropriate.


## Inkling 2 Mini -- the LLM model

- General Information: Inkling 2 Mini is a general-purpose multimodal model that accepts text and image inputs and generates text outputs. It is intended for use in English and other languages, and across multiple coding languages. The model is designed to be used by developers building AI-powered applications, including agentic and tool-use systems, coding assistants, chatbots, and retrieval-augmented generation systems, and is suitable for general-purpose conversational use, instruction-following, and other natural language and visual tasks. It is released with open weights to support research, fine-tuning and integration into third-party products by downstream developers.

- Date of release: November 20, 2026

- On Apple Silicon: Ollama and Exo Labs

- Inkling 2 Mini can also be post-trained with: Miles, SkyRL

- Inkling 2 Mini can also be fine-tuned with: Tinker

 - Architecture type: A 24-layer decoder-only transformer with sparse Mixture-of-Experts (MoE) feed-forward layers. The middle 12 layers run three times with shared weights, giving 48 layer applications per token from 24 layers of weights. In each layer, each token is routed to 8 of 128 experts. Attention is a hybrid of local and global layers. The model is natively multimodal – images are encoded via a vision transformer – with image and text inputs projected into a shared hidden space and processed jointly by the decoder.

- Parameters:26.4B, 3.4B active; Note: each extra pass through the looped layers adds about 1.0B effective active parameters. Since the model runs with three passes, there are 5.4B effective active parameters per token.

## LLM models on this computer:
- Ollama has 8 entries installed: Manifest: /Users/GStahl2/.ollama/models/manifests/registry.ollama.ai/library/inkling-2-mini/latest

- Model	Parameters	Size on disk	Quantization
mybot:latest	        26.4B	20 GB	nvfp4
inkling-2-mini:latest	26.4B	20 GB	nvfp4
qwen2.5:14b	            14.8B	9.0 GB	Q4_K_M
llama3.1:8b	            8.0B	4.9 GB	Q4_K_M
llama3.1:latest	        8.0B	4.9 GB	Q4_K_M
llama3:latest	        8.0B	4.7 GB	Q4_0
gemma3:4b	            4.3B	3.3 GB	Q4_K_M
nomic-embed-text:latest	137M	274 MB	F16
- embedding length      2304               
- Same weights: mybot is your custom model from the Modelfile, built on inkling-2-mini, so they share the same weights. Likewise, llama3.1:8b and llama3.1:latest have the same ID. The real disk use is about 39 GB, not the roughly 72 GB you get by adding up the Size column.
- Embedding model: nomic-embed-text produces embeddings for search. It isn't a chat model.

## Initial steps

- Update Ollama. Use the menu-bar icon and choose "Restart to update", or install from ollama.com/download. Then check ollama --version shows 0.40.17 or newer.

- Pull the model. Run ollama pull inkling-2-mini. This is the default tag, 26b-a5b. There is also an MLX build, inkling-2-mini:26b-a5b-nvfp4, that may run faster on Apple Silicon.

- Smoke test. Run ollama run inkling-2-mini "Hello", then check memory use and speed in Activity Monitor.

- Set the context size. The model supports a 1M-token context, but your RAM can't handle that. Start with 32k, for example /set parameter num_ctx 32768. The server's default already comes out at 32768.

- Create a MYbot Modelfile. Build FROM inkling-2-mini with a system prompt, then run ollama create mybot -f Modelfile. Keep it in ~/AI/mybot/ so it is tracked in git.

- Call it from code. Use the Ollama Python client or the local API at localhost:11434 for the memory layer (JSON files, then RAG over your PDFs).

- Fine-tuning comes later. Ollama only runs models; it can't fine-tune them. The README lists Tinker for fine-tuning and Miles or SkyRL for post-training. Fine-tuned weights would need converting back to GGUF or MLX to run in Ollama.




## Chat UI

- Setup (once): `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`, then `ollama create mybot -f Modelfile`.
- Run: `.venv/bin/streamlit run src/app_streamlit.py` and open http://localhost:8501 (Ollama must be running).
- `src/core.py` holds the chat and history logic with no UI code; `src/app_streamlit.py` is a thin Streamlit layer. A FastAPI + HTML front end can reuse `core.py`.
- Each chat, including the model's thinking, is saved as JSON in `history/`.
- FastAPI + HTML version: `.venv/bin/uvicorn app_fastapi:app --app-dir src --port 8000`, then open http://localhost:8000. The server is `src/app_fastapi.py`; the whole page (HTML, CSS, JavaScript) is the single file `src/web/index.html`, so colors, wording and checkboxes can be changed there. Both front ends call `core.chat_turn`, so they behave the same.

## Follow-up questions

- A chat holds up to 8 questions (`core.MAX_QUESTIONS`, as in CSCLbot); the page shows how many are left.
- Without the library, a follow-up works because the whole conversation is sent to the model each time.
- With library search on, a follow-up is first rewritten into a standalone question by the local model (`core.standalone_question`, using the last 3 question/answer pairs), so "How do they differ from individual cognition?" is searched as "How does group cognition differ from individual cognition?". The rewritten question is shown as "Searched for: ..." and saved with the answer. This adds about 5-7 seconds per library follow-up.

## Memory (in `core.py`)

- `build_system_prompt(session)` builds the system message sent with every request: the SYSTEM text from the `Modelfile` (Ollama drops the Modelfile SYSTEM when a request has its own system message, so it is re-sent), the self-model, the profile of the current user, and a condensed recall of the most recent earlier sessions, including shortened thinking (budget: 5 sessions / 6000 characters).
- Self-model: `personality/self.json`. User profiles: `memory/profiles/<Name>.json`. Both are created with empty fields on first use; edit them by hand. They are git-ignored because the repository is public.
- The sidebar lets you pick or add the person you are talking with (saved in each session as `user`) and switch memory off to compare behavior with and without it.
- Not done yet: relevance-based recall (currently recency only).

## Library search (RAG over the e-library and ijCSCL articles)

- Tick **Search the ijCSCL and e-library documents** in the sidebar to retrieve passages for your next message. They are added to the system prompt with their APA in-text citations, and the sources used are saved with the answer (`sources` in the history JSON) and shown under "Library sources".
- `src/library_search.py` is copied from the CSCLbot project (`~/AI/csclbot/src/search.py`): dense `e5-base-v2` + BM25 + a page-level keyword index, merged by reciprocal rank fusion. It covers 17,441 e-library chunks, 335 chapter summaries, 463 ijCSCL article summaries and 8,226 passages of open-access articles. Retrieval only; Inkling writes the answer.
- The index (about 140 MB) is a copy of `~/AI/csclbot/data/index` and `references.json` in `data/library/`. It is git-ignored, so on a new machine copy it from CSCLbot again. The `e5-base-v2` model must be in the Hugging Face cache (`~/.cache/huggingface`); it is loaded offline.
- Follow-up questions are rewritten before searching (see Follow-up questions).

## Look and feel

- Colors are set in `.streamlit/config.toml` (light green). Streamlit cannot restructure the page; the FastAPI + HTML front end (`src/web/index.html`) can, and is the route for arbitrary HTML, instructions and widgets.

## End-of-day routine

- Run `scripts/end_of_day.sh [-m "commit message"] [-n]` (`-n` = dry run). It cleans caches, lints and formats with ruff, runs pytest, warns if code changed without a README update, then commits and pushes. It stops at the first failure.
- Chat history (`history/*.json`) is git-ignored because the repository is public.
