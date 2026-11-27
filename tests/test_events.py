import json

import chat_intel.extractor as ex
from chat_intel.events import validate_event
from chat_intel.parser import parse_chat

CHAT = "data/team_chat.txt"


def by_id():
    return {m.id: m for m in parse_chat(CHAT)}


def good_status():
    return {"type": "status", "msg_id": 90, "task": "auth", "status": "done", "quote": "auth done, merged"}


def test_valid_event_takes_actor_from_the_chat_and_defaults_person():
    event, reason = validate_event(dict(good_status(), actor="SomeoneElse"), by_id())
    assert reason == "" and event.actor == "Kabir" and event.person == "Kabir"


def test_rejections():
    msgs = by_id()
    assert validate_event(dict(good_status(), type="rumour"), msgs)[0] is None
    assert "not a message" in validate_event(dict(good_status(), msg_id=999), msgs)[1]
    assert "quote not found" in validate_event(dict(good_status(), quote="tests are finished"), msgs)[1]
    assert "not one of" in validate_event(dict(good_status(), status="finished"), msgs)[1]
    assert "missing 'task'" in validate_event({k: v for k, v in good_status().items() if k != "task"}, msgs)[1]
    assert validate_event(dict(good_status(), msg_id=1), msgs)[0] is None     # system line has no sender


def test_quote_matching_ignores_case_and_spacing_and_accepts_L_prefix():
    event, _ = validate_event(dict(good_status(), msg_id="L90", quote="AUTH  DONE, merged"), by_id())
    assert event is not None and event.msg_id == 90


def test_multiline_message_gives_several_events():
    raw = {"type": "assignment", "msg_id": 17, "task": "auth", "person": "Rohan",
           "action": "assigned", "quote": "Rohan - auth (login/signup)"}
    event, reason = validate_event(raw, by_id())
    assert event is not None, reason


def test_windows_cover_everything():
    items = list(range(94))
    windows = list(ex.make_windows(items, 40, 8))
    assert len(windows) == 3 and windows[0][0] == 0 and windows[-1][-1] == 93
    assert len(list(ex.make_windows(list(range(36)), 40, 8))) == 1


def test_extract_dedupes_rejects_and_caches(monkeypatch, tmp_path):
    msgs = parse_chat(CHAT)
    calls = []
    good = {"type": "assignment", "msg_id": 59, "task": "auth", "person": "Kabir",
            "action": "accepted", "quote": "auth bhi le leta hoon"}
    fake = {"type": "assignment", "msg_id": 59, "task": "auth", "person": "Kabir",
            "action": "accepted", "quote": "never said this"}

    def fake_generate(prompt, system=None, **kw):
        calls.append(prompt)
        return json.dumps([good, fake]) if "[L59 " in prompt else "[]"

    monkeypatch.setattr(ex, "generate", fake_generate)
    result = ex.extract_events(msgs, cache_dir=str(tmp_path))
    assert len(result.events) == 1                       # L59 appears in two windows: deduped
    assert any("quote not found" in r["reason"] for r in result.rejected)
    assert any("Task names already in use: auth" in c for c in calls[1:])  # naming hint passed on
    n_calls = len(calls)
    again = ex.extract_events(msgs, cache_dir=str(tmp_path))
    assert len(calls) == n_calls and again.events == result.events     # second run: cache, no model calls


def test_unreadable_reply_is_recorded_not_fatal(monkeypatch, tmp_path):
    monkeypatch.setattr(ex, "generate", lambda *a, **k: "sorry, I cannot")
    result = ex.extract_events(parse_chat(CHAT), cache_dir=str(tmp_path))
    assert result.events == [] and len(result.rejected) == 3
