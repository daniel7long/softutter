"""Compare a learner's attempt with the target and produce soft, score-free feedback.

Pipeline: transcribe the attempt -> diff against target chunks -> (optional) Azure
word-level pronunciation scores -> short encouraging feedback (LLM, with a
deterministic fallback)."""

import difflib
import json
import re
import unicodedata

from .config import settings
from .languages import L1_OPTIONS, LANGUAGES
from .llm import client
from .speech import transcribe

_demo_attempts: dict[str, int] = {}


def _cjk(language: str) -> bool:
    return LANGUAGES[language]["join"] == "" or language == "ko"


def units(text: str, language: str) -> list[str]:
    t = unicodedata.normalize("NFKC", text).lower()
    if language in ("fr", "es", "de"):
        # speech recognition is inconsistent about accents; don't call that a pronunciation error
        t = "".join(c for c in unicodedata.normalize("NFD", t) if not unicodedata.combining(c))
    t = re.sub(r"[^\w\s]|_", "", t)
    if _cjk(language):
        return [c for c in t if not c.isspace()]
    return t.split()


def compare(target_chunks: list[str], heard: str, language: str) -> dict:
    tgt: list[str] = []
    owner: list[int] = []
    for i, chunk in enumerate(target_chunks):
        u = units(chunk, language)
        tgt += u
        owner += [i] * len(u)
    hu = units(heard, language)
    sm = difflib.SequenceMatcher(None, tgt, hu, autojunk=False)
    sep = "" if _cjk(language) else " "
    matched = [False] * len(tgt)
    issues: list[dict] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i1, i2):
                matched[k] = True
        elif tag in ("replace", "delete") and i1 < len(owner):
            issues.append(
                {
                    "chunk": owner[i1],
                    "expected": sep.join(tgt[i1:i2]),
                    "heard": sep.join(hu[j1:j2]),
                    "source": "transcript",
                }
            )
    chunks = []
    for i, text in enumerate(target_chunks):
        idx = [k for k, o in enumerate(owner) if o == i]
        ratio = sum(matched[k] for k in idx) / len(idx) if idx else 1.0
        chunks.append(
            {"text": text, "match": round(ratio, 2), "status": "good" if ratio >= 0.85 else "care"}
        )
    return {"chunks": chunks, "issues": issues}


def azure_word_scores(wav: bytes, text: str, locale: str):
    """Optional: per-word accuracy from Azure Speech. Returns None if unavailable."""
    if not settings.azure:
        return None
    try:
        import azure.cognitiveservices.speech as speechsdk

        cfg = speechsdk.SpeechConfig(
            subscription=settings.azure_key, region=settings.azure_region
        )
        cfg.speech_recognition_language = locale
        stream = speechsdk.audio.PushAudioInputStream(
            speechsdk.audio.AudioStreamFormat(
                samples_per_second=16000, bits_per_sample=16, channels=1
            )
        )
        audio_cfg = speechsdk.audio.AudioConfig(stream=stream)
        pa = speechsdk.PronunciationAssessmentConfig(
            reference_text=text,
            grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
            granularity=speechsdk.PronunciationAssessmentGranularity.Word,
            enable_miscue=True,
        )
        rec = speechsdk.SpeechRecognizer(speech_config=cfg, audio_config=audio_cfg)
        pa.apply_to(rec)
        stream.write(wav[44:])  # strip the 44-byte WAV header; PCM 16 kHz mono 16-bit
        stream.close()
        result = rec.recognize_once()
        scored = speechsdk.PronunciationAssessmentResult(result)
        return [{"word": w.word, "accuracy": w.accuracy_score} for w in scored.words]
    except Exception:
        return None


def merge_azure(comparison: dict, scores, language: str) -> None:
    if not scores:
        return
    for item in scores:
        if item["accuracy"] >= 70:
            continue
        word = "".join(units(item["word"], language))
        for chunk in comparison["chunks"]:
            if word and word in "".join(units(chunk["text"], language)):
                chunk["status"] = "care"
                comparison["issues"].append(
                    {
                        "chunk": comparison["chunks"].index(chunk),
                        "expected": item["word"],
                        "heard": "",
                        "source": "azure",
                    }
                )
                break


def fallback_feedback(comparison: dict) -> dict:
    good = [c["text"] for c in comparison["chunks"] if c["status"] == "good"]
    wins = [f"“{t}” came through clearly." for t in good[:2]]
    focus = None
    if comparison["issues"]:
        first = comparison["issues"][0]
        unit = first["expected"] or comparison["chunks"][first["chunk"]]["text"]
        focus = {
            "unit": unit,
            "tip": "Listen to the target once more, then try just this part slowly.",
        }
    elif not wins:
        wins = ["That was a close match."]
    return {"wins": wins or ["That was a close match."], "focus": focus}


def soft_feedback(target: str, heard: str, comparison: dict, language: str, l1: str) -> dict:
    base = fallback_feedback(comparison)
    if settings.mock:
        return base
    prompt = (
        f"A learner of {LANGUAGES[language]['name']} (first language: {L1_OPTIONS.get(l1, 'English')}) "
        "tried to repeat a target phrase.\n"
        f"Target: {target}\nHeard (speech recognition): {heard}\n"
        f"Chunk results: {json.dumps(comparison['chunks'], ensure_ascii=False)}\n"
        f"Differences: {json.dumps(comparison['issues'], ensure_ascii=False)}\n\n"
        "Write warm, specific, score-free feedback in the learner's first language. "
        'Return ONLY JSON: {"wins": [up to 2 short sentences about what went well], '
        '"focus": {"unit": "the one word or sound to fix next", "tip": "one concrete physical tip, max 25 words"} or null}. '
        "If the attempt matches, focus must be null. Never mention scores or percentages."
    )
    try:
        resp = client().chat.completions.create(
            model=settings.llm_model,
            temperature=0.3,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
        )
        data = json.loads(resp.choices[0].message.content)
        wins = [str(w) for w in (data.get("wins") or [])][:2]
        focus = data.get("focus")
        if isinstance(focus, dict) and focus.get("unit"):
            focus = {"unit": str(focus["unit"]), "tip": str(focus.get("tip", ""))}
        else:
            focus = None
        return {"wins": wins or base["wins"], "focus": focus}
    except Exception:
        return base


def assess(audio: bytes, filename: str, language: str, chunks: list[str], l1: str) -> dict:
    target = LANGUAGES[language]["join"].join(chunks) if LANGUAGES[language]["join"] else "".join(chunks)
    if settings.mock:
        key = target
        _demo_attempts[key] = _demo_attempts.get(key, 0) + 1
        heard = target
        comparison = compare(chunks, heard, language)
        if _demo_attempts[key] % 2 == 1:  # first try shows a gentle focus point
            comparison["chunks"][0]["status"] = "care"
            comparison["issues"].append(
                {"chunk": 0, "expected": chunks[0].split()[0] if " " in chunks[0] else chunks[0], "heard": "", "source": "demo"}
            )
        fb = fallback_feedback(comparison)
        return {"heard": heard, **comparison, **fb, "mock": True}

    heard = transcribe(audio, filename, language)["text"]
    comparison = compare(chunks, heard, language)
    scores = azure_word_scores(audio, target, LANGUAGES[language]["locale"])
    merge_azure(comparison, scores, language)
    fb = soft_feedback(target, heard, comparison, language, l1)
    return {"heard": heard, **comparison, **fb, "mock": False, "azure": scores is not None}
