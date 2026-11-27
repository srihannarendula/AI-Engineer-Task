# Evaluation results

- Run: 2026-11-26 23:21 | answering model: `gemini-3.5-flash-lite`
- Questions: 18 | automatic checks passed: 16
- Judge verdicts: 16 correct, 2 partial, 0 wrong, 0 not judged or errored
- Needs manual review: 2

| # | Question | Auto | Judge | Cited lines |
|---|---|---|---|---|
| 1 | What payment method are we using? | pass | correct | L67, L71 |
| 2 | Who owns auth now, and who owned it before? | pass | correct | L59, L79, L17 |
| 3 | When is demo day, and which earlier dates were announced? | pass | correct | L84, L85, L33, L75, L74, L76 |
| 4 | When is the report due, and how was that date worked out? | pass | correct | L86, L84, L85, L74, L76, L33 |
| 5 | Did Rohan finish the tests? | pass | correct | L89 |
| 6 | Who is doing search? | pass | correct | L96, L102, L97 |
| 7 | Which tasks does Kabir own right now? | pass | correct | L49, L79, L59, L72 |
| 8 | Deployment kaun kar raha hai aur kab tak ready hoga? | pass | correct | L17, L88 |
| 9 | Which hosting platform was chosen, and what was rejected? | pass | correct | L66, L65, L8, L9 |
| 10 | Priya abhi kis task pe kaam kar rahi hai? | pass | correct | L63 |
| 11 | Where was the domain bought, and how much did it cost? | pass | correct | L43 |
| 12 | Which tasks are unassigned, unfinished, or have no known status? | FAIL | partial | L50, L92 |
| 13 | What was decided at the 14 Nov team meeting? | pass | correct | L107, L102 |
| 14 | Why did Aarav switch the project to AWS? | pass | correct | L64, L65, L66 |
| 15 | Did Rohan finish authentication? | pass | correct | L57, L59, L90 |
| 16 | Is Razorpay fully integrated? | pass | correct | L67, L91 |
| 17 | Who actually paid for the domain? | FAIL | partial | L45 |
| 18 | Was the project deployed on Render? | pass | correct | L88 |

## Needs manual review

### Q12: Which tasks are unassigned, unfinished, or have no known status?

- **Expected:** Unassigned: search (L49, L96). Unfinished: tests (Rohan, still pending, L89); chat (Kabir, 70%, L90); payments webhook (Kabir, L91); seller dashboard (Priya, in progress, L94); deployment (Aarav planned it for 15 Nov, L88, but it is unconfirmed because the chat ends on 12 Nov). Unknown status: Meera owns report + PPT (L73), but the chat gives no progress update. Done: auth (L90), listings UI and filters (L63), domain (L45), schema v2 (L80).
- **System answered:** Search has no assigned owner [L50, L92].
- **Auto checks:** FAIL (evidence_ok=False, abstained=None, invalid citations=none)
- **Judge:** partial: The system answer only mentions unassigned search and misses all other unassigned, unfinished, or unknown status tasks.

### Q17: Who actually paid for the domain?

- **Expected:** Aarav bought it (L45). Meera suggested splitting the cost among the 5 members when the price looked like Rs 800 (L41), but no message says the split happened or that anyone paid Aarav back, so the chat does not say who finally paid.
- **System answered:** Aarav bought the domain [L45].
- **Auto checks:** FAIL (evidence_ok=None, abstained=False, invalid citations=none)
- **Judge:** partial: The system omitted that the chat does not say who ultimately paid or if the cost was split.

## All answers

**Q1.** What payment method are we using?

> Razorpay test mode is being used [L67, L71]. The earlier manual UPI QR method was dropped [L71].

**Q2.** Who owns auth now, and who owned it before?

> Auth ab Kabir ke paas hai [L59, L79], aur pehle Rohan ke paas tha [L17].

**Q3.** When is demo day, and which earlier dates were announced?

> Demo day is on **26 November 2026** [L84, L85]. 

Earlier dates announced were:
- **4 December 2026** (the initial demo day date) [L33, L75]
- **27 November 2026** (announced after being preponed, later corrected due to a typo in the notice) [L74, L76, L84]

**Q4.** When is the report due, and how was that date worked out?

> The report is due on **23 Nov** [L86]. 

This date was worked out based on the new Demo day (26 Nov) [L84, L85] after the college prepone notice [L74, L76] and typo correction [L84], following the original rule that the report is due 3 days before the demo day [L33, L86].

**Q5.** Did Rohan finish the tests?

> No, Rohan has not finished the tests yet; they are still pending, with a promise to do them by Sunday [L89].

**Q6.** Who is doing search?

> The chat doesn't say who is doing search yet [L96, L102]. It was discussed that Rohan is busy with schema + tests [L96] and Saturday (14 Nov) was set for a team meeting to discuss who will take on search [L97, L102].

**Q7.** Which tasks does Kabir own right now?

> Kabir currently owns:
- Chat [L49, L79]
- Auth [L59, L79]
- Payments [L72, L79]

**Q8.** Deployment kaun kar raha hai aur kab tak ready hoga?

> Aarav deployment kar raha hai aur deployment 15 Nov tak ready hoga [L17, L88].

**Q9.** Which hosting platform was chosen, and what was rejected?

> Render was chosen [L66], and AWS [L65] (and Firebase for the overall stack [L8, L9]) was rejected.

**Q10.** Priya abhi kis task pe kaam kar rahi hai?

> Priya abhi seller dashboard pe kaam kar rahi hai [L63].

**Q11.** Where was the domain bought, and how much did it cost?

> Namecheap se Rs 650 mein liya [L43].

**Q12.** Which tasks are unassigned, unfinished, or have no known status?

> Search has no assigned owner [L50, L92].

**Q13.** What was decided at the 14 Nov team meeting?

> The chat doesn't say what was decided at the 14 Nov meeting because the chat ends on 12 Nov [L107] and only shows the *agenda* for the meeting: who will take up search, and the deployment status [L102].

**Q14.** Why did Aarav switch the project to AWS?

> The chat doesn't say Aarav switched the project to AWS; in fact, the chat shows Aarav asked about AWS credits [L64], but Meera advised against it because of free tier bills, suggesting Render or Railway instead [L65]. Aarav then decided to use Render [L66].

**Q15.** Did Rohan finish authentication?

> No, Rohan did not finish authentication. He transferred authentication to Kabir because he was overloaded [L57, L59], and Kabir later finished and merged auth [L90].

**Q16.** Is Razorpay fully integrated?

> The chat doesn't say it is fully integrated. It shows that Kabir integrated Razorpay test mode and checkout is working, but the webhook is still remaining [L67, L91].

**Q17.** Who actually paid for the domain?

> Aarav bought the domain [L45].

**Q18.** Was the project deployed on Render?

> The chat doesn't say it was deployed yet, but Aarav states he is deploying it on Render with a target date of 15 Nov [L88].
