import { useEffect, useRef, useState } from 'react'
import LanguagePicker from './LanguagePicker.jsx'
import WaveBars from './WaveBars.jsx'
import { Icon, Pause, Play, Stop } from './Icon.jsx'
import { api } from '../lib/api.js'
import { useLazyAudio } from '../lib/hooks.js'
import { useRecorder } from '../lib/recorder.js'

export const MAX_TURNS = 5

const CONTEXTS = [
  ['cafe', 'At a café'],
  ['meeting', 'Meeting someone'],
  ['friends', 'With friends'],
  ['work', 'At work'],
]
const HELP_TITLES = { 1: 'Nudge', 2: 'Sentence frame', 3: 'Full answer' }
const L1S = [
  ['en', 'English'],
  ['zh', '中文'],
  ['es', 'Español'],
  ['fr', 'Français'],
  ['de', 'Deutsch'],
  ['ja', '日本語'],
  ['ko', '한국어'],
]

let seq = 0
const nextId = () => `m${Date.now()}-${seq++}`

function Speaker({ text, lang, slow, label, autoPlay }) {
  const p = useLazyAudio(text, lang, slow ? 0.6 : 1)
  const fired = useRef(false)
  useEffect(() => {
    if (!autoPlay) return undefined
    // Delay a beat so React StrictMode's mount/unmount cycle cannot cancel it.
    const t = setTimeout(() => {
      if (fired.current) return
      fired.current = true
      p.toggle()
    }, 150)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  return (
    <button className="round blue" onClick={p.toggle} aria-label={`${p.playing ? 'Stop' : 'Play'} ${label}`}>
      {p.playing ? <Pause /> : <Play />}
    </button>
  )
}

function PartnerBubble({ m, role, lang, slow, showMeaning, autoPlay }) {
  return (
    <div className="conv-row partner">
      <div className="conv-who">{role}</div>
      <div className="conv-bubble partner">
        <div className="conv-line">
          <Speaker text={m.text} lang={lang.code} slow={slow} label={`${role}'s line`} autoPlay={autoPlay} />
          <div className="conv-body">
            <div className="conv-text" lang={lang.locale}>{m.text}</div>
            {m.reading && <div className="reading small">{m.reading}</div>}
            {showMeaning && m.meaning && <div className="conv-meaning">“{m.meaning}”</div>}
          </div>
        </div>
      </div>
      {m.listen && (
        <div className="callout conv-listen">
          <Icon name="info" size={18} />
          <span>
            Listen for{' '}
            <b>
              {m.listen.symbol && <span className="ipa">{m.listen.symbol} </span>}
              {m.listen.title}
            </b>
            . {m.listen.tip}
          </span>
        </div>
      )}
    </div>
  )
}

function YouBubble({ m, lang, slow, practicing, onPractice }) {
  const rc = m.recast
  return (
    <div className="conv-row you">
      <div className="conv-who">You · {m.via === 'spoken' ? 'spoken' : 'typed'}</div>
      <div className="conv-bubble you" lang={lang.locale}>{m.text}</div>
      {rc && rc.changed && (
        <div className="conv-recast">
          <div className="eyebrow">A natural way to say it</div>
          <div className="conv-line">
            <Speaker text={rc.text} lang={lang.code} slow={slow} label="the natural version" />
            <div className="conv-body">
              <div className="conv-text sm" lang={lang.locale}>{rc.text}</div>
              {rc.reading && <div className="reading small">{rc.reading}</div>}
            </div>
          </div>
          {rc.note && <div className="small muted">{rc.note}</div>}
          <button className="btn btn-ghost btn-sm" onClick={() => onPractice(m)} disabled={!!practicing}>
            {practicing === rc.text ? 'Getting it ready…' : 'Practice this sentence'}
          </button>
        </div>
      )}
      {rc && !rc.changed && (
        <div className="conv-ok">
          <Icon name="check" size={16} stroke={2.5} /> That worked just as you said it.
        </div>
      )}
    </div>
  )
}

function localScaffold(m, session, l1) {
  const rc = m.recast
  return {
    language: session.language,
    source_text: m.text,
    l1,
    context: session.ctx,
    formality: session.formality,
    target: rc.text,
    meaning: m.answerMeaning || '',
    reading: rc.reading || '',
    ipa: '',
    feedback: '',
    gap_filled: [],
    chunks: [{ text: rc.text, ipa: '', reading: rc.reading || '', tip: '', segments: [{ text: rc.text, tag: 'none' }] }],
    sounds: [],
    hints: [],
    frame: null,
    variants: [],
    mock: true,
  }
}

export default function Conversation({ langs, settings, setSettings, mock, session, setSession, onPractice }) {
  const set = (patch) => setSettings((s) => ({ ...s, ...patch }))
  const lang = langs.find((l) => l.code === (session ? session.language : settings.lang)) || langs[0]
  const short = (l) => l.name.replace(' (Mandarin)', '')

  const [draft, setDraft] = useState('')
  const [via, setVia] = useState('typed')
  const [busy, setBusy] = useState(false)
  const [transcribing, setTranscribing] = useState(false)
  const [error, setError] = useState('')
  const [hintOpen, setHintOpen] = useState(false)
  const [boost, setBoost] = useState(0)
  const [slow, setSlow] = useState(false)
  const [showMeaning, setShowMeaning] = useState(true)
  const [practicing, setPracticing] = useState('')
  const rec = useRecorder()
  const endRef = useRef(null)

  const msgCount = session ? session.msgs.length : 0
  useEffect(() => {
    endRef.current?.scrollIntoView?.({ block: 'nearest', behavior: 'smooth' })
  }, [msgCount, busy])

  const base = () => ({
    language: session ? session.language : settings.lang,
    l1: settings.l1,
    context: session ? session.ctx : settings.ctx,
    formality: session ? session.formality : settings.register,
    max_turns: MAX_TURNS,
  })

  const partnerMsg = (r) => ({ id: nextId(), role: 'partner', text: r.reply.text, reading: r.reply.reading, meaning: r.reply.meaning, listen: r.listen })

  function logListen(listen, code) {
    if (!listen) return
    api
      .logSounds(code, [{ title: listen.title, symbol: listen.symbol, tag: listen.tag, tip: listen.tip, outcome: 'seen' }])
      .catch(() => {})
  }

  async function start() {
    setBusy(true)
    setError('')
    try {
      const b = base()
      const r = await api.converse({ ...b, history: [], user_text: '', turn: 0 })
      setSession({
        language: b.language,
        ctx: b.context,
        formality: b.formality,
        role: r.role,
        mock: r.mock,
        turn: 0,
        msgs: [partnerMsg(r)],
        next: r.next,
        done: false,
      })
      setDraft('')
      setHintOpen(false)
      setBoost(0)
      logListen(r.listen, b.language)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  async function send() {
    const text = draft.trim()
    if (!text || busy || transcribing || rec.state === 'recording' || session.done) return
    setError('')
    const turn = session.turn + 1
    const history = session.msgs.map((m) => ({ role: m.role, text: m.text }))
    const you = { id: nextId(), role: 'you', text, via, answerMeaning: session.next?.meaning || '' }
    setSession((s) => ({ ...s, msgs: [...s.msgs, you] }))
    setDraft('')
    setHintOpen(false)
    setBoost(0)
    setBusy(true)
    try {
      const r = await api.converse({ ...base(), history, user_text: text, turn })
      setSession((s) => {
        const msgs = s.msgs.slice()
        msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], recast: r.recast }
        msgs.push(partnerMsg(r))
        return { ...s, msgs, turn, next: r.next, done: r.done }
      })
      logListen(r.listen, session.language)
    } catch (e) {
      setError(e.message)
      setSession((s) => ({ ...s, msgs: s.msgs.slice(0, -1) }))
      setDraft(text)
    } finally {
      setBusy(false)
    }
  }

  async function toggleRecording() {
    setError('')
    if (rec.state === 'recording') {
      const clip = await rec.stop()
      setTranscribing(true)
      try {
        const t = await api.transcribe(clip.blob, session.language)
        setDraft(t.text)
        setVia('spoken')
      } catch (e) {
        setError(e.message)
      } finally {
        setTranscribing(false)
      }
    } else {
      try {
        await rec.start()
      } catch {
        setError('The microphone is not available. Check the browser permission, or type your answer instead.')
      }
    }
  }

  async function practice(m) {
    setPracticing(m.recast.text)
    setError('')
    try {
      const s = session.mock
        ? localScaffold(m, session, settings.l1)
        : await api.scaffold({
            language: session.language,
            text: m.recast.text,
            l1: settings.l1,
            context: session.ctx,
            formality: session.formality,
          })
      onPractice(s)
    } catch (e) {
      setError(e.message)
    } finally {
      setPracticing('')
    }
  }

  /* ---------- start screen ---------- */
  if (!session) {
    return (
      <div className="conv">
        <header>
          <h1>Have a short conversation</h1>
          <p className="lede">
            A friendly partner speaks, you answer in {short(lang)}. {MAX_TURNS} short turns, no grades. Ask for a
            hint whenever you need one.
          </p>
        </header>

        <section className="card">
          <div className="card-head">
            <h2>I'm learning</h2>
          </div>
          <LanguagePicker langs={langs} value={settings.lang} onChange={(code) => set({ lang: code })} />
          <label className="row small muted" htmlFor="conv-l1">
            My own language:
            <select id="conv-l1" className="select" value={settings.l1} onChange={(e) => set({ l1: e.target.value })}>
              {L1S.map(([code, label]) => (
                <option key={code} value={code}>
                  {label}
                </option>
              ))}
            </select>
            <span>Meanings and hints are written in it.</span>
          </label>
        </section>

        <section className="card">
          <div className="card-head">
            <h2>Where are you?</h2>
          </div>
          <div className="chips">
            {CONTEXTS.map(([id, label]) => (
              <button key={id} className="chip" aria-pressed={settings.ctx === id} onClick={() => set({ ctx: id })}>
                {label}
              </button>
            ))}
          </div>
          {mock && <div className="small muted">Demo mode has one scene: ordering at a café.</div>}
          <div className="row">
            <div className="seg sm" role="group" aria-label="Register">
              <button aria-pressed={settings.register === 'polite'} onClick={() => set({ register: 'polite' })}>
                Polite
              </button>
              <button aria-pressed={settings.register === 'casual'} onClick={() => set({ register: 'casual' })}>
                Casual
              </button>
            </div>
            <div className="seg sm" role="group" aria-label="Help level">
              {[1, 2, 3].map((n) => (
                <button key={n} aria-pressed={settings.level === n} onClick={() => set({ level: n })}>
                  {HELP_TITLES[n]}
                </button>
              ))}
            </div>
          </div>
          {error && <div className="error-banner" role="alert">{error}</div>}
          <div className="row" style={{ paddingTop: 6 }}>
            <button className="btn btn-primary" style={{ height: 54, padding: '0 30px', fontSize: 17 }} onClick={start} disabled={busy}>
              {busy ? 'Starting…' : 'Start the conversation'}
              {!busy && <Icon name="arrow" stroke={2.5} />}
            </button>
            <span className="muted small">You can stop any time. Nothing is graded.</span>
          </div>
        </section>
      </div>
    )
  }

  /* ---------- conversation ---------- */
  const ctxLabel = (CONTEXTS.find(([id]) => id === session.ctx) || [])[1] || ''
  const level = Math.min(3, Math.max(1, settings.level) + boost)
  const next = session.next
  const recording = rec.state === 'recording'
  const lastPartner = [...session.msgs].reverse().find((m) => m.role === 'partner')
  const naturals = session.msgs.filter((m) => m.role === 'you' && m.recast)
  const hintItems = next ? (next.hints.length ? next.hints : [next.frame || next.answer]) : []

  return (
    <div className="conv">
      <header className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div className="stack" style={{ gap: 8 }}>
          <h1 style={{ fontSize: 30 }}>Conversation</h1>
          <div className="row" style={{ gap: 8 }}>
            <span className="pill tone">{short(lang)}</span>
            <span className="pill silent">{ctxLabel}</span>
            <span className="pill silent">{session.formality === 'casual' ? 'Casual' : 'Polite'}</span>
            <span className="pill link" aria-live="polite">
              {session.done ? 'Finished' : `Turn ${Math.min(session.turn + 1, MAX_TURNS)} of ${MAX_TURNS}`}
            </span>
          </div>
        </div>
        <div className="row" style={{ gap: 8 }}>
          <button className="toggle" aria-pressed={showMeaning} onClick={() => setShowMeaning((v) => !v)}>
            Meanings
          </button>
          <button className="toggle" aria-pressed={slow} onClick={() => setSlow((v) => !v)}>
            Slow 0.6×
          </button>
          <button className="btn btn-ghost btn-sm" onClick={() => setSession(null)}>
            Start over
          </button>
        </div>
      </header>

      <section className="conv-log" aria-label="Conversation" aria-live="polite">
        {session.msgs.map((m) =>
          m.role === 'partner' ? (
            <PartnerBubble
              key={m.id}
              m={m}
              role={session.role}
              lang={lang}
              slow={slow}
              showMeaning={showMeaning}
              autoPlay={m === lastPartner}
            />
          ) : (
            <YouBubble key={m.id} m={m} lang={lang} slow={slow} practicing={practicing} onPractice={practice} />
          ),
        )}
        {busy && (
          <div className="conv-row partner" aria-label={`${session.role} is replying`}>
            <div className="conv-bubble partner conv-typing" aria-hidden="true">
              <span /><span /><span />
            </div>
          </div>
        )}
        <div ref={endRef} />
      </section>

      {error && <div className="error-banner" role="alert">{error}</div>}

      {session.done ? (
        <section className="card celebrate">
          <div className="eyebrow">Conversation finished</div>
          <h1>Nicely done.</h1>
          {naturals.length > 0 && <p className="muted">Your sentences, the natural way. Pick any to practice out loud.</p>}
          <div className="stack" style={{ gap: 10, alignSelf: 'stretch', textAlign: 'left' }}>
            {naturals.map((m) => (
              <div className="conv-final" key={m.id}>
                <Speaker text={m.recast.text} lang={lang.code} slow={slow} label="this sentence" />
                <div className="conv-body">
                  <div className="conv-text sm" lang={lang.locale}>{m.recast.text}</div>
                  {m.recast.reading && <div className="reading small">{m.recast.reading}</div>}
                  {m.answerMeaning && showMeaning && <div className="conv-meaning">“{m.answerMeaning}”</div>}
                </div>
                <button className="btn btn-ghost btn-sm" onClick={() => practice(m)} disabled={!!practicing}>
                  {practicing === m.recast.text ? 'Getting it ready…' : 'Practice'}
                </button>
              </div>
            ))}
          </div>
          <div className="row" style={{ justifyContent: 'center' }}>
            <button className="btn btn-primary" onClick={() => setSession(null)}>
              Start another <Icon name="arrow" size={18} stroke={2.5} />
            </button>
          </div>
        </section>
      ) : (
        <section className="card conv-turn">
          <div className="row" style={{ justifyContent: 'space-between' }}>
            <div className="eyebrow">Your turn</div>
            {next && (
              <button className="toggle" aria-pressed={hintOpen} onClick={() => setHintOpen((v) => !v)}>
                {hintOpen ? 'Hide hint' : 'Need a hint'}
              </button>
            )}
          </div>

          {hintOpen && next && (
            <div className="conv-hint" aria-live="polite">
              {level === 1 && (
                <ul className="hint-list">
                  {hintItems.map((h, i) => (
                    <li key={i}>
                      <span className="n">{i + 1}</span>
                      <span>{h}</span>
                    </li>
                  ))}
                </ul>
              )}
              {level === 2 && (
                <>
                  <div className="frame-text sm" lang={lang.locale}>{next.frame || next.answer}</div>
                  {hintItems[0] && <div className="small muted">{hintItems[0]}</div>}
                </>
              )}
              {level === 3 && (
                <div className="conv-line">
                  <Speaker text={next.answer} lang={lang.code} slow={slow} label="the full answer" />
                  <div className="conv-body">
                    <div className="conv-text sm" lang={lang.locale}>{next.answer}</div>
                    {next.reading && <div className="reading small">{next.reading}</div>}
                    {showMeaning && next.meaning && <div className="conv-meaning">“{next.meaning}”</div>}
                  </div>
                </div>
              )}
              <div className="row small muted" style={{ justifyContent: 'space-between' }}>
                <span>Help level {level} · {HELP_TITLES[level]}</span>
                {level < 3 && (
                  <button className="btn btn-ghost btn-sm" onClick={() => setBoost((b) => b + 1)}>
                    A bit more help
                  </button>
                )}
              </div>
            </div>
          )}

          <div className="conv-input">
            <button
              className="mic-big"
              onClick={toggleRecording}
              aria-label={recording ? 'Stop recording' : 'Start recording'}
              disabled={busy || transcribing}
            >
              {recording ? <Stop /> : <Icon name="mic" size={22} />}
            </button>
            {recording ? (
              <div className="conv-live">
                <WaveBars peaks={rec.levels.length ? rec.levels : [0.1]} live />
                <span className="timer">{`00:${String(rec.seconds).padStart(2, '0')}`}</span>
              </div>
            ) : (
              <textarea
                id="conv-reply"
                className="text-in"
                rows={2}
                lang={lang.locale}
                aria-label={`Your answer in ${short(lang)}`}
                value={draft}
                disabled={transcribing}
                placeholder={
                  transcribing ? 'Listening back…' : `Tap the mic, or type in ${short(lang)}`
                }
                onChange={(e) => {
                  setDraft(e.target.value)
                  setVia('typed')
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    send()
                  }
                }}
              />
            )}
            <button className="btn btn-primary" onClick={send} disabled={!draft.trim() || busy || transcribing || recording}>
              Send <Icon name="arrow" size={18} stroke={2.5} />
            </button>
          </div>
          <div className="muted small">Take your time. Whatever you say, you'll hear the natural version back.</div>
        </section>
      )}
    </div>
  )
}
