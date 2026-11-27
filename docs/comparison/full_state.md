# Evaluation results

- Run: 2026-11-27 16:00 | answering model: `gemini-3.5-flash-lite`
- Questions: 18 | automatic checks passed: 17
- Judge verdicts: 16 correct, 2 partial, 0 wrong, 0 not judged or errored
- Needs manual review: 2

| # | Question | Auto | Judge | Cited lines |
|---|---|---|---|---|
| 1 | What payment method are we using? | pass | correct | L71 |
| 2 | Who owns auth now, and who owned it before? | pass | correct | L59, L79, L17, L57 |
| 3 | When is demo day, and which earlier dates were announced? | pass | correct | L85, L33, L74 |
| 4 | When is the report due, and how was that date worked out? | pass | correct | L86, L85, L33 |
| 5 | Did Rohan finish the tests? | pass | correct | L89 |
| 6 | Who is doing search? | pass | correct | L17, L49, L94, L96 |
| 7 | Which tasks does Kabir own right now? | pass | correct | L79, L72, L59 |
| 8 | Deployment kaun kar raha hai aur kab tak ready hoga? | pass | correct | L88 |
| 9 | Which hosting platform was chosen, and what was rejected? | pass | correct | L66, L65 |
| 10 | Priya abhi kis task pe kaam kar rahi hai? | pass | correct | L63, L94 |
| 11 | Where was the domain bought, and how much did it cost? | pass | correct | L43 |
| 12 | Which tasks are unassigned, unfinished, or have no known status? | pass | partial | L92, L94, L95, L79, L90, L72, L91, L17, L88, L60, L89, L73 |
| 13 | What was decided at the 14 Nov team meeting? | pass | correct | L97, L102 |
| 14 | Why did Aarav switch the project to AWS? | pass | correct | L64, L65, L66 |
| 15 | Did Rohan finish authentication? | pass | correct | L57, L59, L90 |
| 16 | Is Razorpay fully integrated? | pass | correct | L67, L91 |
| 17 | Who actually paid for the domain? | FAIL | partial | L45 |
| 18 | Was the project deployed on Render? | pass | correct | L88 |

## Needs manual review

### Q12: Which tasks are unassigned, unfinished, or have no known status?

- **Expected:** Unassigned: search (L49, L96). Unfinished: tests (Rohan, still pending, L89); chat (Kabir, 70%, L90); payments webhook (Kabir, L91); seller dashboard (Priya, in progress, L94); deployment (Aarav planned it for 15 Nov, L88, but it is unconfirmed because the chat ends on 12 Nov). Unknown status: Meera owns report + PPT (L73), but the chat gives no progress update. Done: auth (L90), listings UI and filters (L63), domain (L45), schema v2 (L80).
- **System answered:** Unassigned tasks (no current owner, not done):
- Search [L92, L94, L95]

Unfinished tasks (with owners):
- Chat (owner: Kabir, in progress) [L79, L90]
- Payments webhook (owner: Kabir, in progress) [L72, L91]
- Deployment (owner: Aarav, promised for 15 Nov) [L17, L88]
- Tests (owner: Rohan, promised for Sunday) [L60, L89]

Tasks with no known status reported in the chat:
- PPT (owner: Meera) [L73]
- Report (owner: Meera) [L73]
- **Auto checks:** pass (evidence_ok=True, abstained=None, invalid citations=none)
- **Judge:** partial: The system answer misses the seller dashboard task and the 70% progress detail for Kabir's chat.

### Q17: Who actually paid for the domain?

- **Expected:** Aarav bought it (L45). Meera suggested splitting the cost among the 5 members when the price looked like Rs 800 (L41), but no message says the split happened or that anyone paid Aarav back, so the chat does not say who finally paid.
- **System answered:** Aarav bought the domain [L45].
- **Auto checks:** FAIL (evidence_ok=None, abstained=False, invalid citations=none)
- **Judge:** partial: [OVERCLAIM] The system omitted that the chat does not say who ultimately paid or if the cost was split.

## All answers

**Q1.** What payment method are we using?

> Razorpay test mode [L71].

**Q2.** Who owns auth now, and who owned it before?

> Auth is owned by Kabir now [L59, L79], and Rohan owned it before [L17, L57].

**Q3.** When is demo day, and which earlier dates were announced?

> Demo day is on **26 Nov** [L85]. 

Earlier dates announced were:
- **4 Dec** [L33]
- **27 Nov** [L74]

**Q4.** When is the report due, and how was that date worked out?

> The report is due on **23 Nov** [L86]. 

It was worked out based on the demo day, which is scheduled for **26 Nov** [L85], since the report is due **3 days before** the demo day [L33].

**Q5.** Did Rohan finish the tests?

> The chat doesn't say that the tests are finished. The chat shows that tests are still pending, with Rohan promising to do them by that Sunday [L89].

**Q6.** Who is doing search?

> The chat doesn't say who is doing search. 

The chat shows that search was originally assigned to Kabir [L17], but Kabir dropped it [L49]. Priya declined it [L94], and Rohan suggested discussing it on Saturday [L96].

**Q7.** Which tasks does Kabir own right now?

> Kabir currently owns:
- Chat [L79]
- Payments [L72], [L79]
- Auth [L59], [L79]

**Q8.** Deployment kaun kar raha hai aur kab tak ready hoga?

> Deployment Aarav kar raha hai, aur yeh 15 Nov tak ready hoga [L88].

**Q9.** Which hosting platform was chosen, and what was rejected?

> Render ko choose kiya gaya [L66], aur AWS ko reject kiya gaya kyunki free tier ka bill aa jata hai [L65].

**Q10.** Priya abhi kis task pe kaam kar rahi hai?

> Priya abhi seller dashboard pe kaam kar rahi hai [L63, L94].

**Q11.** Where was the domain bought, and how much did it cost?

> Domain Namecheap se kharida gaya [L43] aur uska cost Rs 650 tha [L43].

**Q12.** Which tasks are unassigned, unfinished, or have no known status?

> Unassigned tasks (no current owner, not done):
- Search [L92, L94, L95]

Unfinished tasks (with owners):
- Chat (owner: Kabir, in progress) [L79, L90]
- Payments webhook (owner: Kabir, in progress) [L72, L91]
- Deployment (owner: Aarav, promised for 15 Nov) [L17, L88]
- Tests (owner: Rohan, promised for Sunday) [L60, L89]

Tasks with no known status reported in the chat:
- PPT (owner: Meera) [L73]
- Report (owner: Meera) [L73]

**Q13.** What was decided at the 14 Nov team meeting?

> The chat doesn't say what was decided at the 14 Nov team meeting. The chat only shows the meeting being planned for Saturday 14 Nov at 4 PM in the college library [L97], with an agenda to discuss who will take the search feature and check the deployment status [L102].

**Q14.** Why did Aarav switch the project to AWS?

> The chat doesn't say Aarav switched the project to AWS; in fact, Aarav asked about getting AWS credits [L64], but Meera advised against it [L65], and Aarav decided to use Render instead [L66].

**Q15.** Did Rohan finish authentication?

> No, Rohan did not finish authentication. He transferred the auth task to Kabir [L57, L59]. Kabir later completed and merged it [L90].

**Q16.** Is Razorpay fully integrated?

> The chat doesn't say Razorpay is fully integrated. It shows that Kabir integrated Razorpay test mode and checkout is working, but the webhook is still pending [L67, L91].

**Q17.** Who actually paid for the domain?

> Aarav bought the domain [L45].

**Q18.** Was the project deployed on Render?

> The chat doesn't say it was deployed yet, but Aarav promised to deploy it on Render by 15 Nov [L88].
