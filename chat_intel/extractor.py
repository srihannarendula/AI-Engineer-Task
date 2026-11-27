"""Read a chat and extract verified events, window by window."""
import hashlib
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List

from chat_intel.events import Event, validate_event
from chat_intel.llm import DEFAULT_MODEL, generate
from chat_intel.models import Message, MessageKind
from chat_intel.qa import build_transcript

PROMPT_VERSION = "1"   # change when the prompt or schema changes, so old caches are ignored

SYSTEM_PROMPT = """You read part of a WhatsApp group chat of a college project team (English + Hinglish)
and extract EVENTS. Each message looks like: [L<line> | <date time> | <sender>] message

Return a JSON array. Each event is one of these four types:

{"type":"decision",   "msg_id":<line>, "topic":"...", "value":"...", "stage":"proposed"|"agreed", "quote":"..."}
{"type":"assignment", "msg_id":<line>, "task":"...", "person":"...", "action":"assigned"|"requested"|"accepted"|"declined"|"dropped", "quote":"..."}
{"type":"status",     "msg_id":<line>, "task":"...", "person":"...", "status":"in_progress"|"done"|"blocked"|"promised", "note":"...", "quote":"..."}
{"type":"deadline",   "msg_id":<line>, "what":"...", "date_text":"...", "stage":"tentative"|"confirmed", "quote":"..."}

Rules:
1. "msg_id" is the line number of the message the event comes from (the number after L). "quote" must be copied EXACTLY from that message (a short piece, at most 12 words). One message can give several events, e.g. a task list gives one assignment per line; then use the same msg_id and quote that line.
2. decision: stage "agreed" only if the team clearly settled it ("final", "decided", "agreed", "deal"). A suggestion or question ("X bana lo?") is "proposed". Always include decisions that were later reversed.
3. assignment: "person" is the one who would DO the work. "Main - deployment" means the sender does deployment. "assigned" = told or listed; "requested" = asking someone to take it ("Kabir le sakta hai?"); "accepted" = agreeing to take it ("le leta hoon", "deal"); "declined" = refusing a request; "dropped" = giving up a task they had.
4. status: "done" only when the person says it is finished. A promise ("kal tak kar dunga", "I'll do by Sunday") is "promised", even if it is repeated. Work being done now is "in_progress". The word "done" alone can mean agreement, so read the context before choosing.
5. deadline: copy the date as written in the chat for "date_text" (like "26 Nov" or "this Sunday"); do not calculate dates. "tentative" for maybe/shayad/question, "confirmed" otherwise.
6. Use the SAME short task name every time for the same task (lowercase, e.g. "auth", "search", "payments", "tests", "deployment"). If a list of task names already in use is given, reuse those names.
7. Person names exactly as they appear in the chat.
8. Ignore greetings, jokes, photos and small talk. If a segment has no events, return [].
9. Output ONLY the JSON array."""


@dataclass
class ExtractionResult:
    events: List[Event]
    rejected: List[dict]    # {"raw": ..., "reason": ...} for every proposal that failed checking


def make_windows(messages: List[Message], size: int = 40, overlap: int = 8):
    """Overlapping chunks so an event spanning a boundary is not lost."""
    n = len(messages)
    start = 0
    while True:
        yield messages[start:start + size]
        if start + size >= n:
            break
        start += size - overlap


def _parse_json_list(text: str) -> list:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[4:] if text.lower().startswith("json") else text
    data = json.loads(text)
    if isinstance(data, dict):
        data = data.get("events", [])
    if not isinstance(data, list):
        raise ValueError("expected a JSON array")
    return data


def _event_key(e: Event):
    return (e.type, e.msg_id, (e.task or e.topic or e.what or "").lower(),
            (e.person or "").lower(), e.action, e.stage, e.status,
            (e.value or e.date_text or "").lower())


def _cache_path(messages: List[Message], cache_dir: str) -> Path:
    model = os.environ.get("LLM_MODEL", DEFAULT_MODEL)
    digest = hashlib.sha1(
        json.dumps([[m.id, m.sender, m.text] for m in messages] + [model, PROMPT_VERSION]).encode()
    ).hexdigest()[:16]
    return Path(cache_dir) / f"events_{digest}.json"


def extract_events(messages: List[Message], window: int = 40, overlap: int = 8,
                   use_cache: bool = True, cache_dir: str = ".cache") -> ExtractionResult:
    cache_file = _cache_path(messages, cache_dir)
    if use_cache and cache_file.exists():
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        return ExtractionResult([Event(**e) for e in data["events"]], data["rejected"])

    by_id = {m.id: m for m in messages}
    usable = [m for m in messages if m.kind == MessageKind.MESSAGE]
    events, rejected, seen, known_tasks = [], [], set(), []

    for chunk in make_windows(usable, window, overlap):
        hint = ""
        if known_tasks:
            hint = "Task names already in use: " + ", ".join(known_tasks) + "\n\n"
        prompt = f"{hint}CHAT SEGMENT:\n{build_transcript(chunk)}\n\nJSON array of events:"
        try:
            proposals = _parse_json_list(generate(prompt, system=SYSTEM_PROMPT, json_mode=True))
        except (ValueError, TypeError) as err:
            rejected.append({"raw": None, "reason": f"unreadable model reply for one window: {err}"})
            continue
        for raw in proposals:
            event, reason = validate_event(raw, by_id)
            if event is None:
                rejected.append({"raw": raw, "reason": reason})
                continue
            key = _event_key(event)
            if key in seen:
                continue
            seen.add(key)
            events.append(event)
            if event.task and event.task.lower() not in known_tasks:
                known_tasks.append(event.task.lower())

    events.sort(key=lambda e: e.msg_id)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(
        json.dumps({"events": [asdict(e) for e in events], "rejected": rejected},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    return ExtractionResult(events, rejected)
