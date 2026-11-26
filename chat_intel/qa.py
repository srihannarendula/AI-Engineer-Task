"""Question answering over a parsed chat (first, simple version).

The whole chat is given to the model with strict rules. Our own code then
checks the line numbers the model cites and prints the real messages as
evidence, so the user never has to trust the model's quoting.
"""
import re
from dataclasses import dataclass
from typing import List

from chat_intel.llm import generate
from chat_intel.models import Message, MessageKind

CITE_RE = re.compile(r"\bL(\d+)\b")

SYSTEM_PROMPT = """You answer questions about the WhatsApp group chat of a college project team.
The chat mixes English and Hinglish. Each message looks like:
[L<line> | <date time> | <sender>] message

Rules:
1. Use ONLY the chat. Never use outside knowledge and never guess.
2. Messages are in time order. When a decision, owner or deadline changes, the LATEST valid one counts. Mention an older one only to explain the change.
3. A suggestion, a maybe ("shayad"), a question or a promise is NOT a final decision and NOT finished work. The word "done" can mean agreed, accepted or finished: read the context.
4. In a line like "Main - deployment", "main" means "I" (the sender).
5. Put the supporting line numbers right after each claim, like [L90]. Cite only line numbers that appear in the chat.
6. If the chat does not clearly answer, say "The chat doesn't say" and then state what the chat DOES show, with citations. Do not invent an owner, a status or a date.
7. Reply in the same language style as the question (English or Hinglish). Be short and direct."""


@dataclass
class Answer:
    text: str
    cited: List[int]      # cited line numbers that exist in the chat
    invalid: List[int]    # cited line numbers that do NOT exist (model error)


def build_transcript(messages: List[Message]) -> str:
    """One block per message, with its line number so it can be cited."""
    blocks = []
    for m in messages:
        if m.kind == MessageKind.SYSTEM:
            continue
        when = m.timestamp.strftime("%d/%m/%y %I:%M %p")
        if m.kind == MessageKind.MEDIA:
            body = "(sent a photo/file)"
        elif m.kind == MessageKind.DELETED:
            body = "(message was deleted)"
        else:
            body = m.text
        blocks.append(f"[L{m.id} | {when} | {m.sender}] {body}")
    return "\n".join(blocks)


def extract_citations(answer_text: str, messages: List[Message]):
    """Split the line numbers cited in the answer into real and non-existent."""
    real_ids = {m.id for m in messages}
    seen = []
    for number in (int(n) for n in CITE_RE.findall(answer_text)):
        if number not in seen:
            seen.append(number)
    cited = [n for n in seen if n in real_ids]
    invalid = [n for n in seen if n not in real_ids]
    return cited, invalid


def ask(messages: List[Message], question: str) -> Answer:
    prompt = (
        f"CHAT:\n{build_transcript(messages)}\n\n"
        f"QUESTION: {question}\n\nANSWER:"
    )
    text = generate(prompt, system=SYSTEM_PROMPT).strip()
    cited, invalid = extract_citations(text, messages)
    return Answer(text, cited, invalid)


def format_evidence(messages: List[Message], line_numbers: List[int]) -> str:
    """The real messages behind the cited lines, taken from the parsed chat."""
    by_id = {m.id: m for m in messages}
    out = []
    for n in line_numbers:
        m = by_id[n]
        body = m.text.replace("\n", "\n      ")
        out.append(f"  {m.cite()}\n      {body}")
    return "\n".join(out)
