"""Scaffold generation: turn what the learner said (any mix of languages) into a
target sentence plus chunks, annotations, sound notes and help levels."""

import json
import re

from fastapi import HTTPException
from openai import OpenAI

from .config import settings
from .languages import CONTEXTS, L1_OPTIONS, LANGUAGES, REGISTERS
from .mock_convo import mock_converse
from .mock_data import mock_payload
from .schemas import (
    TAGS,
    Chunk,
    ConvLine,
    ConvListen,
    ConvNext,
    ConvRecast,
    ConverseRequest,
    ConverseResponse,
    Frame,
    Scaffold,
    ScaffoldRequest,
    Segment,
    Sound,
    Variant,
)

_client: OpenAI | None = None


def client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


SYSTEM = """You are SoftUtter, a warm, low-anxiety speech-scaffolding tutor.
The learner is learning {lang} ({native}). Their first language is {l1}. Approximate level: {cefr}.
Situation: {context}. Register: {formality}.

The learner's message may be in {lang}, in {l1}, or a mix of both (gaps they could not say). Your job:
1. Recast it as one natural {formality} {lang} sentence (at most two short ones). Keep the learner's own correct {lang} wherever possible and fill any gaps. Never scold.
2. Break the target into 2-4 short rhythm chunks (breath groups) for back-chaining practice.
3. Annotate sound details per chunk with segments. Segment texts must concatenate EXACTLY to the chunk text (keep spaces and punctuation).
   Tags: "none"; "care" (a sound learners often get wrong); "silent" (written but not pronounced, devoiced or reduced);
   "link" (liaison, linking, assimilation); "tone" (lexical tone or pitch accent worth watching).
   Tag only the 2-5 most useful spots in the whole sentence.
   For each item in "sounds", set "chunks" to the 0-based indices of the chunks where that sound occurs.
4. Focus areas for {lang}: {focus}.
5. Write meaning, feedback, tips, sound explanations and hints in {l1}. Keep each tip under 20 words.
6. Chunk texts joined with {joiner} must reproduce the target sentence exactly.

Return ONLY a JSON object with exactly these keys:
"""

SCHEMA_HINT = """{
  "target": "full target sentence in the target language's normal script",
  "meaning": "what the target means, in the learner's first language",
  "reading": "romaji for Japanese, romanization for Korean, pinyin with tone marks for Mandarin; empty string for other languages",
  "ipa": "broad IPA for the full sentence, in slashes",
  "feedback": "one encouraging sentence about what the learner did well",
  "gap_filled": ["target-language words you supplied for gaps"],
  "chunks": [{"text": "...", "ipa": "...", "reading": "...", "tip": "...", "segments": [{"text": "...", "tag": "none"}]}],
  "sounds": [{"symbol": "short symbol or character", "title": "...", "tip": "...", "tag": "care", "chunks": [0, 2]}],
  "hints": ["three hints that guide the learner without revealing the target sentence"],
  "frame": {"text": "the target sentence with ___ in place of 1-3 key words", "note": "..."},
  "variants": [{"label": "Polite", "text": "..."}, {"label": "Everyday", "text": "..."}, {"label": "Quick", "text": "..."}]
}"""


def build_system(req: ScaffoldRequest) -> str:
    lang = LANGUAGES[req.language]
    return (
        SYSTEM.format(
            lang=lang["name"],
            native=lang["native"],
            l1=L1_OPTIONS.get(req.l1, "English"),
            cefr=req.cefr,
            context=CONTEXTS.get(req.context, req.context),
            formality=REGISTERS.get(req.formality, "polite"),
            focus=lang["focus"],
            joiner="a single space" if lang["join"] else "no separator",
        )
        + SCHEMA_HINT
    )


def _tag(value) -> str:
    return value if value in TAGS else "none"


def _squash(text: str) -> str:
    return re.sub(r"\s+", "", text)


