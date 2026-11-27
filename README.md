# MYbot

This project creates a local chatbot on my M5 MacBook laptop

The project includes: 
- setting up a local small LLM with open weights.
- defining multiple forms of memory
- post-training the model with documents from ijCSCL and my eLibrary, as well as philosophy texts
- studying its reasoning
- saving its interactions to memory
- post-training with its history of interactions so it learns and grows continuously
- investigating the model's thinking in order to compare human cognition, group cognition and agent cognition

## Project Goals

**Primary Objective:** 
- This project creates a chatbot running lcally. It includes experimental memory features that are included in its reasoning context.

- MYbot is downloaded from:

- MYbot's reasoning is permanently included in its memories of interactions.

- MYbot is post-trained on my writings (300 essays) and on ijCSCL articles (300 articles) and on philosophy texts.

- MYbot learns from its interactions and is post-trained periodically on its past interactions.

- MYbot has models of itself, its past interactions, its users

**Key Targets:**
- Capture history of MYbots interactions
- Capture history of MYbots special post-trainings, and other experimental features added.

**Commentary & Notes:**
- MYbot is a "personal AI agent," not a universal one. It is based on a commercial LLM model that is universal. But then it is personalized to a specific user or user community -- those who use the particular computer that MYbot runs on.

- This particular bot started with the universal training common to the commercial model it started from. But it is open-weights, which means its parameters, which store its knowledge, can be changed, so that it is no longer identical to other models based on the same commercial model. All the experimental aspects of. MYbot are specific to the version running on this computer. For instance, weights are changed by post-training and other forms of continued learning, such as additional on-going training using the history of query/response interactions.

- MYbot is individualized and growing (learning, aging).

**Plan:**
***Goal and users:*** 
- a locally run LLM, that can replace some functions of Claude locally, avoiding charges for tokens.
- a chat agent based on it, that can answer my queries and assist in VSCode, etc.
- a platform for experimental research on AI agent cognition

***Concrete behaviors:*** 
- post-training of LLM on pdfs of writings that are relevant to me. Alternatively, RAG access to a library of pdfs (including from my other projects).
- analog of self-consciousness, 
- analog of continuous temporal awareness across sessions, 
- analog of theory-of-mind awareness of profiles of me and other people,
- analog of memory of all previous sessions, including queries and <thinking>
- analog of records of reasoning

***Constraints:*** 
- run entirely locally on Mac Pro M5 with 32GB RAM and 4 TB storage

***Structure:*** 
- File folders are defined in ~AI/mybot/
- Storage of session memory, etc in JSON/PKL files, synchronized for efficiencly and human-readability
 - End of development sessions: clean up code, tests of code, update documentation, upload to GitHub and commit

***Tests:***
          Request and facilitate user testing as appropriate.

**The End**

