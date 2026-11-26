import chat_intel.qa as qa
from chat_intel.parser import parse_chat

CHAT = "data/team_chat.txt"


def test_transcript_skips_system_and_keeps_multiline():
    msgs = parse_chat(CHAT)
    transcript = qa.build_transcript(msgs)
    assert "end-to-end encrypted" not in transcript          # system line skipped
    assert "[L17 | 05/10/26 08:02 PM | Aarav] Task split karte hain:\nRohan - auth" in transcript
    assert "(sent a photo/file)" in transcript


def test_citations_split_into_real_and_invalid():
    msgs = parse_chat(CHAT)
    cited, invalid = qa.extract_citations("Kabir owns it [L59] and [L60], also [L999] and [L59].", msgs)
    assert cited == [59, 60]
    assert invalid == [999]


def test_ask_uses_model_answer_and_checks_citations(monkeypatch):
    msgs = parse_chat(CHAT)
    monkeypatch.setattr(qa, "generate", lambda prompt, system=None, **kw: "Auth is done [L90]. Also [L500].")
    result = qa.ask(msgs, "Who owns auth?")
    assert result.cited == [90]
    assert result.invalid == [500]


def test_prompt_contains_question_and_chat(monkeypatch):
    msgs = parse_chat(CHAT)
    seen = {}
    def fake(prompt, system=None, **kw):
        seen["prompt"], seen["system"] = prompt, system
        return "x"
    monkeypatch.setattr(qa, "generate", fake)
    qa.ask(msgs, "Who owns search?")
    assert "QUESTION: Who owns search?" in seen["prompt"]
    assert "[L90 | 10/11/26 09:12 PM | Kabir]" in seen["prompt"]
    assert "chat doesn't say" in seen["system"]
