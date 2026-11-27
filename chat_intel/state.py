"""State: turn validated events into the current project state.

Plain rules, no LLM. Events are applied in chat order and every piece of state
keeps the line numbers it came from, so every claim can be cited.
"""
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from chat_intel.events import Event


def _tokens(name: str) -> set:
    return set(re.findall(r"[a-z0-9]+", name.lower()))


def _same(a: str, b: str) -> bool:
    """Same text ignoring case, punctuation and spacing."""
    return " ".join(re.findall(r"[a-z0-9]+", a.lower())) == " ".join(re.findall(r"[a-z0-9]+", b.lower()))


def _canonical(name: str, known) -> str:
    """Reuse an earlier topic name if one name's words contain the other's
    (e.g. 'demo' vs 'demo day'). Otherwise this is a new topic."""
    words = _tokens(name)
    for key in known:
        other = _tokens(key)
        if words and other and (words <= other or other <= words):
            return key
    return name.strip().lower()


@dataclass
class TaskState:
    name: str
    owner: Optional[str] = None
    owner_line: Optional[int] = None
    owner_inferred: bool = False            # owner guessed from a status update
    last_owner: Optional[str] = None
    status: Optional[str] = None            # in_progress / done / blocked / promised / None
    status_line: Optional[int] = None
    promises: List[int] = field(default_factory=list)
    requests: List[Tuple[str, int]] = field(default_factory=list)   # pending (person, line)
    declines: List[Tuple[str, int]] = field(default_factory=list)
    drops: List[Tuple[str, int]] = field(default_factory=list)
    trail: List[Tuple[int, str]] = field(default_factory=list)      # (line, what happened)

    @property
    def is_done(self) -> bool:
        return self.status == "done"

    @property
    def is_unassigned(self) -> bool:
        return self.owner is None and not self.is_done


@dataclass
class DecisionState:
    topic: str
    current: Optional[str] = None
    current_line: Optional[int] = None
    confirmations: List[int] = field(default_factory=list)          # later lines repeating the same decision
    history: List[Tuple[str, int]] = field(default_factory=list)    # replaced decisions (value, line)
    proposals: List[Tuple[str, int, str]] = field(default_factory=list)  # (value, line, who), not yet agreed


@dataclass
class DeadlineState:
    what: str
    current: Optional[str] = None
    current_line: Optional[int] = None
    history: List[Tuple[str, int]] = field(default_factory=list)
    pending: Optional[Tuple[str, int]] = None   # a tentative date not yet confirmed


@dataclass
class ProjectState:
    tasks: Dict[str, TaskState] = field(default_factory=dict)
    decisions: Dict[str, DecisionState] = field(default_factory=dict)
    deadlines: Dict[str, DeadlineState] = field(default_factory=dict)

    def unassigned(self) -> List[TaskState]:
        return [t for t in self.tasks.values() if t.is_unassigned]

    def open_tasks(self) -> List[TaskState]:
        return [t for t in self.tasks.values() if t.owner and not t.is_done]

    def done_tasks(self) -> List[TaskState]:
        return [t for t in self.tasks.values() if t.is_done]


def _task(state: ProjectState, name: str) -> TaskState:
    return state.tasks.setdefault(name, TaskState(name))


def _apply_assignment(state: ProjectState, e: Event) -> None:
    t = _task(state, e.task)
    who = e.person
    if e.action in ("assigned", "accepted"):
        if t.owner and t.owner != who:
            t.trail.append((e.msg_id, f"owner {t.owner} -> {who}"))
        else:
            t.trail.append((e.msg_id, f"{e.action}: {who}"))
        t.owner, t.owner_line, t.owner_inferred = who, e.msg_id, False
        t.last_owner = who
        t.requests = [r for r in t.requests if r[0] != who]
    elif e.action == "requested":                 # asking someone does not change the owner
        t.requests.append((who, e.msg_id))
        t.trail.append((e.msg_id, f"requested: {who}"))
    elif e.action == "declined":                  # only clears that person's pending request
        t.requests = [r for r in t.requests if r[0] != who]
        t.declines.append((who, e.msg_id))
        t.trail.append((e.msg_id, f"declined: {who}"))
    elif e.action == "dropped":
        t.drops.append((who, e.msg_id))
        t.trail.append((e.msg_id, f"dropped: {who}"))
        if t.owner == who:                        # only the current owner can give it up
            t.owner, t.owner_line, t.owner_inferred = None, None, False


def _apply_status(state: ProjectState, e: Event) -> None:
    t = _task(state, e.task)
    # Someone reports on a task nobody ever owned: they are the owner.
    if t.owner is None and t.last_owner is None and e.person:
        t.owner, t.owner_line, t.owner_inferred, t.last_owner = e.person, e.msg_id, True, e.person
        t.trail.append((e.msg_id, f"owner inferred from status: {e.person}"))
    if e.status == "promised":
        t.promises.append(e.msg_id)               # a promise is recorded, never counted as progress
        t.trail.append((e.msg_id, "promised"))
        if t.status in (None, "promised", "blocked"):
            t.status, t.status_line = "promised", e.msg_id
        return
    t.status, t.status_line = e.status, e.msg_id  # otherwise the latest status wins
    t.trail.append((e.msg_id, f"status: {e.status}"))


def _apply_decision(state: ProjectState, e: Event) -> None:
    key = _canonical(e.topic, state.decisions)
    d = state.decisions.setdefault(key, DecisionState(key))
    if e.stage == "agreed":
        if d.current and _same(d.current, e.value):
            d.confirmations.append(e.msg_id)
            return
        if d.current:
            d.history.append((d.current, d.current_line))
        d.current, d.current_line = e.value, e.msg_id
        d.proposals = []                          # earlier proposals are now settled
    else:  # proposed
        if d.current and _same(d.current, e.value):
            return
        d.proposals = [p for p in d.proposals if not _same(p[0], e.value)]
        d.proposals.append((e.value, e.msg_id, e.actor))


def _apply_deadline(state: ProjectState, e: Event) -> None:
    key = _canonical(e.what, state.deadlines)
    d = state.deadlines.setdefault(key, DeadlineState(key))
    if e.stage == "confirmed":
        if d.current and not _same(d.current, e.date_text):
            d.history.append((d.current, d.current_line))
        d.current, d.current_line, d.pending = e.date_text, e.msg_id, None
    else:  # tentative
        if d.current and _same(d.current, e.date_text):
            return
        d.pending = (e.date_text, e.msg_id)


_HANDLERS = {
    "assignment": _apply_assignment,
    "status": _apply_status,
    "decision": _apply_decision,
    "deadline": _apply_deadline,
}


def build_state(events: List[Event]) -> ProjectState:
    state = ProjectState()
    for e in sorted(events, key=lambda ev: ev.msg_id):    # stable: same-line events keep their order
        _HANDLERS[e.type](state, e)
    return state
