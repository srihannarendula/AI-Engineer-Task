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

PROMPT_VERSION = "4"   # change when the prompt or schema changes, so old caches are ignored

SYSTEM_PROMPT = """You read part of a WhatsApp group chat of a team working on a project (English + Hinglish)
and extract EVENTS. Each message looks like: [L<line> | <date time> | <sender>] message

Return a JSON array. Each event is one of these four types:

{"type":"decision",   "msg_id":<line>, "topic":"...", "value":"...", "stage":"proposed"|"agreed", "quote":"..."}
{"type":"assignment", "msg_id":<line>, "task":"...", "person":"...", "action":"assigned"|"requested"|"accepted"|"declined"|"dropped", "quote":"..."}
{"type":"status",     "msg_id":<line>, "task":"...", "person":"...", "status":"in_progress"|"done"|"blocked"|"promised", "note":"...", "quote":"..."}
{"type":"deadline",   "msg_id":<line>, "what":"...", "date_text":"...", "stage":"tentative"|"confirmed", "quote":"..."}

Rules:
1. msg_id = line number of the message (the number after L). quote = a short exact piece (max 12 words) copied from THAT message. One message can give several events; use the same msg_id and quote the relevant part each time.
2. One task = one deliverable. NEVER put "+", "&" or "and" in a task name. Split lists into separate events: a line like "Sam - login + search" gives two assignments, "login" and "search". Likewise, if someone keeps one part and gives up another ("I'll do A, someone else take B"), give one event per part (accepted A, dropped B). Use the same short lowercase name every time for the same task. If a list of task names already in use is given, reuse them.
3. decision: for choices the team makes (tools, plans, methods). Include suggestions as stage "proposed" and settled choices as "agreed" ("final", "decided", "deal", or the person who owns that part states it). Keep every decision, even ones that were later reversed. A reply that agrees ("yes", "haan", "ok") to an earlier proposal is its own "agreed" event at the reply's line. Dates are NOT decisions: use deadline events for them. A single person's opinion or preference ("X looks better") is only "proposed". Meeting agendas and open questions are not decisions.
4. assignment: person = who would DO the work. "Main - <task>" or "I'll do <task>" means the sender does it. assigned = told or listed; requested = asking someone to take it; accepted = agreeing to take it; declined = refusing a request; dropped = giving up a task they had. A message that only says someone is busy or postpones the topic is not an acceptance.
5. status: done = clearly finished. If the message says first version, partly, or that something remains, use in_progress. A promise ("will do by tomorrow") is promised, even when repeated; a missed promise followed by a new promise is promised again. blocked = something outside the person stops the work (a missing approval, account or requirement). A person's own promised date for their task goes in "note" of a promised status, not in a deadline event. One message can hold several status events, each with its OWN task name taken from what its quoted words are about. Example: "login page done, now building the invoice export" gives {"type":"status","msg_id":<line>,"task":"login page","status":"done","quote":"login page done"} and {"type":"status","msg_id":<line>,"task":"invoice export","status":"in_progress","quote":"now building the invoice export"}.
6. deadline: only for team-wide dates (demo, submission, report, meeting). Emit one event per date mentioned. date_text is copied as written ("26 Nov", "this Sunday"); never calculate dates. tentative = maybe/"shayad"/question; confirmed = stated as fact, or agreed by a reply.
7. Person names exactly as written in the chat.
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
