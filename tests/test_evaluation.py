import chat_intel.evaluation as ev
from chat_intel.parser import parse_chat
from chat_intel.qa import Answer

Q_NORMAL = {"id": 1, "question": "q", "expected_answer": "e", "evidence_lines": [67, 71],
            "should_abstain": False, "false_premise": False}
Q_ABSTAIN = {"id": 2, "question": "q", "expected_answer": "e", "evidence_lines": [],
             "should_abstain": True, "false_premise": False}


def test_auto_checks_evidence():
    assert ev.auto_checks(Q_NORMAL, "x", [71], []) == (True, None, True)
    assert ev.auto_checks(Q_NORMAL, "x", [5], []) == (False, None, False)   # cited the wrong line
    assert ev.auto_checks(Q_NORMAL, "x", [71], [999])[2] is False           # invented line number


def test_auto_checks_abstention():
    assert ev.auto_checks(Q_ABSTAIN, "The chat doesn't say what was decided.", [], [])[1] is True
    assert ev.auto_checks(Q_ABSTAIN, "They decided to use Django.", [], []) == (None, False, False)


def test_parse_judge():
    assert ev.parse_judge('{"verdict": "correct", "reason": "ok"}') == ("correct", "ok")
    assert ev.parse_judge('```json\n{"verdict": "Partial", "reason": "missing date"}\n```') == ("partial", "missing date")
    assert ev.parse_judge("sure, looks fine!")[0] == "judge_error"
    assert ev.parse_judge('{"verdict": "great"}')[0] == "judge_error"


def test_run_evaluation_and_report(monkeypatch):
    msgs = parse_chat("data/team_chat.txt")
    answers = {"q1": Answer("Razorpay [L71]", [71], []), "q2": Answer("They chose Django [L500]", [], [500])}
    monkeypatch.setattr(ev, "ask", lambda m, question, overview=None: answers[question])
    monkeypatch.setattr(ev, "generate", lambda *a, **k: '{"verdict": "correct", "reason": "fine"}')
    questions = [dict(Q_NORMAL, question="q1"), dict(Q_ABSTAIN, question="q2")]
    results = ev.run_evaluation(msgs, questions, pause=0)
    assert [r.auto_pass for r in results] == [True, False]
    s = ev.summarize(results)
    assert s["total"] == 2 and s["auto_pass"] == 1 and s["needs_review"] == 1
    report = ev.render_report(results)
    assert "| 1 | q1 | pass | correct |" in report
    assert "## Needs manual review" in report and "### Q2" in report


def test_one_failing_question_does_not_stop_the_run(monkeypatch):
    msgs = parse_chat("data/team_chat.txt")
    def flaky(m, question, overview=None):
        if question == "boom":
            raise ValueError("model exploded")
        return Answer("ok [L71]", [71], [])
    monkeypatch.setattr(ev, "ask", flaky)
    results = ev.run_evaluation(msgs, [dict(Q_NORMAL, question="boom"), dict(Q_NORMAL, question="fine")],
                                use_judge=False, pause=0)
    assert results[0].verdict == "error" and "exploded" in results[0].error
    assert results[1].auto_pass is True


def test_overview_is_passed_through_to_ask(monkeypatch):
    msgs = parse_chat("data/team_chat.txt")
    seen = []
    def spy(m, question, overview=None):
        seen.append(overview)
        return Answer("ok [L71]", [71], [])
    monkeypatch.setattr(ev, "ask", spy)
    ev.run_evaluation(msgs, [dict(Q_NORMAL, question="a")], use_judge=False, pause=0, overview="STATE")
    ev.run_evaluation(msgs, [dict(Q_NORMAL, question="b")], use_judge=False, pause=0)
    assert seen == ["STATE", None]
