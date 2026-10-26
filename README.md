# SoftUtter 2.0

Friendly speech scaffolding for six languages: **French, Spanish, German, Japanese, Korean, Mandarin Chinese**.
Say it however you can (speak, type, or mix in your own language) and SoftUtter gives you a natural version,
annotated sounds, chunked practice and soft, score-free feedback.

## Stack

| Layer | Choice | Why |
| --- | --- | --- |
| Frontend | React 19 + Vite (JavaScript) | Custom UI from the redesign (waveforms, annotated text, stepper) is awkward in Streamlit |
| Backend | FastAPI (Python) | Same family as Langogo; clean async uploads; easy to add auth and pronunciation scoring |
| LLM | OpenAI chat (JSON mode), model via `OPENAI_LLM_MODEL` | One call returns target, chunks, annotations, hints, frame and variants for all 3 help levels |
| Speech to text | OpenAI transcription, with token log-probs | Flags uncertain words so the learner can fix them |
| Text to speech | OpenAI TTS, cached on disk | Multilingual, supports 0.6x speed; browser voices are the fallback |
| Pronunciation | Optional Azure Speech word-level scores | Reuse your Langogo Azure setup; falls back to transcript diff |
| Storage | SQLite (`backend/data/softutter.db`) | Zero-setup phrasebook for one local user |

Recording is encoded in the browser as 16 kHz mono WAV, so there is **no ffmpeg dependency**.

## Run it (Windows PowerShell)

Terminal 1, backend:

```powershell
cd softutter\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # if blocked: Set-ExecutionPolicy -Scope Process Bypass
pip install -r requirements.txt
copy .env.example .env             # optional: put your OPENAI_API_KEY in .env
uvicorn app.main:app --reload --port 8000
```

Terminal 2, frontend:

```powershell
cd softutter\frontend
npm install
npm run dev
```

Open http://localhost:5173 in Chrome.

**No API key?** The backend runs in **demo mode**: sample café-order content in all six languages, your browser's own
voices for audio, and sample feedback. The whole flow is explorable offline.

Optional Azure scoring: `pip install -r requirements-azure.txt`, then set `AZURE_SPEECH_KEY` and `AZURE_SPEECH_REGION`.

Offline logic checks: `python tests/test_logic.py` (from `backend/`).

## How it works

1. **Compose** → `POST /api/scaffold` (text from typing, mixing, or `POST /api/transcribe`).
2. **Result** → help level 1 Nudge (hints), 2 Frame (fill the blanks), 3 Full recast. All three are generated in one call, so switching levels is instant.
3. **Shadow** → back-chaining over chunks (last chunk first), then the whole sentence. Each attempt goes to `POST /api/assess`: transcribe, diff against the target, optional Azure word scores, then short encouraging feedback. No scores are shown.
4. **Phrasebook** → `GET/POST/PATCH/DELETE /api/phrases`.
5. **Conversation** → `POST /api/converse` plays a short role-play (5 learner turns; café, meeting someone, friends, work). The partner speaks; you answer by voice or typing (any mix of languages). Each answer is *recast* into a natural sentence without scolding, the partner replies in character, and a hint ladder (Nudge, Frame, Full answer) is always one tap away. Finished conversations list your natural sentences, each with a Practice button into Shadow. Demo mode has one scripted café scene per language.
6. **My sounds** → Shadow logs, per sound, whether it was *seen*, *clear* or *to revisit* (`POST /api/sounds/events`; `GET /api/sounds`). Each sound is linked to the chunks it occurs in, so a chunk result is credited to the right sounds. Status comes from the last three outcomes: a recent "to revisit" → *Worth another go*; two or more tries with the last three clear → *Getting steady*. No scores. Compose shows the top few as "Sounds to watch".

Sound annotations use five tags rendered in the UI: `care`, `silent`, `link`, `tone` (and `none`).
Language data (focus areas, codes, placeholders) lives in `backend/app/languages.py`; adding a language is one entry there plus a demo entry in `mock_data.py`.

## Known limits

- IPA, tips and demo content are model/sample output: have a native speaker or linguist spot-check each language.
- Word-level feedback is only as good as speech recognition (plus Azure if enabled). Phoneme-level feedback is a later step.
- No accounts yet: one local user. Add auth before any public launch.

## Roadmap

Warm-up queue from the phrasebook, accounts.
