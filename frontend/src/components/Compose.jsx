import { useEffect, useState } from 'react'
import LanguagePicker from './LanguagePicker.jsx'
import Transcript from './Transcript.jsx'
import WaveBars from './WaveBars.jsx'
import { Icon, Pause, Play, Stop } from './Icon.jsx'
import { api } from '../lib/api.js'
import { usePlayer } from '../lib/hooks.js'
import { useRecorder } from '../lib/recorder.js'

const HELPS = [
  { id: 1, title: 'Nudge', desc: 'Hints only. I point at what to rethink, you rebuild it.' },
  { id: 2, title: 'Sentence frame', desc: 'A fill-in-the-blank skeleton you complete yourself.' },
  { id: 3, title: 'Full recast', desc: 'Hear the whole target sentence, then echo it.' },
]
const CONTEXTS = [
  ['cafe', 'At a café'],
  ['meeting', 'Meeting someone'],
  ['friends', 'With friends'],
  ['work', 'At work'],
]
const L1S = [
  ['en', 'English'],
  ['zh', '中文'],
  ['es', 'Español'],
  ['fr', 'Français'],
  ['de', 'Deutsch'],
  ['ja', '日本語'],
  ['ko', '한국어'],
]

export default function Compose({ langs, settings, setSettings, onScaffold, onOpenPhrase, onOpenSounds }) {
  const lang = langs.find((l) => l.code === settings.lang) || langs[0]
  const set = (patch) => setSettings((s) => ({ ...s, ...patch }))

  const [mode, setMode] = useState('speak')
  const [typed, setTyped] = useState('')
  const [mixed, setMixed] = useState('')
  const [transcript, setTranscript] = useState('')
  const [uncertain, setUncertain] = useState([])
  const [clip, setClip] = useState(null)
  const [transcribing, setTranscribing] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [recent, setRecent] = useState([])
  const [watch, setWatch] = useState([])

  const rec = useRecorder()
  const clipPlayer = usePlayer(() => Promise.resolve(clip))

  useEffect(() => {
    api.phrases().then((rows) => setRecent(rows.slice(0, 3))).catch(() => {})
  }, [])

  useEffect(() => {
    api
      .sounds(settings.lang)
      .then((rows) => setWatch(rows.filter((r) => r.status === 'working').slice(0, 4)))
      .catch(() => setWatch([]))
  }, [settings.lang])

  // A transcript is tied to the language it was recorded in.
  useEffect(() => {
    setTranscript('')
    setUncertain([])
    setClip(null)
  }, [settings.lang])

  const text = mode === 'speak' ? transcript : mode === 'type' ? typed : mixed

  async function toggleRecording() {
    setError('')
    if (rec.state === 'recording') {
      const result = await rec.stop()
      setClip(result)
      setTranscribing(true)
      try {
        const t = await api.transcribe(result.blob, settings.lang)
        setTranscript(t.text)
        setUncertain(t.uncertain || [])
      } catch (e) {
        setError(e.message)
      } finally {
        setTranscribing(false)
      }
    } else {
      clipPlayer.stop()
      try {
        await rec.start()
      } catch {
        setError('The microphone is not available. Check the browser permission, or use Type instead.')
      }
    }
  }

  async function go() {
    if (!text.trim()) {
      setError(mode === 'speak' ? 'Record something first, or switch to Type.' : 'Type something first.')
      return
    }
    setBusy(true)
    setError('')
    try {
      const s = await api.scaffold({
        language: settings.lang,
        text: text.trim(),
        l1: settings.l1,
        context: settings.ctx,
        formality: settings.register,
      })
      onScaffold(s)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const recording = rec.state === 'recording'
  const mmss = `00:${String(rec.seconds).padStart(2, '0')}`

  return (
    <>
      <header>
        <h1>What do you want to say?</h1>
        <p className="lede">
          Say it however you can: in {lang.name.replace(' (Mandarin)', '')}, in your own language, or both.
          SoftUtter helps you get to the {lang.name.replace(' (Mandarin)', '')}, one small step at a time.
        </p>
      </header>

      <div className="cols">
        <div className="stack" style={{ flex: '1 1 520px' }}>
          <section className="card">
            <div className="card-head">
              <h2>I'm learning</h2>
            </div>
            <LanguagePicker langs={langs} value={settings.lang} onChange={(code) => set({ lang: code })} />
            <label className="row small muted" htmlFor="l1">
              My own language:
              <select
                id="l1"
                className="select"
                value={settings.l1}
                onChange={(e) => set({ l1: e.target.value })}
              >
                {L1S.map(([code, label]) => (
                  <option key={code} value={code}>
                    {label}
                  </option>
                ))}
              </select>
              <span>Explanations and tips will be written in it.</span>
            </label>
          </section>

          <section className="card">
            <div className="card-head">
              <span className="step-badge">1</span>
              <h2>Say it your way</h2>
            </div>

            <div className="seg" role="group" aria-label="Input method">
              <button aria-pressed={mode === 'speak'} onClick={() => setMode('speak')}>
                <Icon name="mic" size={18} /> Speak
              </button>
              <button aria-pressed={mode === 'type'} onClick={() => setMode('type')}>
                <Icon name="keyboard" size={18} /> Type
              </button>
              <button aria-pressed={mode === 'mix'} onClick={() => setMode('mix')}>
                <Icon name="globe" size={18} /> Mix in my language
              </button>
            </div>

            {mode === 'speak' && (
              <div className="stack" style={{ gap: 14 }}>
                <div className="recorder">
                  <button
                    className="mic-big"
                    onClick={toggleRecording}
                    aria-label={recording ? 'Stop recording' : 'Start recording'}
                    disabled={transcribing}
                  >
                    {recording ? <Stop /> : <Icon name="mic" size={22} />}
                  </button>
                  {recording ? (
                    <WaveBars peaks={rec.levels.length ? rec.levels : [0.1]} live />
                  ) : clip ? (
                    <>
                      <button
                        className="round blue"
                        onClick={clipPlayer.toggle}
                        aria-label={clipPlayer.playing ? 'Pause your recording' : 'Play your recording'}
                      >
                        {clipPlayer.playing ? <Pause /> : <Play />}
                      </button>
                      <WaveBars peaks={clip.peaks} played={clipPlayer.progress} />
                    </>
                  ) : (
                    <div className="muted small" style={{ flex: 1 }}>
                      Tap the mic and say it. No rush: you can re-record any time.
                    </div>
                  )}
                  <div className="timer">{recording ? mmss : clip ? `${clip.duration.toFixed(1)}s` : ''}</div>
                </div>

                {transcribing && <div className="muted small">Listening back…</div>}
                {!transcribing && transcript && (
                  <Transcript
                    text={transcript}
                    uncertain={uncertain}
                    locale={lang.locale}
                    onChange={setTranscript}
                  />
                )}
              </div>
            )}

            {mode === 'type' && (
              <div className="stack" style={{ gap: 10 }}>
                <label className="field-label" htmlFor="typed">
                  Type your sentence in {lang.name.replace(' (Mandarin)', '')}
                </label>
                <textarea
                  id="typed"
                  className="text-in"
                  rows={3}
                  lang={lang.locale}
                  value={typed}
                  placeholder={lang.placeholder_type}
                  onChange={(e) => setTyped(e.target.value)}
                />
                <div className="muted small">Accents and punctuation are optional.</div>
              </div>
            )}

            {mode === 'mix' && (
              <div className="stack" style={{ gap: 10 }}>
                <label className="field-label" htmlFor="mixed">
                  Stuck on a word? Use your own language for the gap.
                </label>
                <textarea
                  id="mixed"
                  className="text-in"
                  rows={3}
                  lang={lang.locale}
                  value={mixed}
                  placeholder={lang.placeholder_mix}
                  onChange={(e) => setMixed(e.target.value)}
                />
                <div className="callout" style={{ background: 'var(--teal-tint)', color: 'var(--teal-ink)' }}>
                  <Icon name="globe" size={16} />
                  <span>Write what you can, then “…” or your own words where you are stuck. I'll fill the gap.</span>
                </div>
              </div>
            )}
          </section>

          <section className="card">
            <div className="card-head">
              <span className="step-badge">2</span>
              <h2>How much help do you want?</h2>
            </div>
            <div className="ladder">
              {HELPS.map((h) => (
                <button key={h.id} aria-pressed={settings.level === h.id} onClick={() => set({ level: h.id })}>
                  <span className="lv">Level {h.id}</span>
                  <span className="tt">{h.title}</span>
                  <span className="ds">{h.desc}</span>
                </button>
              ))}
            </div>
          </section>

          <section className="card">
            <div className="card-head">
              <span className="step-badge">3</span>
              <h2>Where are you saying it?</h2>
            </div>
            <div className="chips">
              {CONTEXTS.map(([id, label]) => (
                <button key={id} className="chip" aria-pressed={settings.ctx === id} onClick={() => set({ ctx: id })}>
                  {label}
                </button>
              ))}
            </div>
            <div className="seg sm" role="group" aria-label="Register" style={{ alignSelf: 'flex-start' }}>
              <button aria-pressed={settings.register === 'polite'} onClick={() => set({ register: 'polite' })}>
                Polite
              </button>
              <button aria-pressed={settings.register === 'casual'} onClick={() => set({ register: 'casual' })}>
                Casual
              </button>
            </div>

            {error && <div className="error-banner" role="alert">{error}</div>}

            <div className="row" style={{ paddingTop: 6 }}>
              <button className="btn btn-primary" style={{ height: 54, padding: '0 30px', fontSize: 17 }} onClick={go} disabled={busy || transcribing || recording}>
                {busy ? 'Scaffolding…' : 'Scaffold my sentence'}
                {!busy && <Icon name="arrow" stroke={2.5} />}
              </button>
              <span className="muted small">Takes a few seconds. Nothing is graded.</span>
            </div>
          </section>
        </div>

        <aside className="stack" style={{ flex: '1 1 280px', maxWidth: 360 }}>
          <section className="card" style={{ padding: 20, gap: 12 }}>
            <h2 style={{ fontSize: 16 }}>{recent.length ? 'Pick up where you left off' : 'How it works'}</h2>
            {recent.length > 0 ? (
              recent.map((p) => (
                <button
                  key={p.id}
                  className="phrase"
                  style={{ background: 'var(--bg)', border: 0, textAlign: 'left' }}
                  onClick={() => onOpenPhrase(p)}
                >
                  <span className="body">
                    <span className="tg" style={{ fontSize: 15 }} lang={p.language}>{p.target}</span>
                    <span className="small muted" style={{ display: 'block' }}>{p.meaning}</span>
                  </span>
                  <span className={`status ${p.status}`}>{p.status === 'own' ? 'Own it' : p.status === 'echo' ? 'Echo' : 'New'}</span>
                </button>
              ))
            ) : (
              <ol className="small muted" style={{ margin: 0, paddingLeft: 18, lineHeight: 1.7 }}>
                <li>Say or type it however you can.</li>
                <li>Get a natural version and hear it.</li>
                <li>Echo it back in small chunks.</li>
                <li>Save the phrases you want to keep.</li>
              </ol>
            )}
          </section>

          {watch.length > 0 && (
            <section className="card" style={{ padding: 20, gap: 12 }}>
              <h2 style={{ fontSize: 16 }}>Sounds to watch</h2>
              <p className="small muted" style={{ margin: 0, lineHeight: 1.45 }}>
                Patterns from your recent practice.
              </p>
              <div className="chips" style={{ gap: 8 }}>
                {watch.map((w) => (
                  <span key={w.key} className={`pill ${w.tag}`}>
                    {w.symbol && <span className="ipa">{w.symbol}</span>} {w.title}
                  </span>
                ))}
              </div>
              <button className="back-link" onClick={onOpenSounds} style={{ alignSelf: 'flex-start' }}>
                See all my sounds
              </button>
            </section>
          )}
        </aside>
      </div>
    </>
  )
}
