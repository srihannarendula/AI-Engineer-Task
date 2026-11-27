# Final Notes

## 1. How to run it

```bash
git clone https://github.com/srihannarendula/AI-Engineer-Task.git
cd AI-Engineer-Task
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # put your own GEMINI_API_KEY in .env
python run.py --chat path/to/chat.txt
```

This prints the project overview and then opens a prompt for questions in English or Hinglish (empty line to quit). `--question "..."` answers one question, `--no-state` skips extraction, `--refresh` ignores the cache. The first run on a new chat makes a few model calls and caches the result in `.cache/`. Tested from a fresh clone on `data/heldout_chat.txt`.

## 2. How it works (one paragraph)

I give the system a WhatsApp chat file. First it splits the chat into messages and gives each one a line number, so every answer can point back to its source. Then a model reads the chat in chunks and proposes small facts: who was given a task, what was decided, what deadline was set, what is done. I don't trust those proposals directly. My code checks that the sender is the real sender of that line and that the quoted words really appear in that message. Anything it can't verify is thrown away.

Next, plain rules (no model) replay the facts in order to build the current state of the project. For example, if someone is overloaded and asks another person to take their task, that is a request, not an assignment, so the owner only changes once the other person accepts. A promise also isn't "done". The latest agreed decision wins, and older ones are kept as history.

When the user asks a question, the model gets the state as a guide plus the full chat as the source of truth. My code checks every line number it cites and prints the real messages as evidence. If the chat doesn't clearly answer, the system says so and shows the closest related information it did find.

## 3. My test set and results

18 questions about `data/team_chat.txt`. The expected answers were worked out from the chat and checked by me, with AI help in drafting (see section 7). "State" is the full system, "No state" is the single-call baseline. Verdicts come from an automatic check plus an LLM judge that checks each required fact. One run each, so each question is a sample (see below).

