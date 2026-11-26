# Evaluation results

- Run: 2026-11-26 21:48 | answering model: `gemini-3.5-flash-lite`
- Questions: 18 | automatic checks passed: 17
- Judge verdicts: 11 correct, 7 partial, 0 wrong, 0 not judged or errored
- Needs manual review: 7

| # | Question | Auto | Judge | Cited lines |
|---|---|---|---|---|
| 1 | What payment method are we using? | pass | correct | L71 |
| 2 | Who owns auth now, and who owned it before? | pass | correct | L59, L79, L17 |
| 3 | When is demo day, and which earlier dates were announced? | pass | correct | L84, L85, L33, L75, L74, L76 |
| 4 | When is the report due, and how was that date worked out? | pass | correct | L86, L33, L74, L77, L84, L85 |
| 5 | Did Rohan finish the tests? | pass | correct | L89, L83 |
| 6 | Who is doing search? | pass | correct | L17, L49, L50, L94, L96, L102 |
| 7 | Which tasks does Kabir own right now? | pass | partial | L49, L79, L59, L90, L67, L72 |
| 8 | Deployment kaun kar raha hai aur kab tak ready hoga? | pass | correct | L17, L88 |
| 9 | Which hosting platform was chosen, and what was rejected? | pass | partial | L66, L65 |
| 10 | Priya abhi kis task pe kaam kar rahi hai? | pass | partial | L63 |
| 11 | Where was the domain bought, and how much did it cost? | pass | partial | L43 |
| 12 | Which tasks are unassigned, unfinished, or have no known status? | pass | partial | L92, L93, L94, L95, L96, L102, L90, L63, L49, L79, L67, L72, L91, L66, L88, L80, L89, L73, L86 |
| 13 | What was decided at the 14 Nov team meeting? | pass | correct | L102 |
| 14 | Why did Aarav switch the project to AWS? | pass | correct | L64, L65, L66 |
| 15 | Did Rohan finish authentication? | pass | correct | L57, L59, L90 |
| 16 | Is Razorpay fully integrated? | pass | partial | L67 |
| 17 | Who actually paid for the domain? | FAIL | partial | L43, L45 |
| 18 | Was the project deployed on Render? | pass | correct | L88 |

## Needs manual review

### Q7: Which tasks does Kabir own right now?

- **Expected:** Chat (70% done, L90), payments (took over from Meera on 02/11, L72; webhook still pending, L91) and auth (done and merged, L90). He gave up search (L49).
- **System answered:** The chat doesn't explicitly list all of Kabir's current tasks in one place, but it shows that he owns:
- Chat [L49, L79]
- Auth (taken over from Rohan) [L59, L79, L90]
- Payments (after Razorpay test mode was integrated) [L67, L72, L79]
- **Auto checks:** pass (evidence_ok=True, abstained=None, invalid citations=none)
- **Judge:** partial: The system mentions his tasks, but includes inaccuracies regarding auth and misses the status details provided in the expected answer.

### Q9: Which hosting platform was chosen, and what was rejected?

- **Expected:** Render was chosen (L66). AWS was rejected because Meera warned the free tier can still produce a bill (L65). Railway was mentioned as an alternative but not chosen.
- **System answered:** Render was chosen [L66], and AWS was rejected [L65].
- **Auto checks:** pass (evidence_ok=True, abstained=None, invalid citations=none)
- **Judge:** partial: The system correctly identified the chosen and rejected platforms, but omitted the details about why AWS was rejected and that Railway was mentioned.

### Q10: Priya abhi kis task pe kaam kar rahi hai?

- **Expected:** Seller dashboard (L63, L94). She finished the listings UI and filters on 26/10 (L63). On 12/11 she shared two logo options (L103) and Meera said she prefers the second, blue one (L106).
- **System answered:** Priya abhi seller dashboard pe kaam kar rahi hai [L63].
- **Auto checks:** pass (evidence_ok=True, abstained=None, invalid citations=none)
- **Judge:** partial: The system correctly identifies the current task, but misses the additional details about the logos mentioned in the expected answer.

