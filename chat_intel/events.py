"""Events: small structured facts the model reads out of messages.

The model only PROPOSES events. Every proposal is checked against the real
chat here, and anything that cannot be verified is rejected.
"""
import re
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from chat_intel.models import Message

EVENT_TYPES = {"decision", "assignment", "status", "deadline"}

ALLOWED_VALUES = {
    ("decision", "stage"): {"proposed", "agreed"},
    ("assignment", "action"): {"assigned", "requested", "accepted", "declined", "dropped"},
    ("status", "status"): {"in_progress", "done", "blocked", "promised"},
    ("deadline", "stage"): {"tentative", "confirmed"},
}

REQUIRED_FIELDS = {
    "decision": ["topic", "value", "stage"],
    "assignment": ["task", "person", "action"],
    "status": ["task", "status"],
    "deadline": ["what", "date_text", "stage"],
}


@dataclass(frozen=True)
class Event:
    type: str
    msg_id: int                    # line number of the message the event comes from
    actor: str                     # who wrote that message (taken from the chat, not the model)
    quote: str                     # exact words from that message, checked by code
    task: Optional[str] = None
    person: Optional[str] = None
    action: Optional[str] = None   # assignment: assigned / requested / accepted / declined / dropped
    topic: Optional[str] = None
    value: Optional[str] = None
    stage: Optional[str] = None    # decision: proposed / agreed; deadline: tentative / confirmed
    status: Optional[str] = None   # in_progress / done / blocked / promised
    what: Optional[str] = None
    date_text: Optional[str] = None
    note: Optional[str] = None


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _clean(value) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parse_msg_id(value) -> Optional[int]:
    match = re.search(r"\d+", str(value))
    return int(match.group()) if match else None


def validate_event(raw: dict, by_id: Dict[int, Message]) -> Tuple[Optional[Event], str]:
    """Return (event, "") if the proposal checks out, else (None, reason)."""
    if not isinstance(raw, dict):
        return None, "not an object"
    etype = _clean(raw.get("type"))
    if etype not in EVENT_TYPES:
        return None, f"unknown type {etype!r}"

    msg_id = _parse_msg_id(raw.get("msg_id"))
    message = by_id.get(msg_id)
    if message is None or message.sender is None:
        return None, f"msg_id {raw.get('msg_id')!r} is not a message in the chat"

    quote = _clean(raw.get("quote"))
    if not quote or len(quote) < 3:
        return None, "missing quote"
    if _norm(quote) not in _norm(message.text):
        return None, f"quote not found in L{msg_id}"

    fields = {k: _clean(raw.get(k)) for k in
              ("task", "person", "action", "topic", "value", "stage",
               "status", "what", "date_text", "note")}
    for name in REQUIRED_FIELDS[etype]:
        if not fields[name]:
            return None, f"{etype} is missing '{name}'"
    for (t, field), allowed in ALLOWED_VALUES.items():
        if t == etype and fields[field] not in allowed:
            return None, f"{field}={fields[field]!r} is not one of {sorted(allowed)}"

    # Code rule: task names are lowercase, and one task = one deliverable.
    if fields["task"]:
        fields["task"] = fields["task"].lower()
        if re.search(r"\s(\+|&|and)\s", fields["task"]):
            return None, f"compound task name {fields['task']!r} (one event per task)"

    # Code rule: a status update with no named person is about the sender.
    if etype == "status" and not fields["person"]:
        fields["person"] = message.sender

    return Event(type=etype, msg_id=msg_id, actor=message.sender, quote=quote, **fields), ""
