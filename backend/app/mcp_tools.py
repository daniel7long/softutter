"""The functions behind SoftUtter's MCP tools.

Plain Python, no MCP SDK imports, so they are easy to test and reuse. `mcp_server.py` registers them.
Errors are raised as ValueError (bad input) or RuntimeError (the model call failed); the MCP layer
turns them into tool errors the client can read.
"""

import logging

from fastapi import HTTPException

from . import store
from .config import settings
from .languages import CONTEXTS, L1_OPTIONS, LANGUAGES, REGISTERS
from .llm import generate_scaffold
from .schemas import ScaffoldRequest

SOUND_STATUSES = ("working", "new", "steady")
log = logging.getLogger(__name__)


def _lang(code: str | None) -> str:
    code = (code or "").strip().lower()
    if code not in LANGUAGES:
        raise ValueError(f"Unsupported language '{code}'. Use one of: {', '.join(LANGUAGES)}.")
    return code


def _maybe_lang(code: str | None) -> str | None:
    return _lang(code) if code and code.strip() else None


def _phrase_view(p: dict) -> dict:
    return {
        "id": p["id"],
        "language": p["language"],
        "target": p["target"],
        "meaning": p["meaning"],
        "reading": p["reading"],
        "status": p["status"],
        "saved_at": p["created_at"],
        "can_practice": bool((p.get("payload") or {}).get("chunks")),
    }


def list_languages() -> list[dict]:
    """The languages SoftUtter supports, with the code to pass to other tools."""
    return [{"code": v["code"], "name": v["name"], "native": v["native"]} for v in LANGUAGES.values()]


def list_phrases(language: str | None = None, status: str | None = None, limit: int = 50) -> list[dict]:
    """List phrases saved in the SoftUtter phrasebook, newest first.

    Args:
        language: Optional language code (fr, es, de, ja, ko, zh). Omit for all languages.
        status: Optional practice status: "new" (not practiced yet), "echo" (echoed with help), "own" (said on their own).
        limit: Maximum number of phrases to return (1-200).
    """
    if status and status not in store.STATUSES:
        raise ValueError("status must be one of: " + ", ".join(store.STATUSES))
    rows = store.list_phrases(_maybe_lang(language))
    if status:
        rows = [r for r in rows if r["status"] == status]
    limit = max(1, min(int(limit), 200))
    return [_phrase_view(r) for r in rows[:limit]]


def _minimal_scaffold(language: str, text: str, meaning: str) -> dict:
    """A one-chunk scaffold so a phrase saved as written can still be practiced in the app."""
    return {
        "language": language,
        "source_text": text,
        "l1": "en",
        "context": "friends",
        "formality": "polite",
        "target": text,
        "meaning": meaning,
        "reading": "",
        "ipa": "",
        "feedback": "",
        "gap_filled": [],
        "chunks": [{"text": text, "ipa": "", "reading": "", "tip": "", "segments": [{"text": text, "tag": "none"}]}],
        "sounds": [],
        "hints": [],
        "frame": None,
        "variants": [],
        "mock": True,
    }


def _scaffold(req: ScaffoldRequest):
    try:
        return generate_scaffold(req)
    except HTTPException as exc:
        # The detail can quote the provider's error (even a masked key), so keep it in the server log.
        log.warning("Scaffolding failed: %s", exc.detail)
        raise RuntimeError(
            "The language model call failed. Try again, or check the OpenAI key and quota on the server."
        ) from exc


def save_phrase(language: str, text: str, meaning: str = "") -> dict:
    """Save a sentence to the SoftUtter phrasebook so it can be practiced in the app.

    With an OpenAI key configured, the text may be in the target language, in English, or a mix: it is
    recast into a natural sentence with chunks and sound notes first. Without a key (demo mode) it is
    saved exactly as written.

    Args:
        language: Language code (fr, es, de, ja, ko, zh).
        text: The sentence to save (up to 300 characters).
        meaning: Optional meaning in English. Used only when the sentence is saved as written.
    """
    language = _lang(language)
    text = (text or "").strip()
    if not text or len(text) > 300:
        raise ValueError("text must be between 1 and 300 characters.")

    if settings.mock:
        payload = _minimal_scaffold(language, text, meaning.strip())
        note = "Saved as written (demo mode: no OpenAI key, so it was not recast or annotated)."
    else:
        payload = _scaffold(ScaffoldRequest(language=language, text=text, context="friends")).model_dump()
        note = "Recast into a natural sentence." if payload["target"] != text else "Saved."

    exists = any(p["target"] == payload["target"] for p in store.list_phrases(language))
    row = store.add_phrase(
        {
            "language": language,
            "target": payload["target"],
            "meaning": payload["meaning"],
            "reading": payload["reading"],
            "ipa": payload["ipa"],
            "payload": payload,
        }
    )
    out = _phrase_view(row)
    out["already_saved"] = exists
    out["note"] = "That sentence was already in the phrasebook." if exists else note
    return out


