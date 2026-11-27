"""Print the events extracted from a chat, so they can be checked by eye.

Usage: python show_events.py --chat data/team_chat.txt [--refresh]
"""
import argparse
import sys

from chat_intel.extractor import extract_events
from chat_intel.parser import parse_chat


def describe(e) -> str:
    if e.type == "decision":
        return f"{e.stage:<9} {e.topic}: {e.value}"
    if e.type == "assignment":
        return f"{e.action:<9} {e.person} <- {e.task}"
    if e.type == "status":
        return f"{e.status:<11} {e.person} / {e.task}" + (f" ({e.note})" if e.note else "")
    return f"{e.stage:<9} {e.what}: {e.date_text}"


def main():
    p = argparse.ArgumentParser(description="Show events extracted from a chat.")
    p.add_argument("--chat", required=True)
    p.add_argument("--refresh", action="store_true", help="ignore the cache and ask the model again")
    args = p.parse_args()
    try:
        messages = parse_chat(args.chat)
    except FileNotFoundError:
        sys.exit(f"Chat file not found: {args.chat}")
    try:
        result = extract_events(messages, use_cache=not args.refresh)
    except RuntimeError as err:
        sys.exit(f"Error: {err}")

    for e in result.events:
        print(f"L{e.msg_id:<4} {e.actor:<7} {e.type:<10} {describe(e)}")
    print(f"\n{len(result.events)} events accepted, {len(result.rejected)} rejected")
    for r in result.rejected[:8]:
        print(f"  rejected: {r['reason']}")


if __name__ == "__main__":
    main()
