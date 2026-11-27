"""Ask questions about a WhatsApp chat export.

Usage:
  python run.py --chat data/team_chat.txt                     (overview, then questions)
  python run.py --chat data/team_chat.txt --question "Who owns auth?"
  python run.py --chat data/team_chat.txt --no-state          (single-call mode, no extraction)
  python run.py --chat data/team_chat.txt --refresh           (re-extract instead of using the cache)
"""
import argparse
import sys

from chat_intel.extractor import extract_events
from chat_intel.overview import render_overview
from chat_intel.parser import parse_chat
from chat_intel.qa import ask, format_evidence
from chat_intel.state import build_state


def build_overview(messages, refresh: bool):
    """Overview text built from extracted events, or None if extraction failed."""
    print("Reading the chat (the first run on a new chat makes a few model calls, then it is cached)...")
    try:
        result = extract_events(messages, use_cache=not refresh)
    except Exception as err:
        print(f"WARNING: could not build the project state ({err}). Answering from the raw chat only.")
        return None
    text = render_overview(build_state(result.events))
    if result.rejected:
        text += f"\n\n({len(result.rejected)} model-proposed facts were rejected because they could not be verified)"
    return text


def answer_and_print(messages, question, overview):
    result = ask(messages, question, overview=overview)
    print("\nANSWER")
    print(result.text)
    if result.cited:
        print("\nEVIDENCE (from the chat file)")
        print(format_evidence(messages, result.cited))
    if result.invalid:
        shown = ", ".join(f"L{n}" for n in result.invalid)
        print(f"\nWARNING: the answer cites lines that do not exist ({shown}). "
              "Do not trust those parts.")
    print()


def main():
    parser = argparse.ArgumentParser(description="Ask questions about a WhatsApp chat export.")
    parser.add_argument("--chat", required=True, help="path to the exported .txt chat")
    parser.add_argument("--question", help="a single question (omit for interactive mode)")
    parser.add_argument("--no-state", action="store_true",
                        help="skip event extraction and answer from the raw chat only")
    parser.add_argument("--refresh", action="store_true", help="ignore the cache and re-extract")
    parser.add_argument("--overview", action="store_true",
                        help="print the project overview even when a single question is given")
    args = parser.parse_args()

    try:
        messages = parse_chat(args.chat)
    except FileNotFoundError:
        sys.exit(f"Chat file not found: {args.chat}")
    if not messages:
        sys.exit("No messages found. Is this a WhatsApp export in the expected format?")
    print(f"Loaded {len(messages)} messages from {args.chat}")

    try:
        overview = None if args.no_state else build_overview(messages, args.refresh)
        if overview and (args.overview or not args.question):
            print("\n=== PROJECT OVERVIEW (built by code from the chat; line numbers are chat lines) ===")
            print(overview)
            print("=== END OVERVIEW ===\n")
        if args.question:
            answer_and_print(messages, args.question, overview)
        else:
            print("Ask a question (empty line to quit).")
            while True:
                question = input("> ").strip()
                if not question:
                    break
                answer_and_print(messages, question, overview)
    except RuntimeError as err:   # e.g. missing API key
        sys.exit(f"Error: {err}")


if __name__ == "__main__":
    main()
