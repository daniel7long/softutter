"""Speech-to-text and text-to-speech (OpenAI), with a disk cache for TTS."""

import hashlib
import math

from fastapi import HTTPException

from .config import settings
from .languages import LANGUAGES
from .llm import client
from .mock_data import MOCK

LOW_CONFIDENCE = 0.6


def _tokens(logprobs):
    for lp in logprobs or []:
        if isinstance(lp, dict):
            yield lp.get("token", ""), lp.get("logprob", 0.0)
        else:
            yield getattr(lp, "token", ""), getattr(lp, "logprob", 0.0)


def uncertain_words(logprobs, join: str) -> list[str]:
    """Group token log-probs into words and return the low-confidence ones."""
    words: list[tuple[str, float]] = []
    cur, prob = "", 1.0
    for tok, logprob in _tokens(logprobs):
        p = math.exp(logprob)
        starts_word = tok.startswith(" ") or join == ""
        if starts_word and cur:
            words.append((cur.strip(), prob))
            cur, prob = "", 1.0
        cur += tok
        prob = min(prob, p)
    if cur:
        words.append((cur.strip(), prob))
    punct = " ,.!?;:。！？、，"
    return [w for w, p in words if p < LOW_CONFIDENCE and w.strip(punct)]


def transcribe(audio: bytes, filename: str, language: str) -> dict:
    if language not in LANGUAGES:
        raise HTTPException(400, f"Unsupported language: {language}")
    if settings.mock:
        return {"text": MOCK[language]["stt"], "uncertain": [], "mock": True}
    kwargs = dict(
        model=settings.stt_model,
        file=(filename or "speech.wav", audio, "audio/wav"),
        language=language,
    )
    try:
        try:
            resp = client().audio.transcriptions.create(
                **kwargs, response_format="json", include=["logprobs"]
            )
        except Exception:
            # e.g. whisper-1 has no logprobs: retry plain
            resp = client().audio.transcriptions.create(**kwargs)
        join = LANGUAGES[language]["join"]
        return {
            "text": (resp.text or "").strip(),
            "uncertain": uncertain_words(getattr(resp, "logprobs", None), join),
            "mock": False,
        }
    except Exception as exc:
        raise HTTPException(502, f"Transcription failed: {exc}") from exc


def synthesize(text: str, language: str, speed: float) -> bytes | None:
    """Return mp3 bytes, or None in demo mode (the browser speaks instead)."""
    if language not in LANGUAGES:
        raise HTTPException(400, f"Unsupported language: {language}")
    if settings.mock:
        return None
    speed = max(0.5, min(1.5, speed))
    key = hashlib.sha1(
        f"{settings.tts_model}|{settings.tts_voice}|{language}|{speed}|{text}".encode()
    ).hexdigest()
    path = settings.cache_dir / f"{key}.mp3"
    if path.exists():
        return path.read_bytes()
    try:
        resp = client().audio.speech.create(
            model=settings.tts_model,
            voice=settings.tts_voice,
            input=text,
            speed=speed,
            response_format="mp3",
        )
        data = resp.content
    except Exception as exc:
        raise HTTPException(502, f"Speech synthesis failed: {exc}") from exc
    path.write_bytes(data)
    return data