### Q11: Where was the domain bought, and how much did it cost?

- **Expected:** campuscart.in was bought by Aarav on Namecheap for Rs 650 (L43, L45), after GoDaddy showed Rs 800/year (L40).
- **System answered:** The domain was bought from Namecheap for Rs 650 [L43].
- **Auto checks:** pass (evidence_ok=True, abstained=None, invalid citations=none)
- **Judge:** partial: The system correctly identified the registrar and cost, but omitted who bought it and the comparison with GoDaddy.

### Q12: Which tasks are unassigned, unfinished, or have no known status?

- **Expected:** Unassigned: search (L49, L96). Unfinished: tests (Rohan, still pending, L89); chat (Kabir, 70%, L90); payments webhook (Kabir, L91); seller dashboard (Priya, in progress, L94); deployment (Aarav planned it for 15 Nov, L88, but it is unconfirmed because the chat ends on 12 Nov). Unknown status: Meera owns report + PPT (L73), but the chat gives no progress update. Done: auth (L90), listings UI and filters (L63), domain (L45), schema v2 (L80).
- **System answered:** The chat doesn't say search is assigned to anyone (it is discussed in L92, L93, L94, L95, L96, L102). 

Here are the statuses of other tasks as shown in the chat:
- **Search:** Unassigned [L92].
- **Auth:** Done and merged [L90].
- **Listings UI & Seller Dashboard:** Priya is working on the seller dashboard [L63] after finishing listing UI + filters [L63].
- **Chat:** 70% done, handled by Kabir [L49, L79, L90].
- **Payments:** Kabir integrated test mode and checkout is working; webhook is pending [L67, L72, L91].
- **Deployment:** Aarav is deploying on Render [L66, L88] with a target of Nov 15 [L88].
- **DB Schema & Tests:** Rohan provided schema v2 [L80], but tests are pending [L89].
- **Report & PPT:** Fully handled by Meera [L73], due on Nov 23 [L86].
- **Auto checks:** pass (evidence_ok=True, abstained=None, invalid citations=none)
- **Judge:** partial: The system identifies unassigned and unfinished tasks well, but misses some details and miscategorizes tasks like report/PPT (unknown status) and deployment (unconfirmed due to chat end date).

### Q16: Is Razorpay fully integrated?

- **Expected:** Partly. Kabir integrated Razorpay in test mode and checkout works (L67); the payments webhook is still pending (L91). The chat does not mention a live (non-test) setup.
- **System answered:** Yes, Razorpay test mode has been integrated [L67].
- **Auto checks:** pass (evidence_ok=True, abstained=None, invalid citations=none)
- **Judge:** partial: The system confirms test mode integration but misses that it is only partly integrated and the webhook is still pending.

### Q17: Who actually paid for the domain?

- **Expected:** Aarav bought it (L45). Meera suggested splitting the cost among the 5 members when the price looked like Rs 800 (L41), but no message says the split happened or that anyone paid Aarav back, so the chat does not say who finally paid.
- **System answered:** Aarav bought the domain [L43, L45].
- **Auto checks:** FAIL (evidence_ok=None, abstained=False, invalid citations=none)
- **Judge:** partial: The system mentions who bought it initially, but fails to note that the chat does not confirm who ultimately paid for it.

## All answers

**Q1.** What payment method are we using?

> Razorpay test mode is being used [L71].

**Q2.** Who owns auth now, and who owned it before?

> Auth abhi Kabir ke paas hai [L59, L79], aur pehle Rohan ke paas tha [L17].

**Q3.** When is demo day, and which earlier dates were announced?

> Demo day is on **26 Nov** (Thursday) [L84, L85]. 

Earlier dates announced were:
- **4 Dec** (the original date) [L33, L75]
- **27 Nov** (the date after the first prepone notice) [L74, L76]

**Q4.** When is the report due, and how was that date worked out?

> Report due date is 23 Nov [L86]. 

