"""Data model for one parsed WhatsApp message."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class MessageKind(str, Enum):
    MESSAGE = "message"   # normal text from a person
    SYSTEM = "system"     # e.g. "Aarav added you", encryption notice
    MEDIA = "media"       # "<Media omitted>"
    DELETED = "deleted"   # "This message was deleted"


@dataclass(frozen=True)
class Message:
    id: int                      # line number in the file where the message starts
    timestamp: datetime
    sender: Optional[str]        # None for system lines
    text: str                    # full text, continuation lines joined
    kind: MessageKind = MessageKind.MESSAGE
    edited: bool = False

    def cite(self) -> str:
        """Short evidence string, e.g. 'L90 | 10/11/26 09:12 PM | Kabir'."""
        when = self.timestamp.strftime("%d/%m/%y %I:%M %p")
        who = self.sender or "system"
        return f"L{self.id} | {when} | {who}"
