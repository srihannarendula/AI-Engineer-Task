"""Print the project-state overview built from a chat.

Usage: python show_state.py --chat data/team_chat.txt [--refresh]
"""
import argparse
import sys

from chat_intel.extractor import extract_events
from chat_intel.overview import render_overview
from chat_intel.parser import parse_chat
from chat_intel.state import build_state


def main():
    p = argparse.ArgumentParser(description="Show the project state for a chat.")
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

    print(render_overview(build_state(result.events)))
    print(f"\n({len(result.events)} events used, {len(result.rejected)} rejected as unverifiable)")


if __name__ == "__main__":
    main()
