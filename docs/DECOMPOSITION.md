# Decomposition (written BEFORE any code)

## 1. The problem in my own words

I'm building a tool where you give it a WhatsApp group chat file and then ask questions about the project in normal English or Hinglish. It answers only from what the chat says, and shows the exact messages (who, when, what) it used. Because people in a group change their minds, the tool has to work out the *latest* decision and the *current* owner of each task, not just find any message that mentions them. If the chat doesn't clearly answer, it says so, and tells what the chat does show. It also gives an overview of the project: decisions, owners, what's done, what's open, and where the chat itself shows a problem.

## 2. What I noticed in the data

| # | What I noticed (quote + timestamp) | Why it makes answering hard |
|---|---|---|
| 1 | `03/10/26, 9:26 PM` Aarav: "done. Postgres" · `05/10/26, 8:05 PM` Rohan: "done" · `10/11/26, 9:12 PM` Kabir: "auth done, merged" | The same word means a decision, an acceptance and a completion. A bare "done" doesn't say which task it refers to, especially when one person owns two tasks (Rohan owns schema and tests after 24/10), so the surrounding messages must be read. |
| 2 | `12/10/26, 7:30 PM` Meera: "report due 3 days before demo day. Demo day 4 Dec so report 1 Dec" · `05/11/26, 6:14 PM` Aarav: "haan shayad" (about 24 Nov) · `09/11/26, 5:32 PM` Meera: "toh report 23 Nov" | One deadline has several values over time. One of them is only a "maybe", and the report date is derived from a rule ("3 days before demo day") and never announced by the college. The system must pick the latest valid value. |
| 3 | `19/10/26, 6:16 PM` Kabir: "search koi aur le lo please" · `19/10/26, 6:20 PM` Aarav: "ok search baad mein dekhte hain" · `10/11/26, 9:18 PM` Rohan: "search Saturday ko discuss karte hain" | Search was discussed many times but nobody accepted it. The system must not invent an owner. It should say the last known owner (Kabir) dropped it and that it is now unassigned. |
| 4 | `24/10/26, 11:25 PM` Kabir: "auth bhi le leta hoon. but Rohan you do the DB schema and the tests then" · `24/10/26, 11:26 PM` Rohan: "deal. schema + tests mere" | Ownership changed, and it came with a condition that gave the previous owner new tasks. The system must keep the history of who owned what and when, not only the latest line. |
| 5 | `06/11/26, 11:06 PM` Rohan: "tests kal raat tak kar dunga" · `07/11/26, 11:50 PM` Rohan: "tests nahi ho paye. kal pakka" · `09/11/26, 5:40 PM` Rohan: "tests ab bhi pending hain, I'll do by this Sunday" | These are repeated promises, not completions. The system must report "pending, promised deadline missed" and never treat a promise as done. Sarcastic replies (`06/11/26, 11:07 PM` Priya) also hide the meaning from a keyword search. |
| 6 | `05/10/26, 8:02 PM` Aarav: "Main - deployment" | In Hinglish *main* means "I", so the owner is the sender (Aarav). A system that doesn't understand Hinglish may miss the owner or read "main" as the English word. |
| 7 | `09/11/26, 5:40 PM` Rohan: "I'll do by this Sunday" · `06/11/26, 11:06 PM` Rohan: "kal raat tak" | These dates are relative to the message's own timestamp: "this Sunday" is 15 Nov, and "kal raat" is the night of 7 Nov. *Kal* can also mean yesterday, so context decides. |
| 8 | `05/10/26, 8:02 PM` Aarav: "Task split karte hain:" followed by 5 more lines (file lines 18-22) | Lines 18-22 have no timestamp. A line-by-line parser would drop them or treat them as separate messages and lose the task assignments. |

## 3. The simplest thing that could work, and how it would fail

**Simplest approach:** split the chat into messages, find the message that shares the most words with the question (keyword / TF-IDF search), and print that message as the answer.

**Three questions it would get wrong:**

1. **"What payment method are we using?"**
   - Correct: Razorpay in test mode (`02/11/26, 8:49 PM`, Aarav).
   - Simple approach: likely returns `20/10/26, 8:16 PM`, "final decision: no Razorpay, UPI QR manual", because it matches payment words and says "final".
   - Why: it matches words and has no idea which message came *later* and replaced the other.

2. **"Who owns auth, and is it finished?"**
   - Correct: Kabir took it over on 24/10 and reported it done and merged on `10/11/26, 9:12 PM`.
   - Simple approach: likely returns Rohan, because "Rohan - auth" (`05/10/26, 8:02 PM`) and Rohan's own auth messages match the words well.
   - Why: it cannot follow an ownership handoff over time, and cannot tell "promised" (Rohan, `12/10/26, 7:35 PM`) from "done" (Kabir).

3. **"Who is doing search?"**
   - Correct: nobody. Kabir gave it up on `19/10/26, 6:16 PM`, and the later discussions never ended with someone accepting it.
   - Simple approach: returns Kabir (from `05/10/26, 8:02 PM`, "Kabir - search + chat") or Aarav's "search baad mein dekhte hain".
   - Why: it cannot tell a dropped task from an owned one, and it always returns something, so it never says "the chat doesn't say".

## 4. Break it into sub-problems

