# Chat Intel: the current state of a project, from its WhatsApp chat

Reads a WhatsApp group-chat export (English + Hinglish), builds a project overview
(decisions, deadlines, owners, open, done and unassigned tasks), and answers questions
with line-number evidence. It says "the chat doesn't say" when the chat does not support an answer.

## Setup (Python 3.10+)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then put your own Gemini API key in .env
```

`.env` needs `GEMINI_API_KEY`. Optional: `LLM_MODEL` (answering model) and `EXTRACTION_MODEL` (a stronger model used once per chat for extraction). `.env` is git-ignored.

## Run

```bash
python run.py --chat path/to/chat.txt
```

This prints the project overview, then opens a prompt where you can ask questions in English or Hinglish. Press Enter on an empty line to quit.

| Flag | Effect |
|---|---|
| `--question "..."` | Answer one question and exit |
| `--overview` | Also print the overview when `--question` is used |
| `--no-state` | Skip extraction and answer from the raw chat only (the single-call baseline) |
| `--refresh` | Ignore the cache and re-extract events |

The first run on a new chat makes a few model calls for extraction. The result is cached in `.cache/`, so later runs are faster.

## How it works

1. **Parse** (`chat_intel/parser.py`): export lines become messages. The message id is its line number, so every claim can cite `L<n>`.
2. **Extract events** (`extractor.py`, `events.py`): the model proposes small structured events (decision, assignment, status, deadline). Code then checks each one: the sender comes from the real chat, and the quoted words must appear in the cited message. Unverifiable events are rejected.
3. **Build state** (`state.py`): plain rules with no model. Owners change only on assigned or accepted, a request is not an assignment, a promise is not "done", the latest agreed decision wins with history kept, and a task with no owner that is not done is unassigned.
4. **Overview** (`overview.py`): renders the state with line numbers.
5. **Answer** (`qa.py`): the model gets the overview as a guide and the full chat as the source of truth. Cited line numbers are checked by code, and the evidence printed is the real parsed message text.

## Tests and evaluation

```bash
python -m pytest -q          # unit tests, no API calls
python evaluate.py           # 18 hand-checked questions on data/team_chat.txt
python evaluate.py --no-state                     # same, without the project state
python evaluate.py --chat data/heldout_chat.txt --questions tests/heldout_questions.json   # a second chat
```

Questions and ground truth are in `tests/`. Reports are in `docs/` (`comparison/` and `variance_baseline/` hold the runs). Results, failures and known limits are written up honestly in `docs/FINAL_NOTES.md`.

## Known limits

- Task names from the extractor can be inconsistent, so the overview can split one piece of work into several rows or miss a link between them.
- Some tasks mentioned only in passing are not extracted.
- Model answers vary between runs even at temperature 0, and the LLM judge used in evaluation is itself imperfect.

Details and numbers are in `docs/FINAL_NOTES.md`.

---

# Original task description

## Take-Home Task: Make Sense of the Team Chat


---

## The problem

A college project team has a WhatsApp group. For five weeks they argued, changed their minds, gave each other tasks, missed deadlines, made decisions, reversed them, and joked around.

Nobody on the team can say what the **current** state of their project is. Not who owns what, not what was decided, not even when the deadline is.

**Your job: build a system that reads the chat and answers questions about it.**

The chat is in `data/team_chat.txt`. It's a real-format WhatsApp export, in a mix of English and Hinglish. **Read it yourself before you design anything.** All of it. It's short.

Someone should be able to ask things like:

- "What's the current status of X?"
- "Who is responsible for Y, and did they finish?"
- "What did we decide about Z, and has that changed?"
- "Is there anything nobody is working on?"

and get a correct, trustworthy answer.

### What your system must do

1. **Run on any chat file in this format, not just ours.** We will run it on a different chat during your interview. Hardcoding facts from this chat will fail. Give us one command, for example `python run.py --chat path/to/chat.txt`. A web app, notebook or CLI is all fine. We care that it runs.
2. **Answer questions in English or Hinglish, and show its evidence.** Each answer should point back to the message(s) it is based on (timestamp, sender, or line).
3. **Say "the chat doesn't say" when it doesn't.** A confident wrong answer is worse than no answer.
4. **Produce a "state of the project" view.** It should list current decisions, who owns what, and what is still open or unassigned. The format is up to you.

That's the whole spec. We have deliberately not told you how to do it. Figuring that out is the task.



## How to work

### Step 0: Decompose before you code

Copy `docs/DECOMPOSITION.md` and fill it in **before writing any code**. Commit it on its own, first, so the git history shows the order.

This is the most important document in your submission. Spend real time on it.

### Step 1: Build in small slices

Get the smallest end-to-end version working first (chat in, one answer out), then improve it. Commit often. 

### Step 2: Test yourself honestly

Write **at least 10 questions** about this chat, with the correct answers worked out by you, by hand. Run your system on them and score it. Don't hide the failures. We trust a candidate who finds their own bugs more than one who claims everything works.

### Step 3: Wrap up

- Fill in `docs/FINAL_NOTES.md`.
- Upload to a Repo

---

## Rules and practical notes


- **No secrets in the repo.** Keep API keys in a `.env` file (already git-ignored) and tell us what we need to set.
- **Do your own work.** Don't share this task or your solution publicly before deadline / submission date .

---

## Submission checklist

- [ ] Public GitHub repo (fork or copy of this one) with a commit history that shows your process
- [ ] `docs/DECOMPOSITION.md`, committed before any code
- [ ] A working command to run the system on any chat file
- [ ] Your own test questions and results, in `docs/FINAL_NOTES.md`
- [ ] `docs/FINAL_NOTES.md` complete, with the video link
- [ ] The repo link, submitted via the form before the deadline


Good luck. We're looking forward to seeing how you think.
