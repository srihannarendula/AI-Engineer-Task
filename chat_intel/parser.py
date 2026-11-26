"""Turn a WhatsApp export (.txt) into a list of Message objects.

Format handled:  DD/MM/YY, h:mm AM/PM - Sender: text
A line that does NOT start with a timestamp is a continuation of the
previous message (WhatsApp writes multi-line messages that way).
"""
import re
from datetime import datetime
from pathlib import Path
from typing import List

from chat_intel.models import Message, MessageKind

# \s also matches the narrow no-break space some exports put before AM/PM
LINE_START = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4}),\s(\d{1,2}:\d{2})\s?([AaPp][Mm])\s-\s(.*)$"
)
EDITED_MARK = "<This message was edited>"
MEDIA_TEXT = "<Media omitted>"
DELETED_TEXTS = {"This message was deleted", "You deleted this message"}


def _parse_timestamp(date_part: str, time_part: str, ampm: str) -> datetime:
    year_fmt = "%Y" if len(date_part.split("/")[-1]) == 4 else "%y"
    return datetime.strptime(
        f"{date_part} {time_part} {ampm.upper()}", f"%d/%m/{year_fmt} %I:%M %p"
    )


def _split_sender(rest: str):
    """'Aarav: hello' -> ('Aarav', 'hello'); system lines have no sender."""
    if ": " in rest:
        name, text = rest.split(": ", 1)
        if len(name) <= 50:
            return name, text
    return None, rest


def parse_chat(path: str) -> List[Message]:
    raw_lines = Path(path).read_text(encoding="utf-8-sig").splitlines()

    # Pass 1: group raw lines into messages (header line + continuations)
    blocks = []  # each: [line_number, timestamp, rest_text]
    for number, line in enumerate(raw_lines, start=1):
        line = line.replace("\u200e", "")  # invisible mark some exports add
        match = LINE_START.match(line)
        if match:
            ts = _parse_timestamp(match.group(1), match.group(2), match.group(3))
            blocks.append([number, ts, match.group(4)])
        elif blocks:
            blocks[-1][2] += "\n" + line
        # lines before the first timestamp are ignored

    # Pass 2: classify each block
    messages = []
    for number, ts, rest in blocks:
        sender, text = _split_sender(rest)
        text = text.rstrip()
        edited = EDITED_MARK in text
        if edited:
            text = text.replace(EDITED_MARK, "").strip()

        if sender is None:
            kind = MessageKind.SYSTEM
        elif text == MEDIA_TEXT:
            kind = MessageKind.MEDIA
        elif text in DELETED_TEXTS:
            kind = MessageKind.DELETED
        else:
            kind = MessageKind.MESSAGE

        messages.append(Message(number, ts, sender, text, kind, edited))
    return messages
