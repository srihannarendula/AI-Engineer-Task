from chat_intel.events import Event
from chat_intel.overview import render_overview
from chat_intel.state import build_state


def ev(type_, line, **kw):
    return Event(type=type_, msg_id=line, actor="x", quote="q", **kw)


def test_overview_sections_and_citations():
    events = [
        ev("assignment", 1, person="a", task="search", action="assigned"),
        ev("assignment", 2, person="a", task="search", action="dropped"),
        ev("assignment", 3, person="b", task="ui", action="assigned"),
        ev("status", 4, person="b", task="ui", status="done"),
        ev("assignment", 5, person="c", task="api", action="assigned"),
        ev("decision", 6, topic="pay", value="upi", stage="agreed"),
        ev("deadline", 7, what="demo", date_text="4 Dec", stage="confirmed"),
    ]
    text = render_overview(build_state(events))
    assert "pay: upi [L6]" in text
    assert "demo: 4 Dec [L7]" in text
    assert "api: c [L5], no status reported in the chat" in text
    assert "ui: b [L4]" in text
    assert "dropped by a [L2]" in text and "last owner: a" in text


def test_empty_state_does_not_crash():
    assert "(none found)" in render_overview(build_state([]))
