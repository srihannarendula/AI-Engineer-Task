from datetime import datetime
from pathlib import Path

from chat_intel.models import MessageKind
from chat_intel.parser import parse_chat

CHAT = "data/team_chat.txt"


def by_id(messages, line_number):
    return next(m for m in messages if m.id == line_number)


def test_message_counts():
    msgs = parse_chat(CHAT)
    assert len(msgs) == 102  # 107 file lines minus 5 continuation lines
    kinds = [m.kind for m in msgs]
    assert kinds.count(MessageKind.SYSTEM) == 3
    assert kinds.count(MessageKind.MEDIA) == 4
    assert kinds.count(MessageKind.DELETED) == 1


def test_system_lines_have_no_sender():
    msgs = parse_chat(CHAT)
    assert by_id(msgs, 1).sender is None
    assert by_id(msgs, 2).kind == MessageKind.SYSTEM


def test_multiline_message_is_joined():
    m = by_id(parse_chat(CHAT), 17)
    assert m.sender == "Aarav"
    assert len(m.text.splitlines()) == 6
    assert "Main - deployment" in m.text


def test_timestamp_is_day_first_12_hour():
    m = by_id(parse_chat(CHAT), 33)
    assert m.timestamp == datetime(2026, 10, 12, 19, 30)


def test_edited_marker_removed_but_remembered():
    m = by_id(parse_chat(CHAT), 41)
    assert m.edited is True
    assert "<This message was edited>" not in m.text


def test_cite_format():
    assert by_id(parse_chat(CHAT), 90).cite() == "L90 | 10/11/26 09:12 PM | Kabir"


def test_works_on_a_different_chat(tmp_path: Path):
    other = tmp_path / "other.txt"
    other.write_text(
        "01/01/25, 10:05 AM - Ravi: hello\n"
        "still ravi, second line\n"
        "01/01/25, 10:06 AM - Sam: <Media omitted>\n",
        encoding="utf-8",
    )
    msgs = parse_chat(str(other))
    assert len(msgs) == 2
    assert msgs[0].text == "hello\nstill ravi, second line"
    assert msgs[1].kind == MessageKind.MEDIA
