from chat_intel.events import Event
from chat_intel.state import build_state


def ev(type_, line, **kw):
    return Event(type=type_, msg_id=line, actor=kw.pop("actor", "x"), quote="q", **kw)


def assign(line, person, task, action="assigned"):
    return ev("assignment", line, person=person, task=task, action=action)


def status(line, person, task, st):
    return ev("status", line, person=person, task=task, status=st)


def test_handoff_changes_owner_and_keeps_trail():
    s = build_state([assign(1, "a", "auth"), assign(5, "b", "auth", "accepted")])
    t = s.tasks["auth"]
    assert t.owner == "b" and t.last_owner == "b"
    assert (5, "owner a -> b") in t.trail


def test_request_does_not_change_owner_until_accepted():
    s = build_state([assign(1, "a", "auth"), assign(2, "b", "auth", "requested")])
    assert s.tasks["auth"].owner == "a"
    assert s.tasks["auth"].requests == [("b", 2)]
    s = build_state([assign(1, "a", "auth"), assign(2, "b", "auth", "requested"),
                     assign(3, "b", "auth", "accepted")])
    assert s.tasks["auth"].owner == "b" and s.tasks["auth"].requests == []


def test_decline_clears_that_request_only():
    s = build_state([assign(1, "a", "x"), assign(2, "b", "x", "requested"),
                     assign(3, "b", "x", "declined")])
    t = s.tasks["x"]
    assert t.owner == "a" and t.requests == [] and t.declines == [("b", 3)]


def test_drop_by_owner_makes_task_unassigned_and_remembers_who():
    s = build_state([assign(1, "a", "search"), assign(2, "a", "search", "dropped")])
    t = s.tasks["search"]
    assert t.owner is None and t.last_owner == "a" and t.drops == [("a", 2)]
    assert t in s.unassigned()


def test_drop_by_non_owner_changes_nothing():
    s = build_state([assign(1, "a", "x"), assign(2, "b", "x", "dropped")])
    assert s.tasks["x"].owner == "a"


def test_status_on_never_owned_task_infers_owner():
    s = build_state([status(3, "p", "dashboard", "in_progress")])
    t = s.tasks["dashboard"]
    assert t.owner == "p" and t.owner_inferred is True


def test_status_does_not_infer_owner_for_task_that_had_one():
    s = build_state([assign(1, "a", "x"), assign(2, "a", "x", "dropped"),
                     status(3, "b", "x", "in_progress")])
    assert s.tasks["x"].owner is None


def test_promise_is_not_done_and_is_counted():
    s = build_state([assign(1, "r", "tests"), status(2, "r", "tests", "promised"),
                     status(3, "r", "tests", "promised")])
    t = s.tasks["tests"]
    assert not t.is_done and t.promises == [2, 3] and t.status == "promised"


def test_latest_status_wins_and_done_needs_done_event():
    s = build_state([assign(1, "a", "x"), status(2, "a", "x", "in_progress"),
                     status(3, "a", "x", "done")])
    assert s.tasks["x"].is_done and s.tasks["x"] in s.done_tasks()
    assert s.tasks["x"] not in s.unassigned()


def test_promise_does_not_overwrite_in_progress():
    s = build_state([assign(1, "a", "x"), status(2, "a", "x", "in_progress"),
                     status(3, "a", "x", "promised")])
    assert s.tasks["x"].status == "in_progress"


def test_events_are_applied_in_line_order():
    s = build_state([assign(9, "b", "x", "accepted"), assign(1, "a", "x")])
    assert s.tasks["x"].owner == "b"


def test_open_tasks_have_owner_and_are_not_done():
    s = build_state([assign(1, "a", "x"), assign(2, "b", "y"), status(3, "b", "y", "done")])
    assert [t.name for t in s.open_tasks()] == ["x"]


def test_decision_latest_agreed_wins_with_history_and_pending_proposal():
    d = lambda line, val, stage: ev("decision", line, topic="pay", value=val, stage=stage)
    s = build_state([d(1, "razorpay", "agreed"), d(2, "upi", "proposed"),
                     d(3, "upi", "agreed"), d(4, "razorpay test", "proposed")])
    dec = s.decisions["pay"]
    assert dec.current == "upi" and dec.history == [("razorpay", 1)]
    assert [p[0] for p in dec.proposals] == ["razorpay test"]


def test_repeated_agreement_is_not_a_change():
    d = lambda line: ev("decision", line, topic="pay", value="UPI QR", stage="agreed")
    s = build_state([d(1), d(2)])
    assert s.decisions["pay"].history == [] and s.decisions["pay"].confirmations == [2]


def test_deadline_latest_confirmed_wins_and_tentative_is_pending():
    dl = lambda line, date, stage: ev("deadline", line, what="demo", date_text=date, stage=stage)
    s = build_state([dl(1, "4 Dec", "confirmed"), dl(2, "27 Nov", "confirmed"),
                     dl(3, "26 Nov", "tentative")])
    d = s.deadlines["demo"]
    assert d.current == "27 Nov" and d.history == [("4 Dec", 1)] and d.pending == ("26 Nov", 3)


def test_confirming_clears_pending():
    dl = lambda line, date, stage: ev("deadline", line, what="demo", date_text=date, stage=stage)
    s = build_state([dl(1, "4 Dec", "confirmed"), dl(2, "26 Nov", "tentative"),
                     dl(3, "26 Nov", "confirmed")])
    assert s.deadlines["demo"].pending is None and s.deadlines["demo"].current == "26 Nov"


def test_topic_names_that_drift_are_merged():
    s = build_state([ev("deadline", 1, what="demo day", date_text="4 Dec", stage="confirmed"),
                     ev("deadline", 2, what="demo", date_text="27 Nov", stage="confirmed")])
    assert list(s.deadlines) == ["demo day"] and s.deadlines["demo day"].current == "27 Nov"


def test_request_on_same_line_as_own_drop_is_ignored():
    s = build_state([assign(1, "k", "search"), assign(2, "k", "search", "dropped"),
                     assign(2, "k", "search", "requested")])
    assert s.tasks["search"].requests == []


def test_same_date_with_extra_words_is_not_a_change():
    dl = lambda line, date: ev("deadline", line, what="demo", date_text=date, stage="confirmed")
    s = build_state([dl(1, "27 Nov"), dl(2, "27 Nov (Friday)")])
    assert s.deadlines["demo"].history == []
