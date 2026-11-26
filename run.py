"""Ask questions about a WhatsApp chat export.

Usage:
  python run.py --chat data/team_chat.txt --question "Who owns auth?"
  python run.py --chat data/team_chat.txt          (interactive)
"""
import argparse
import sys

from chat_intel.parser import parse_chat
from chat_intel.qa import ask, format_evidence


def answer_and_print(messages, question):
    result = ask(messages, question)
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
    args = parser.parse_args()

    try:
        messages = parse_chat(args.chat)
    except FileNotFoundError:
        sys.exit(f"Chat file not found: {args.chat}")
    if not messages:
        sys.exit("No messages found. Is this a WhatsApp export in the expected format?")
    print(f"Loaded {len(messages)} messages from {args.chat}")

    try:
        if args.question:
            answer_and_print(messages, args.question)
        else:
            print("Ask a question (empty line to quit).")
            while True:
                question = input("> ").strip()
                if not question:
                    break
                answer_and_print(messages, question)
    except RuntimeError as err:   # e.g. missing API key
        sys.exit(f"Error: {err}")


if __name__ == "__main__":
    main()