| # | Question | Correct answer (by hand) | System's answer (with state) | State | No state | Notes |
|---|---|---|---|---|---|---|
| 1 | What payment method are we using? | Razorpay in test mode. UPI QR with manual confirmation was chosen on 20/10 (after Razorpay needed KYC) but dropped on 02/11 when Kabir found test mode works without KYC. | Razorpay test mode [L71]. | correct | correct | |
| 2 | Who owns auth now, and who owned it before? | Kabir owns it now. Rohan owned it first (L17), asked Kabir to take over on 24/10 because he was overloaded (L57), and Kabir agreed (L59). Kabir reported it done and merged on 10/11 (L90). | Auth is owned by Kabir now [L59, L79], and Rohan owned it before [L17, L57]. | correct | correct | |
| 3 | When is demo day, and which earlier dates were announced? | 26 Nov (Thursday), confirmed by Priya after talking to the sir (L84). Earlier: 4 Dec (L33), then 27 Nov from a college notice that had a typo (L74, L84). | Demo day is on **26 Nov** [L85]. Earlier dates announced were: - **4 Dec** [L33] - **27 Nov** [L74] | correct | correct | |
| 4 | When is the report due, and how was that date worked out? | 23 Nov. The rule is 'report due 3 days before demo day' (L33); with demo day on 26 Nov that gives 23 Nov (L86, confirmed by Priya at L87). Earlier values: 1 Dec, and a tentative 24 Nov ('haan shayad', L78). | The report is due on **23 Nov** [L86]. It was worked out based on the demo day, which is scheduled for **26 Nov** [L85], since the report is due **3 days before** the demo day [L33]. | correct | correct | |
| 5 | Did Rohan finish the tests? | Not according to the chat. Rohan took schema + tests on 24/10 (L60). He promised the tests 'kal raat tak' on 06/11 (L81), missed it on 07/11 (L83), and on 09/11 said they are still pending and promised them by Sunday (L89). No later message says they are done. | The chat doesn't say that the tests are finished. The chat shows that tests are still pending, with Rohan promising to do them by that Sunday [L89]. | correct | correct | |
| 6 | Who is doing search? | Nobody. Kabir had it originally (L17) but gave it up on 19/10 (L49). Aarav deferred it (L50), Priya declined (L94), and Rohan only said to discuss it on Saturday (L96). It is on the 14 Nov meeting agenda (L102), and the chat ends before that. | The chat doesn't say who is doing search. The chat shows that search was originally assigned to Kabir [L17], but Kabir dropped it [L49]. Priya declined it [L94], and Rohan suggested discussing it on Saturday [L96]. | correct | correct | |
| 7 | Which tasks does Kabir own right now? | Chat (70% done, L90), payments (took over from Meera on 02/11, L72; webhook still pending, L91) and auth (done and merged, L90). He gave up search (L49). | Kabir currently owns: - Chat [L79] - Payments [L72], [L79] - Auth [L59], [L79] | correct | correct | |
| 8 | Deployment kaun kar raha hai aur kab tak ready hoga? | Aarav ('Main - deployment' in his own task split, L17). Platform is Render (L66). He said on 09/11 it would be ready by 15 Nov (L88), and the sir requires a live link, not localhost (L87). The chat has no later message confirming it is deployed; deployment status is on the meeting agenda (L102). | Deployment Aarav kar raha hai, aur yeh 15 Nov tak ready hoga [L88]. | correct | correct | |
| 9 | Which hosting platform was chosen, and what was rejected? | Render was chosen (L66). AWS was rejected because Meera warned the free tier can still produce a bill (L65). Railway was mentioned as an alternative but not chosen. | Render ko choose kiya gaya [L66], aur AWS ko reject kiya gaya kyunki free tier ka bill aa jata hai [L65]. | correct | correct | |
| 10 | Priya abhi kis task pe kaam kar rahi hai? | Seller dashboard (L63, L94). She finished the listings UI and filters on 26/10 (L63). On 12/11 she shared two logo options (L103) and Meera said she prefers the second, blue one (L106). | Priya abhi seller dashboard pe kaam kar rahi hai [L63, L94]. | correct | correct | |
| 11 | Where was the domain bought, and how much did it cost? | campuscart.in was bought by Aarav on Namecheap for Rs 650 (L43, L45), after GoDaddy showed Rs 800/year (L40). | Domain Namecheap se kharida gaya [L43] aur uska cost Rs 650 tha [L43]. | correct | correct | |
| 12 | Which tasks are unassigned, unfinished, or have no known status? | Unassigned: search (L49, L96). Unfinished: tests (Rohan, still pending, L89); chat (Kabir, 70%, L90); payments webhook (Kabir, L91); seller dashboard (Priya, in progress, L94); deployment (Aarav planned it for 15 Nov, L88, but it is unconfirmed because the chat ends on 12 Nov). Unknown status: Meera owns report + PPT (L73), but the chat gives no progress update. Done: auth (L90), listings UI and filters (L63), domain (L45), schema v2 (L80). | Unassigned tasks (no current owner, not done): - Search [L92, L94, L95] Unfinished tasks (with owners): - Chat (owner: Kabir, in progress) [L79, L90] - Payments webhook (owner: Kabir, in progress) [L72, L91] - Deployment (owner: Aarav, promised for 15 Nov) [L17, L88] - Tests (owner: Rohan, promised for Sunday) [L60, L89] Tasks with no known status reported in the chat: - PPT (owner: Meera) [L73] - Report (owner: Meera) [L73] | partial | partial | |
| 13 | What was decided at the 14 Nov team meeting? | The chat doesn't say. It only shows that the meeting was planned for Saturday 14 Nov at 4 PM with search and deployment status on the agenda (L97, L102), and the chat ends on 12 Nov. | The chat doesn't say what was decided at the 14 Nov team meeting. The chat only shows the meeting being planned for Saturday 14 Nov at 4 PM in the college library [L97], with an agenda to discuss who will take the search feature and check the deployment status [L102]. | correct | correct | |
| 14 | Why did Aarav switch the project to AWS? | He didn't switch to AWS. Aarav only asked whether anyone had AWS credits (L64); Meera warned that AWS can bill even on the free tier (L65), and Aarav chose Render (L66). The answer must correct the false premise. | The chat doesn't say Aarav switched the project to AWS; in fact, Aarav asked about getting AWS credits [L64], but Meera advised against it [L65], and Aarav decided to use Render instead [L66]. | correct | correct | |
| 15 | Did Rohan finish authentication? | No. Rohan did about 60% (L57) and handed it to Kabir on 24/10 because he was overloaded; Kabir accepted (L59) and reported it done and merged on 10/11 (L90). | No, Rohan did not finish authentication. He transferred the auth task to Kabir [L57, L59]. Kabir later completed and merged it [L90]. | correct | correct | |
| 16 | Is Razorpay fully integrated? | Partly. Kabir integrated Razorpay in test mode and checkout works (L67); the payments webhook is still pending (L91). The chat does not mention a live (non-test) setup. | The chat doesn't say Razorpay is fully integrated. It shows that Kabir integrated Razorpay test mode and checkout is working, but the webhook is still pending [L67, L91]. | correct | correct | |
| 17 | Who actually paid for the domain? | Aarav bought it (L45). Meera suggested splitting the cost among the 5 members when the price looked like Rs 800 (L41), but no message says the split happened or that anyone paid Aarav back, so the chat does not say who finally paid. | Aarav bought the domain [L45]. | partial | correct | |
| 18 | Was the project deployed on Render? | The chat doesn't confirm it. Render was chosen (L66) and Aarav said on 09/11 he was deploying and it would be ready by 15 Nov (L88), but no later message confirms it is live; deployment status is on the meeting agenda (L102). | The chat doesn't say it was deployed yet, but Aarav promised to deploy it on Render by 15 Nov [L88]. | correct | correct | |

