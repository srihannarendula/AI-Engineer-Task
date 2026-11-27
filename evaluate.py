"""Run all hand-checked questions through the system and score them.

Usage:
  python evaluate.py
  python evaluate.py --only 5,12,14        (just some questions)
  python evaluate.py --no-judge            (automatic checks only)
"""
import argparse
import json
import sys
from pathlib import Path

from chat_intel.evaluation import render_report, run_evaluation, summarize
from chat_intel.parser import parse_chat
from run import build_overview


def main():
    p = argparse.ArgumentParser(description="Score the system on the evaluation questions.")
    p.add_argument("--chat", default="data/team_chat.txt")
    p.add_argument("--questions", default="tests/eval_questions.json")
    p.add_argument("--report", default="docs/eval_results.md", help="where to write the report")
    p.add_argument("--only", help="comma-separated question ids, e.g. 5,12,14")
    p.add_argument("--no-judge", action="store_true", help="skip the judge model call")
    p.add_argument("--pause", type=float, default=1.0, help="seconds between API calls")
    p.add_argument("--no-state", action="store_true", help="answer from the raw chat only (old single-call mode)")
    p.add_argument("--refresh", action="store_true", help="re-extract events instead of using the cache")
    args = p.parse_args()

    try:
        messages = parse_chat(args.chat)
        questions = json.loads(Path(args.questions).read_text(encoding="utf-8"))
    except FileNotFoundError as err:
        sys.exit(f"File not found: {err.filename}")
    except ValueError as err:
        sys.exit(f"{args.questions} is not valid JSON: {err}")
    if args.only:
        wanted = {int(x) for x in args.only.split(",")}
        questions = [q for q in questions if q["id"] in wanted]
    if not questions:
        sys.exit("No questions to run.")
    print(f"Running {len(questions)} questions on {len(messages)} messages...\n")

    def show(r):
        auto = "ERROR" if r.error else ("pass" if r.auto_pass else "FAIL")
        print(f"Q{r.qid:<3} auto={auto:<5} judge={r.verdict:<10} {r.question}")

    try:
        overview = None if args.no_state else build_overview(messages, args.refresh)
        results = run_evaluation(messages, questions, use_judge=not args.no_judge, overview=overview,
                                 pause=args.pause, on_result=show)
    except RuntimeError as err:
        sys.exit(f"Error: {err}")

    s = summarize(results)
    print(f"\nAuto checks passed: {s['auto_pass']}/{s['total']}")
    print(f"Judge: {s['correct']} correct, {s['partial']} partial, {s['wrong']} wrong, "
          f"{s['other']} other")
    print(f"Needs manual review: {s['needs_review']}")

    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(render_report(results), encoding="utf-8")
    print(f"\nFull report written to {args.report}")


if __name__ == "__main__":
    main()
