"""Score the system on the hand-checked questions.

Two kinds of scoring, used together:
  1. Automatic checks (strict, no AI): valid citations, expected evidence cited,
     refusal wording when the chat cannot answer.
  2. A judge call: a second model call compares the answer's MEANING with the
     expected answer. It can be wrong too, so failures are always reviewed by hand.
"""
import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, List, Optional

from chat_intel.llm import DEFAULT_MODEL, generate
from chat_intel.qa import ask

VERDICTS = {"correct", "partial", "wrong"}

# Rough check that an answer admits the chat does not give the answer.
ABSTAIN_RE = re.compile(
    r"(doesn'?t|does not|didn'?t|did not) (say|confirm|show|mention|state|specify)"
    r"|not (clear|confirmed|mentioned|stated|specified)"
    r"|no (information|mention|confirmation|record)"
    r"|nahi (bataya|likha|hai)",
    re.IGNORECASE,
)

JUDGE_SYSTEM = """You grade an AI system that answers questions about a project team's WhatsApp chat.
You get the QUESTION, optionally a list of REQUIRED FACTS, the EXPECTED answer (written by a human who read the chat) and the SYSTEM answer.
Grade the MEANING, not the wording. Ignore citation markers like [L90].

Verdicts when REQUIRED FACTS are given:
- "correct": every required fact is present in the system answer, and nothing contradicts the expected answer.
- "partial": at least one required fact is missing, vague, or mixed with wrong claims.
- "wrong": it contradicts the expected answer, invents facts, or answers a different question.
Details that appear only in the EXPECTED text (not in the required facts) are background. Do NOT lower the verdict for omitting them.

When no REQUIRED FACTS are given, grade against the EXPECTED answer:
- "correct": agrees on all key facts and contradicts nothing.
- "partial": some key facts are right but important ones are missing, vague, or mixed with wrong claims.
- "wrong": contradicts it, invents facts, or answers a different question.

Special cases:
- If the expected answer says the chat does not say or confirm something, the system must clearly say so and must NOT present the missing fact as true.
- If the expected answer corrects a false premise in the question, the system must correct it and not play along.

Overclaim: set "overclaim" to true if the system presents as settled, complete or confirmed something that the expected answer describes as partial, only planned, unconfirmed or unknown. Otherwise false.

When REQUIRED FACTS are given, first check each one separately and list it in "facts" as "present" or "missing". A fact counts as present only if the system answer states it clearly. Then give the verdict.

Reply with JSON only: {"facts": [{"fact": "<text>", "status": "present" | "missing"}], "verdict": "correct" | "partial" | "wrong", "reason": "<one short sentence>", "overclaim": true | false}"""


@dataclass
class Result:
    qid: int
    question: str
    expected: str
    answer: str
    cited: List[int]
    invalid: List[int]
    expected_evidence: List[int]
    should_abstain: bool
    false_premise: bool
    evidence_ok: Optional[bool]    # None = not applicable
    abstained: Optional[bool]      # None = not applicable
    auto_pass: bool
    verdict: str = "not_judged"
    reason: str = ""
    error: str = ""

    @property
    def needs_review(self) -> bool:
        return bool(self.error) or not self.auto_pass or self.verdict != "correct"


def auto_checks(q: dict, answer_text: str, cited: List[int], invalid: List[int]):
    """Return (evidence_ok, abstained, auto_pass)."""
    expected = q.get("evidence_lines", [])
    if q.get("should_abstain") or not expected:
        evidence_ok = None
    else:
        evidence_ok = bool(set(cited) & set(expected))
    abstained = bool(ABSTAIN_RE.search(answer_text)) if q.get("should_abstain") else None
    auto_pass = not invalid and evidence_ok is not False and abstained is not False
    return evidence_ok, abstained, auto_pass


def parse_judge(text: str):
    """Read the judge's JSON reply; never crash on a badly formatted one."""
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        data = json.loads(cleaned)
        verdict = str(data.get("verdict", "")).lower()
        if verdict in VERDICTS:
            reason = str(data.get("reason", ""))
            if data.get("overclaim") is True:
                reason = "[OVERCLAIM] " + reason
            return verdict, reason
    except (ValueError, AttributeError):
        pass
    return "judge_error", f"could not read judge reply: {text[:80]!r}"


