import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import assess as assess_mod
from . import speech, store
from .config import settings
from .languages import LANGUAGES, public_languages
from .llm import generate_converse, generate_scaffold
from .schemas import (
    ConverseRequest,
    ConverseResponse,
    PhraseIn,
    PhraseStatus,
    Scaffold,
    ScaffoldRequest,
    SoundEventsIn,
)

MAX_AUDIO_BYTES = 8 * 1024 * 1024  # ~4 minutes of 16 kHz mono WAV


@asynccontextmanager
async def lifespan(_: FastAPI):
    store.init()
    yield


app = FastAPI(title="SoftUtter API", version="2.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _read_audio(audio: UploadFile) -> bytes:
    data = await audio.read()
    if not data:
        raise HTTPException(400, "Empty audio upload.")
    if len(data) > MAX_AUDIO_BYTES:
        raise HTTPException(413, "Recording is too long. Try a shorter phrase.")
    return data


@app.get("/api/health")
def health():
    return {"ok": True, "mock": settings.mock, "azure": settings.azure}


@app.get("/api/languages")
def languages():
    return public_languages()


@app.post("/api/scaffold", response_model=Scaffold)
def scaffold(req: ScaffoldRequest):
    return generate_scaffold(req)


@app.post("/api/converse", response_model=ConverseResponse)
def converse(req: ConverseRequest):
    return generate_converse(req)


@app.post("/api/transcribe")
async def transcribe(audio: UploadFile = File(...), language: str = Form(...)):
    data = await _read_audio(audio)
    return speech.transcribe(data, audio.filename or "speech.wav", language)


class TtsRequest(BaseModel):
    text: str
    language: str
    speed: float = 1.0


@app.post("/api/tts")
def tts(req: TtsRequest):
    if not req.text.strip() or len(req.text) > 400:
        raise HTTPException(400, "Text must be between 1 and 400 characters.")
    data = speech.synthesize(req.text, req.language, req.speed)
    if data is None:  # demo mode: the browser speaks
        return Response(status_code=204)
    return Response(content=data, media_type="audio/mpeg")


@app.post("/api/assess")
async def assess(
    audio: UploadFile = File(...),
    language: str = Form(...),
    chunks: str = Form(...),
    l1: str = Form("en"),
):
    if language not in LANGUAGES:
        raise HTTPException(400, f"Unsupported language: {language}")
    try:
        chunk_list = [str(c) for c in json.loads(chunks)]
    except Exception:
        raise HTTPException(400, "chunks must be a JSON list of strings.")
    if not chunk_list:
        raise HTTPException(400, "chunks must not be empty.")
    data = await _read_audio(audio)
    return assess_mod.assess(data, audio.filename or "speech.wav", language, chunk_list, l1)


@app.get("/api/phrases")
def phrases(language: str | None = None):
    return store.list_phrases(language)


@app.post("/api/phrases")
def add_phrase(p: PhraseIn):
    if p.language not in LANGUAGES:
        raise HTTPException(400, f"Unsupported language: {p.language}")
    return store.add_phrase(p.model_dump())


@app.patch("/api/phrases/{phrase_id}")
def update_phrase(phrase_id: int, body: PhraseStatus):
    if body.status not in store.STATUSES:
        raise HTTPException(400, "status must be one of: " + ", ".join(store.STATUSES))
    row = store.set_status(phrase_id, body.status)
    if row is None:
        raise HTTPException(404, "Phrase not found.")
    return row


@app.delete("/api/phrases/{phrase_id}", status_code=204)
def remove_phrase(phrase_id: int):
    store.delete_phrase(phrase_id)
    return Response(status_code=204)


@app.post("/api/sounds/events", status_code=204)
def sound_events(body: SoundEventsIn):
    if body.language not in LANGUAGES:
        raise HTTPException(400, f"Unsupported language: {body.language}")
    if not body.events or len(body.events) > 20:
        raise HTTPException(400, "Send between 1 and 20 events.")
    for e in body.events:
        if e.outcome not in store.SOUND_OUTCOMES:
            raise HTTPException(400, "outcome must be one of: " + ", ".join(store.SOUND_OUTCOMES))
    store.add_sound_events(body.language, [e.model_dump() for e in body.events])
    return Response(status_code=204)


@app.get("/api/sounds")
def sounds(language: str | None = None):
    return store.list_sounds(language)