def set_phrase_status(phrase_id: int, status: str) -> dict:
    """Mark how well a saved phrase is going: "new", "echo" (said with help) or "own" (said on their own).

    Args:
        phrase_id: The id from list_phrases.
        status: One of "new", "echo", "own".
    """
    if status not in store.STATUSES:
        raise ValueError("status must be one of: " + ", ".join(store.STATUSES))
    row = store.set_status(int(phrase_id), status)
    if row is None:
        raise ValueError(f"No phrase with id {phrase_id}.")
    return _phrase_view(row)


def get_sounds(language: str | None = None, status: str | None = None) -> list[dict]:
    """The learner's "My sounds" tracker: pronunciation patterns and how they are going. No scores.

    Statuses: "working" = needed another go in a recent try, "new" = just getting started,
    "steady" = recent tries were clear.

    Args:
        language: Optional language code. Omit for all languages.
        status: Optional filter: "working", "new" or "steady".
    """
    if status and status not in SOUND_STATUSES:
        raise ValueError("status must be one of: " + ", ".join(SOUND_STATUSES))
    rows = store.list_sounds(_maybe_lang(language))
    if status:
        rows = [r for r in rows if r["status"] == status]
    return [
        {
            "language": r["language"],
            "title": r["title"],
            "symbol": r["symbol"],
            "tag": r["tag"],
            "tip": r["tip"],
            "status": r["status"],
            "attempts": r["attempts"],
            "clear": r["clear"],
            "care": r["care"],
            "history": r["history"],
        }
        for r in rows
    ]


def progress_summary(language: str | None = None) -> dict:
    """A snapshot for planning practice: phrase counts by status, sounds worth revisiting, phrases to practice next.

    Args:
        language: Optional language code. Omit for all languages.
    """
    lang = _maybe_lang(language)
    phrases = store.list_phrases(lang)
    sounds = store.list_sounds(lang)
    by_status = {s: sum(1 for p in phrases if p["status"] == s) for s in store.STATUSES}
    # Phrases already echoed with help come first: they are closest to being "own it".
    queue = [p for p in phrases if p["status"] == "echo"] + [p for p in phrases if p["status"] == "new"]
    return {
        "language": lang or "all",
        "phrases": {"total": len(phrases), **by_status},
        "sounds": {s: sum(1 for x in sounds if x["status"] == s) for s in SOUND_STATUSES},
        "revisit_sounds": [
            {"language": x["language"], "title": x["title"], "tip": x["tip"], "history": x["history"]}
            for x in sounds
            if x["status"] == "working"
        ][:3],
        "phrases_to_practice": [
            {"id": p["id"], "language": p["language"], "target": p["target"], "meaning": p["meaning"], "status": p["status"]}
            for p in queue
        ][:5],
    }


def scaffold_sentence(
    language: str, text: str, l1: str = "en", context: str = "cafe", formality: str = "polite"
) -> dict:
    """Turn what a learner can say (target language, their own language, or a mix) into a natural sentence.

    Returns the sentence, its meaning, practice chunks (for back-chaining), the sounds to watch, hints and
    a fill-in frame. Does not save anything: use save_phrase for that. Uses the OpenAI key; in demo mode it
    returns a sample café sentence.

    Args:
        language: Language code (fr, es, de, ja, ko, zh).
        text: What the learner wants to say (up to 300 characters).
        l1: The learner's own language code for explanations (en, zh, es, fr, de, ja, ko).
        context: One of cafe, meeting, friends, work.
        formality: "polite" or "casual".
    """
    language = _lang(language)
    text = (text or "").strip()
    if not text or len(text) > 300:
        raise ValueError("text must be between 1 and 300 characters.")
    if l1 not in L1_OPTIONS:
        raise ValueError("l1 must be one of: " + ", ".join(L1_OPTIONS))
    if context not in CONTEXTS:
        raise ValueError("context must be one of: " + ", ".join(CONTEXTS))
    if formality not in REGISTERS:
        raise ValueError("formality must be one of: " + ", ".join(REGISTERS))
    s = _scaffold(ScaffoldRequest(language=language, text=text, l1=l1, context=context, formality=formality))
    return {
        "language": s.language,
        "target": s.target,
        "meaning": s.meaning,
        "reading": s.reading,
        "ipa": s.ipa,
        "chunks": [{"text": c.text, "tip": c.tip} for c in s.chunks],
        "sounds": [{"title": x.title, "tag": x.tag, "tip": x.tip, "chunks": x.chunks} for x in s.sounds],
        "hints": s.hints,
        "frame": s.frame.text if s.frame else "",
        "variants": [{"label": v.label, "text": v.text} for v in s.variants],
        "demo": s.mock,
    }