def judge(q: dict, answer_text: str):
    facts = q.get("required_facts")
    required = ""
    if facts:
        required = "REQUIRED FACTS (all must be present):\n" + "\n".join(f"- {f}" for f in facts) + "\n\n"
    prompt = (
        f"QUESTION: {q['question']}\n\n"
        f"{required}"
        f"EXPECTED (background): {q['expected_answer']}\n\n"
        f"SYSTEM ANSWER: {answer_text}\n"
    )
    raw = generate(prompt, system=JUDGE_SYSTEM, json_mode=True)
    verdict, reason = parse_judge(raw)
    if facts and verdict == "correct" and _any_missing(raw):
        verdict, reason = "partial", "[missing fact] " + reason
    return verdict, reason


def _any_missing(raw: str) -> bool:
    """True if the judge itself marked any required fact as missing."""
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        items = json.loads(cleaned).get("facts", [])
        return any(str(i.get("status", "")).lower() == "missing" for i in items)
    except (ValueError, AttributeError):
        return False


def run_evaluation(messages, questions: List[dict], use_judge: bool = True, overview: Optional[str] = None,
                   pause: float = 1.0, on_result: Callable = None) -> List[Result]:
    results = []
    for q in questions:
        try:
            answer = ask(messages, q["question"], overview=overview)
            evidence_ok, abstained, auto_pass = auto_checks(q, answer.text, answer.cited, answer.invalid)
            result = Result(q["id"], q["question"], q["expected_answer"], answer.text,
                            answer.cited, answer.invalid, q.get("evidence_lines", []),
                            q.get("should_abstain", False), q.get("false_premise", False),
                            evidence_ok, abstained, auto_pass)
            if use_judge:
                time.sleep(pause)
                result.verdict, result.reason = judge(q, answer.text)
        except RuntimeError:
            raise                               # e.g. missing API key: stop the whole run
        except Exception as err:                # one failed question must not kill the run
            result = Result(q["id"], q["question"], q["expected_answer"], "", [], [],
                            q.get("evidence_lines", []), q.get("should_abstain", False),
                            q.get("false_premise", False), None, None, False,
                            verdict="error", error=str(err)[:200])
        results.append(result)
        if on_result:
            on_result(result)
        time.sleep(pause)
    return results


def summarize(results: List[Result]) -> dict:
    return {
        "total": len(results),
        "auto_pass": sum(r.auto_pass for r in results),
        "correct": sum(r.verdict == "correct" for r in results),
        "partial": sum(r.verdict == "partial" for r in results),
        "wrong": sum(r.verdict == "wrong" for r in results),
        "other": sum(r.verdict not in VERDICTS for r in results),
        "needs_review": sum(r.needs_review for r in results),
    }


def _auto_label(r: Result) -> str:
    if r.error:
        return "ERROR"
    return "pass" if r.auto_pass else "FAIL"


def render_report(results: List[Result]) -> str:
    s = summarize(results)
    model = os.environ.get("LLM_MODEL", DEFAULT_MODEL)
    lines = [
        "# Evaluation results", "",
        f"- Run: {datetime.now():%Y-%m-%d %H:%M} | answering model: `{model}`",
        f"- Questions: {s['total']} | automatic checks passed: {s['auto_pass']}",
        f"- Judge verdicts: {s['correct']} correct, {s['partial']} partial, "
        f"{s['wrong']} wrong, {s['other']} not judged or errored",
        f"- Needs manual review: {s['needs_review']}", "",
        "| # | Question | Auto | Judge | Cited lines |", "|---|---|---|---|---|",
    ]
    for r in results:
        cited = ", ".join(f"L{n}" for n in r.cited) or "-"
        lines.append(f"| {r.qid} | {r.question} | {_auto_label(r)} | {r.verdict} | {cited} |")

    review = [r for r in results if r.needs_review]
    lines += ["", "## Needs manual review", ""]
    if not review:
        lines.append("Nothing flagged.")
    for r in review:
        lines += [f"### Q{r.qid}: {r.question}", "",
                  f"- **Expected:** {r.expected}",
                  f"- **System answered:** {r.answer or '(no answer)'}",
                  f"- **Auto checks:** {_auto_label(r)} (evidence_ok={r.evidence_ok}, "
                  f"abstained={r.abstained}, invalid citations={r.invalid or 'none'})",
                  f"- **Judge:** {r.verdict}: {r.reason or r.error}", ""]
    lines += ["## All answers", ""]
    for r in results:
        lines += [f"**Q{r.qid}.** {r.question}", "", f"> {r.answer or '(no answer)'}", ""]
    return "\n".join(lines)