Ye date aise aayi:
- Pehle Demo day 4 Dec tha, toh report 3 days pehle yaani 1 Dec batayi gayi thi [L33].
- Phir college ne demo day pehle karke 27 Nov (Friday) kar diya [L74], jisse report ki deadline 24 Nov discuss hui [L77].
- Fir Priya ne bataya ki sir se baat hui hai aur demo day 26 Nov (Thursday) hai (notice mein typo tha) [L84].
- Isliye final Demo day 26 Nov hone ki wajah se report ki deadline 23 Nov ho gayi [L85, L86].

**Q5.** Did Rohan finish the tests?

> No, Rohan has not finished the tests yet; they are still pending [L89]. He apologized that he couldn't do them and stated he will do them by that Sunday [L83, L89].

**Q6.** Who is doing search?

> The chat doesn't say who is doing search yet. 

The chat DOES show:
- Search was originally assigned to Kabir [L17].
- Kabir dropped it because it was too much with chat [L49], and Aarav said they would look at search later [L50].
- Priya said she couldn't take it because she is on the seller dashboard [L94].
- Rohan said he is on schema + tests and suggested discussing search on Saturday [L96].
- Discussing who will do search is on the agenda for the team meeting on Saturday, 14 Nov [L102].

**Q7.** Which tasks does Kabir own right now?

> The chat doesn't explicitly list all of Kabir's current tasks in one place, but it shows that he owns:
- Chat [L49, L79]
- Auth (taken over from Rohan) [L59, L79, L90]
- Payments (after Razorpay test mode was integrated) [L67, L72, L79]

**Q8.** Deployment kaun kar raha hai aur kab tak ready hoga?

> Aarav deployment kar raha hai aur 15 Nov tak ready hoga [L17, L88].

**Q9.** Which hosting platform was chosen, and what was rejected?

> Render was chosen [L66], and AWS was rejected [L65].

**Q10.** Priya abhi kis task pe kaam kar rahi hai?

> Priya abhi seller dashboard pe kaam kar rahi hai [L63].

**Q11.** Where was the domain bought, and how much did it cost?

> The domain was bought from Namecheap for Rs 650 [L43].

**Q12.** Which tasks are unassigned, unfinished, or have no known status?

> The chat doesn't say search is assigned to anyone (it is discussed in L92, L93, L94, L95, L96, L102). 

Here are the statuses of other tasks as shown in the chat:
- **Search:** Unassigned [L92].
- **Auth:** Done and merged [L90].
- **Listings UI & Seller Dashboard:** Priya is working on the seller dashboard [L63] after finishing listing UI + filters [L63].
- **Chat:** 70% done, handled by Kabir [L49, L79, L90].
- **Payments:** Kabir integrated test mode and checkout is working; webhook is pending [L67, L72, L91].
- **Deployment:** Aarav is deploying on Render [L66, L88] with a target of Nov 15 [L88].
- **DB Schema & Tests:** Rohan provided schema v2 [L80], but tests are pending [L89].
- **Report & PPT:** Fully handled by Meera [L73], due on Nov 23 [L86].

**Q13.** What was decided at the 14 Nov team meeting?

> The chat doesn't say what was decided at the 14 Nov team meeting. The chat ONLY shows the meeting agenda was decided beforehand: who will take up search and the deployment status [L102].

**Q14.** Why did Aarav switch the project to AWS?

> The chat doesn't say Aarav switched the project to AWS; instead, he asked about AWS credits [L64], but Meera advised against using AWS due to free tier bills and suggested Render or Railway [L65], leading Aarav to decide on Render instead [L66].

**Q15.** Did Rohan finish authentication?

> The chat doesn't say Rohan finished authentication. The chat shows that Rohan handed over authentication to Kabir [L57, L59], and Kabir later stated that auth was done and merged [L90].

**Q16.** Is Razorpay fully integrated?

> Yes, Razorpay test mode has been integrated [L67].

**Q17.** Who actually paid for the domain?

> Aarav bought the domain [L43, L45].

**Q18.** Was the project deployed on Render?

> The chat doesn't say it was deployed yet; Aarav states he is deploying on Render with a target date of 15 Nov [L88].