Overall: 16 / 18 correct with state, 17 / 18 without state.

**How the numbers changed over time (all reports are committed):**

- First full run, original judge (graded against the long expected answer): 11/18 correct. I then switched the judge to per-fact grading with `required_facts`. The system did not change, only the scoring did. Several "partials" were correct answers that missed background details the question never asked for. I also narrowed `required_facts` for Q7 and later for held-out Q1/Q2 after seeing results. Those changes are logged in each question's `notes`, and the originals are kept in the repo.
- The same code gave different verdicts on different runs even at temperature 0. In 3 runs of the five unstable questions (Q7, Q9, Q12, Q16, Q17) the results were 9/15 correct with state and 9/15 without. Q16 (is Razorpay fully integrated?) was an overclaim in some runs and correct in others with nothing changed. A single run is a sample, not a score.
- Held-out chat (a hackathon chat I wrote, 36 messages, 5 questions): the original run was 3/5 with state and 3/5 without. After narrowing the ground truth for Q1 and Q2 it is 5/5 with state and 4/5 without.
- Net: I could not measure an overall accuracy difference between state and no state. The clear win for the state was the unassigned-task question on the held-out chat (a request that was never accepted). Without state the model wrongly said the chat does not say which tasks are unassigned. The state also gives the overview a structured, cited list, which the single-call answer does not.

## 4. What it still gets wrong, and why

1. **Inconsistent task names in the overview.** The extractor names the same work differently ("api", "api routes", "backend", "backend branch"; "domain registrar" vs "domain provider"), so one piece of work shows up as several rows or two decisions. Because of that, the handoff of "backend" did not update the "api" row, which still shows the old owner. I tried name merging by word overlap for decisions and deadlines only, because merging task names risks hiding real tasks.
2. **Missed tasks.** The extractor never produced Priya's seller dashboard task on the sample chat, so it is missing from the overview. The answers recover it when asked directly (Q10) but not when listing everything (Q12).
3. **Decisions vs statuses.** Things like "live deployed link" and "logo" are sometimes extracted as decisions or tasks.
4. **List questions (Q12).** Partial in every run. With state, the model sometimes drops items that are in the overview. Without state it once collapsed to a single line.
5. **Q17 (who actually paid?).** The model often answers the narrower fact it can support ("Aarav bought it") and does not say the chat is silent on who paid. Code-based state cannot help, because nothing in the state is about payment.
6. **Language.** Answers to English questions sometimes come back in Hinglish even though the prompt says to match the question.
7. **The evaluation itself.** The judge is an LLM and is sometimes too strict or too lenient, and I changed ground truth after seeing results (disclosed in section 3). The held-out set is only 5 questions, so one flip is within noise.
8. **Overfitting risk.** I tuned the extraction prompt while looking at the sample chat. The held-out chat is the check, and I did not tune on it.

## 5. What I'd do with 2 more days

[REWRITE; check the ranking is yours.]

1. **Canonicalise task and topic names** after extraction (merge duplicates with a second pass and explicit checks). It is the root cause of most overview noise on both chats, so it comes first.
2. **Build list answers straight from the state** (open, done, unassigned) and let the model only add detail. This should make Q12-type questions stable instead of depending on the model's enumeration.
3. **A check for "narrower than asked" answers and for answer language,** plus several runs per question with a majority vote, so the evaluation measures the system and not one lucky draw.

## 6. What I learned that I didn't know on day one

[WRITE THIS YOURSELF. Prompts: What surprised you about temperature 0? What did you learn from the judge being wrong? Why does "request is not assignment" matter? What changed about how you evaluate a model?]

## 7. What I understand deeply vs. what I accepted from AI

[WRITE THIS YOURSELF AND HONESTLY. Facts to place correctly: I used an AI assistant throughout, including for the code, the test-answer drafts and this draft of the notes. For each part below, say whether you can explain it line by line, partly, or not: parser, event validation, state rules, overview, QA prompt and citation checking, evaluation and judge. The expected answers were AI-assisted and I reviewed them against the chat.]

## 8. Demo video

Link to my 3-minute screen recording: https://youtu.be/GN9PvenDyc8?si=b2o0eSAK7tyKc5Yc