def normalize(data: dict, req: ScaffoldRequest, mock: bool = False) -> Scaffold:
    """Validate model output; repair what we can so the UI never breaks."""
    lang = LANGUAGES[req.language]
    target = str(data.get("target", "")).strip()
    if not target:
        raise ValueError("The model returned no target sentence.")

    chunks: list[Chunk] = []
    for c in data.get("chunks") or []:
        text = str(c.get("text", "")).strip()
        if not text:
            continue
        segs = [
            Segment(text=str(s.get("text", "")), tag=_tag(s.get("tag")))
            for s in (c.get("segments") or [])
            if s.get("text")
        ]
        if "".join(s.text for s in segs).strip() != text:
            segs = [Segment(text=text)]
        chunks.append(
            Chunk(
                text=text,
                ipa=str(c.get("ipa", "")),
                reading=str(c.get("reading", "")),
                tip=str(c.get("tip", "")),
                segments=segs,
            )
        )
    if not chunks or _squash(lang["join"].join(c.text for c in chunks)) != _squash(target):
        chunks = [
            Chunk(
                text=target,
                ipa=str(data.get("ipa", "")),
                reading=str(data.get("reading", "")),
                segments=[Segment(text=target)],
            )
        ]

    sounds = [
        Sound(
            symbol=str(s.get("symbol", "")),
            title=str(s.get("title", "")),
            tip=str(s.get("tip", "")),
            tag=_tag(s.get("tag")),
            chunks=[
                i
                for i in (s.get("chunks") or [])
                if isinstance(i, int) and 0 <= i < len(chunks)
            ],
        )
        for s in (data.get("sounds") or [])
        if s.get("title")
    ][:5]

    frame = None
    f = data.get("frame")
    if isinstance(f, dict) and f.get("text"):
        frame = Frame(text=str(f["text"]), note=str(f.get("note", "")))

    variants = [
        Variant(label=str(v.get("label", "")), text=str(v.get("text", "")))
        for v in (data.get("variants") or [])
        if v.get("text")
    ][:4]

    return Scaffold(
        language=req.language,
        source_text=req.text,
        l1=req.l1,
        context=req.context,
        formality=req.formality,
        target=target,
        meaning=str(data.get("meaning", "")),
        reading=str(data.get("reading", "")),
        ipa=str(data.get("ipa", "")),
        feedback=str(data.get("feedback", "")),
        gap_filled=[str(g) for g in (data.get("gap_filled") or [])],
        chunks=chunks,
        sounds=sounds,
        hints=[str(h) for h in (data.get("hints") or [])][:3],
        frame=frame,
        variants=variants,
        mock=mock,
    )


def generate_scaffold(req: ScaffoldRequest) -> Scaffold:
    if req.language not in LANGUAGES:
        raise HTTPException(400, f"Unsupported language: {req.language}")
    if settings.mock:
        return normalize(mock_payload(req.language), req, mock=True)
    try:
        resp = client().chat.completions.create(
            model=settings.llm_model,
            temperature=0.3,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": build_system(req)},
                {"role": "user", "content": req.text},
            ],
        )
        data = json.loads(resp.choices[0].message.content)
        return normalize(data, req)
    except HTTPException:
        raise
    except Exception as exc:  # network, auth, bad JSON...
        raise HTTPException(502, f"Scaffolding failed: {exc}") from exc


# ---------- conversation mode ----------
ROLES = {
    "cafe": "a friendly barista in a café",
    "meeting": "a friendly person the learner is meeting for the first time",
    "friends": "a friend chatting with the learner",
    "work": "a friendly colleague at work",
}
ROLE_LABELS = {"cafe": "Barista", "meeting": "New friend", "friends": "Friend", "work": "Colleague"}

CONVO_SYSTEM = """You are a warm conversation partner for a language learner, playing {role}.
The learner is learning {lang} ({native}). Their first language is {l1}. Level: {cefr}. Register: {formality}.
Situation: {context}. The conversation has {max_turns} learner turns; the learner has completed {turn}.

Rules:
- Stay in character and speak ONLY {lang}. Use simple, natural language for the level: one or two short sentences. Ask something the learner can answer in one short sentence.
- Never correct out loud. If the learner's last turn needs fixing, reply naturally and "recast" it: give the natural version in "recast.text" and one warm, short sentence in {l1} in "recast.note" (empty if nothing needed fixing; "changed" false then).
- The learner may answer in {l1} or mixed languages: recast it into {lang}.
- "listen" is ONE sound or rhythm detail worth hearing in your reply (tags: care, silent, link, tone), explained in {l1} in under 20 words.
- "next" helps the learner answer your reply: "answer" is a natural learner answer (one short sentence), "frame" is that answer with ___ replacing the key word(s), "hints" are two hints in {l1} that do not reveal the answer.
- Put readings in "reading" for Japanese (romaji), Korean (romanization) and Mandarin (pinyin with tone marks); otherwise "".
- If turn is 0, open the conversation. If turn equals {max_turns}, say a short goodbye, set "done" true and omit "next" and "listen".

Return ONLY a JSON object:
{{
  "recast": {{"text": "...", "reading": "...", "note": "...", "changed": true}},
  "reply": {{"text": "...", "reading": "...", "meaning": "meaning in {l1}"}},
  "listen": {{"symbol": "...", "title": "...", "tip": "...", "tag": "care"}},
  "next": {{"answer": "...", "reading": "...", "meaning": "...", "frame": "...", "hints": ["...", "..."]}},
  "done": false
}}
Omit "recast" when turn is 0."""


