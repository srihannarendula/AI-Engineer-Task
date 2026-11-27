"""Render a ProjectState as a readable overview. Plain code, no LLM.

Every statement carries the chat line numbers it came from.
"""
from typing import List

from chat_intel.state import ProjectState, TaskState


def _l(n) -> str:
    return f"L{n}"


def _decisions(state: ProjectState) -> List[str]:
    out = ["CURRENT DECISIONS"]
    if not state.decisions:
        out.append("  (none found)")
    for d in state.decisions.values():
        if d.current:
            line = f"  - {d.topic}: {d.current} [{_l(d.current_line)}]"
            if d.confirmations:
                line += " (repeated " + ", ".join(_l(n) for n in d.confirmations) + ")"
            out.append(line)
            for value, n in d.history:
                out.append(f"      earlier: {value} [{_l(n)}] (replaced)")
        else:
            out.append(f"  - {d.topic}: nothing agreed yet")
        for value, n, who in d.proposals:
            out.append(f"      proposed, not agreed: {value} by {who} [{_l(n)}]")
    return out


def _deadlines(state: ProjectState) -> List[str]:
    out = ["DEADLINES"]
    if not state.deadlines:
        out.append("  (none found)")
    for d in state.deadlines.values():
        if d.current:
            out.append(f"  - {d.what}: {d.current} [{_l(d.current_line)}]")
        else:
            out.append(f"  - {d.what}: no confirmed date")
        for value, n in d.history:
            out.append(f"      earlier: {value} [{_l(n)}] (changed)")
        if d.pending:
            out.append(f"      tentative change, not confirmed: {d.pending[0]} [{_l(d.pending[1])}]")
    return out


def _status_text(t: TaskState) -> str:
    if t.status is None:
        return "no status reported in the chat"
    return f"{t.status.replace('_', ' ')} [{_l(t.status_line)}]"


def _extras(t: TaskState) -> List[str]:
    out = []
    if t.owner_inferred:
        out.append("owner inferred from a status update, never formally assigned")
    if len(t.promises) > 1:
        out.append(f"promised {len(t.promises)} times: " + ", ".join(_l(n) for n in t.promises))
    for who, n in t.requests:
        out.append(f"{who} was asked but has not accepted [{_l(n)}]")
    return out


def _tasks(state: ProjectState) -> List[str]:
    out = ["OPEN TASKS (owner, not done)"]
    open_tasks = sorted(state.open_tasks(), key=lambda t: t.name)
    if not open_tasks:
        out.append("  (none)")
    for t in open_tasks:
        out.append(f"  - {t.name}: {t.owner} [{_l(t.owner_line)}], {_status_text(t)}")
        out += [f"      {x}" for x in _extras(t)]

    out += ["", "DONE"]
    done = sorted(state.done_tasks(), key=lambda t: t.name)
    if not done:
        out.append("  (none)")
    for t in done:
        out.append(f"  - {t.name}: {t.owner or t.last_owner or 'unknown'} [{_l(t.status_line)}]")

    out += ["", "UNASSIGNED (no current owner, not done)"]
    free = sorted(state.unassigned(), key=lambda t: t.name)
    if not free:
        out.append("  (none)")
    for t in free:
        out.append(f"  - {t.name}")
        if t.last_owner:
            out.append(f"      last owner: {t.last_owner}")
        for who, n in t.drops:
            out.append(f"      dropped by {who} [{_l(n)}]")
        for who, n in t.requests:
            out.append(f"      asked {who}, no acceptance [{_l(n)}]")
        for who, n in t.declines:
            out.append(f"      declined by {who} [{_l(n)}]")
    return out


def render_overview(state: ProjectState) -> str:
    parts = _decisions(state) + [""] + _deadlines(state) + [""] + _tasks(state)
    return "\n".join(parts)