```
 chat.txt
    |
    v
[1 Parser] ---------> messages (id, time, sender, text)
    |
    v
[2 Cleaner] --------> noise flagged, real dates
    |
    v
[3 Event extractor (LLM)] --> events + evidence message ids
    |            ^
    |            |
    |     [4 Date resolver (code)]  ("kal", "this Sunday" -> real dates)
    v
[5 State builder (code)] --> project state: decisions, owners, status, open/unassigned
    |                              |
    v                              v
[6 Question answerer]       [7 Project overview]
 state lookup + message search
 + LLM writes answer from that only
 + citation check
    |
    v
 answer + evidence   OR   "the chat doesn't say"
```

**1. Parser**
- Input: raw chat text file.
- Output: a list of messages, each with an id (file line number), timestamp, sender and text. Multi-line messages are joined, and a new message starts only at a line with the timestamp pattern.
- Check: on the sample chat it must produce 102 messages (107 lines minus the 5 continuation lines), 3 of them system messages, and the message at line 17 must contain all of the task list.

**2. Cleaner**
- Input: parsed messages.
- Output: the same messages with real datetimes (DD/MM/YY, 12-hour clock) and flags for system messages, `<Media omitted>`, deleted and edited messages.
- Check: lines 1-3 are flagged system, lines 29/46/61/104 flagged media, line 47 flagged deleted, and the datetime of line 33 is 12 Oct 2026, 19:30.

**3. Event extractor (LLM)**
- Input: windows of cleaned messages.
- Output: events (decision, assignment, handoff, status, deadline) each with a certainty (proposed / agreed / promised / done) and the ids of the messages it comes from.
- Check: compare against a hand-labelled list of events for part of the sample chat, and verify that every cited message id exists in the chat.

**4. Date resolver (code)**
- Input: a phrase like "this Sunday" or "kal raat tak" and the message's timestamp.
- Output: a concrete date (or "unclear").
- Check: unit tests, e.g. line 89 (sent Mon 9 Nov) gives 15 Nov, and line 81 (sent 6 Nov) gives 7 Nov.

**5. State builder (code)**
- Input: events in time order.
- Output: the current state: latest decision per topic with the history it replaced, current owner per task with previous owners, latest status, and the open and unassigned lists.
- Check: run it on the sample and compare with my hand-made expected state (payments = Razorpay test mode, auth owner = Kabir and done, search = unassigned, demo day = 26 Nov, and so on).

**6. Question answerer**
- Input: a question (English or Hinglish) and the project state plus messages.
- Output: an answer with evidence (timestamp, sender, line), or "the chat doesn't say" and what the chat does show.
- Check: my 10+ hand-written questions, including at least 3 that the chat cannot answer, which must be refused. Every cited line must exist and support the claim.

**7. Project overview**
- Input: the project state.
- Output: a readable report of decisions, owners, done work, open work, unassigned work, and problems the chat itself shows, each with evidence.
- Check: it matches my hand-made expected state, and no item appears without a cited message.

## 5. What I don't know yet

- **How well an LLM reads Hinglish events.** Plan: run it on the sample chat and compare with my hand-labelled events.
- **Which LLM and API to use** (cost, Hinglish quality, API key setup, or a local model on my Mac). Plan: try one or two on a few messages and compare.
- **How different WhatsApp exports look** (iPhone vs Android, 24-hour clock, other date orders). Plan: look up the formats, make the parser tolerant, and test it with small hand-edited variants of the sample.
- **How to separate "proposed", "agreed" and "promised" from "done".** Plan: try a first schema, then check it on the tricky messages from section 2.
- **How to verify that cited evidence really supports an answer.** Plan: start with a check that the cited ids exist, then try checking that the quoted text appears in those messages.
- **What happens with a very long chat** that won't fit in one request. Plan: process in overlapping windows, and test with a long chat I make by joining or extending the sample.
- **How to decide what "kal" means.** Plan: use the tense of the sentence and the message timestamp, and mark it "unclear" when unsure.

## 6. Build order

1. **Parser only, no AI.** Print the parsed messages and check the count of 102. This is the foundation and is fully testable.
2. **A crude end-to-end version.** `python run.py --chat file --question "..."` sends the parsed chat and the question to an LLM and prints an answer with line numbers. It will be flawed, but it proves the command runs and gives me something to improve.
3. **Event extraction, date resolver and state builder**, then the project overview. This is the main improvement, since time-tracking is the hard part.
4. **Question answering over the state**, with citation checks and refusing to answer when the chat doesn't say.
5. **Test set and honest scoring**, then fixes for the failures I find.
6. **Try a second chat**, write FINAL_NOTES, record the demo video.

I chose this order so that something runs from the start, each step can be tested before the next one builds on it, and the exact (non-AI) parts are built before the parts that depend on an AI.

## 7. Where I'll use AI, and where I won't

- **At runtime, the LLM is used for two things only:** reading messages into events (step 3) and writing the final answer from the evidence I give it (step 6). Language understanding is its strength, especially for Hinglish.
- **Plain code, not the LLM, handles** parsing, date calculation, building the current state from events, and checking citations. These must be exactly right and testable, and models make mistakes on calendar maths and on "what is the latest".
- **While building,** I'll use an AI assistant to help with code, such as the regex parser, but I will design the data model (what an event and the state look like) myself, because everything else depends on it, and I need to be able to explain it.
- **I will write the 10+ test questions and their correct answers by hand,** so the evaluation doesn't depend on the system's own output.
- In FINAL_NOTES I'll state honestly which parts I wrote or fully understand, and which I accepted from AI.