def _converse_system(req: ConverseRequest) -> str:
    lang = LANGUAGES[req.language]
    return CONVO_SYSTEM.format(
        role=ROLES.get(req.context, ROLES["friends"]),
        lang=lang["name"],
        native=lang["native"],
        l1=L1_OPTIONS.get(req.l1, "English"),
        cefr=req.cefr,
        formality=REGISTERS.get(req.formality, "polite"),
        context=CONTEXTS.get(req.context, req.context),
        max_turns=req.max_turns,
        turn=req.turn,
    )


def _line(d) -> ConvLine | None:
    if not isinstance(d, dict) or not str(d.get("text", "")).strip():
        return None
    return ConvLine(
        text=str(d["text"]).strip(), reading=str(d.get("reading", "")), meaning=str(d.get("meaning", ""))
    )


def normalize_converse(data: dict, req: ConverseRequest, mock: bool = False) -> ConverseResponse:
    """Validate model output so the chat UI never breaks."""
    reply = _line(data.get("reply"))
    if reply is None:
        raise ValueError("The model returned no reply.")
    done = bool(data.get("done")) or req.turn >= req.max_turns

    recast = None
    r = data.get("recast")
    if req.turn >= 1 and isinstance(r, dict) and str(r.get("text", "")).strip():
        recast = ConvRecast(
            text=str(r["text"]).strip(),
            reading=str(r.get("reading", "")),
            note=str(r.get("note", "")),
            changed=bool(r.get("changed", bool(r.get("note")))),
        )

    listen = None
    li = data.get("listen")
    if not done and isinstance(li, dict) and li.get("title"):
        listen = ConvListen(
            symbol=str(li.get("symbol", "")),
            title=str(li["title"]),
            tip=str(li.get("tip", "")),
            tag=_tag(li.get("tag")) if li.get("tag") in TAGS else "care",
        )

    nxt = None
    n = data.get("next")
    if not done and isinstance(n, dict) and str(n.get("answer", "")).strip():
        nxt = ConvNext(
            hints=[str(h) for h in (n.get("hints") or [])][:3],
            frame=str(n.get("frame", "")),
            answer=str(n["answer"]).strip(),
            reading=str(n.get("reading", "")),
            meaning=str(n.get("meaning", "")),
        )

    return ConverseResponse(
        role=str(data.get("role") or ROLE_LABELS.get(req.context, "Partner")),
        recast=recast,
        reply=reply,
        listen=listen,
        next=nxt,
        done=done,
        mock=mock,
    )


def generate_converse(req: ConverseRequest) -> ConverseResponse:
    if req.language not in LANGUAGES:
        raise HTTPException(400, f"Unsupported language: {req.language}")
    req.max_turns = max(3, min(8, req.max_turns))
    req.turn = max(0, min(req.max_turns, req.turn))
    if req.turn >= 1 and not req.user_text.strip():
        raise HTTPException(400, "Say or type something first.")
    if settings.mock:
        req.max_turns = 5  # the demo script is five turns long
        req.turn = min(req.turn, 5)
        return normalize_converse(mock_converse(req.language, req.turn, req.user_text), req, mock=True)
    messages = [{"role": "system", "content": _converse_system(req)}]
    for t in req.history[-16:]:
        messages.append({"role": "assistant" if t.role == "partner" else "user", "content": t.text})
    if req.turn >= 1:
        messages.append({"role": "user", "content": req.user_text})
    else:
        messages.append({"role": "user", "content": "(Begin the conversation.)"})
    try:
        resp = client().chat.completions.create(
            model=settings.llm_model,
            temperature=0.6,
            response_format={"type": "json_object"},
            messages=messages,
        )
        return normalize_converse(json.loads(resp.choices[0].message.content), req)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"The conversation partner failed: {exc}") from exc
