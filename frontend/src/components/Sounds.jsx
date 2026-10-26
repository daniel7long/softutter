import { useEffect, useState } from 'react'
import { api } from '../lib/api.js'

const STATUS = {
  working: { label: 'Worth another go', cls: 'echo' },
  new: { label: 'Just getting started', cls: 'new' },
  steady: { label: 'Getting steady', cls: 'own' },
}
const SECTIONS = [
  ['working', 'Worth another go', 'These needed a little more practice in your last tries.'],
  ['new', 'Just getting started', 'Not enough tries yet to say much. Keep going.'],
  ['steady', 'Getting steady', 'Your recent tries came through clearly.'],
]
const DOT_LABEL = { clear: 'came through clearly', care: 'needed another go' }
const keyOf = (title) => title.toLowerCase().split(/\s+/).filter(Boolean).join(' ')

function SoundCard({ s, phrase, onPractice }) {
  const st = STATUS[s.status]
  return (
    <div className="sound-card">
      <span className={`sym ${s.tag}`}>{s.symbol || '•'}</span>
      <div className="body">
        <div className="row" style={{ gap: 8 }}>
          <b>{s.title}</b>
          <span className={`status ${st.cls}`}>{st.label}</span>
        </div>
        <div className="small" style={{ color: 'var(--soft)', lineHeight: 1.45 }}>{s.tip}</div>
        <div className="row" style={{ gap: 10 }}>
          {s.history.length > 0 ? (
            <span className="dots" role="list" aria-label="Recent tries, oldest first">
              {s.history.map((o, i) => (
                <span
                  key={i}
                  role="listitem"
                  className={`dot-i ${o}`}
                  aria-label={`Try ${i + 1}: ${DOT_LABEL[o]}`}
                  title={DOT_LABEL[o]}
                />
              ))}
            </span>
          ) : (
            <span className="small muted">Not tried yet. Seen {s.seen} {s.seen === 1 ? 'time' : 'times'}.</span>
          )}
          {s.attempts > 0 && (
            <span className="small muted">
              {s.clear} clear · {s.care} to revisit
            </span>
          )}
        </div>
      </div>
      {phrase && (
        <button className="btn btn-ghost btn-sm" onClick={() => onPractice(phrase)}>
          Practice
        </button>
      )}
    </div>
  )
}

export default function Sounds({ langs, settings, onOpen }) {
  const [sounds, setSounds] = useState(null)
  const [phrases, setPhrases] = useState([])
  const [filter, setFilter] = useState(settings.lang)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([api.sounds(), api.phrases()])
      .then(([s, p]) => {
        setSounds(s)
        setPhrases(p)
      })
      .catch((e) => setError(e.message))
  }, [])

  const present = langs.filter((l) => (sounds || []).some((s) => s.language === l.code))
  const active = filter === 'all' || present.some((l) => l.code === filter) ? filter : 'all'
  const shown = (sounds || []).filter((s) => active === 'all' || s.language === active)

  const phraseFor = (s) =>
    phrases.find(
      (p) =>
        p.language === s.language &&
        p.payload &&
        (p.payload.sounds || []).some((x) => keyOf(x.title) === s.key),
    )
  const langName = (code) => (langs.find((l) => l.code === code)?.native) || code

  return (
    <>
      <header>
        <h1>My sounds</h1>
        <p className="lede">
          The sounds that keep coming up in your practice, and how they're going. No scores: just what to
          revisit and what's getting steady.
        </p>
      </header>

      {error && <div className="error-banner">{error}</div>}

      {present.length > 1 && (
        <div className="chips" role="group" aria-label="Filter by language">
          <button className="chip" aria-pressed={active === 'all'} onClick={() => setFilter('all')}>All</button>
          {present.map((l) => (
            <button key={l.code} className="chip" aria-pressed={active === l.code} onClick={() => setFilter(l.code)}>
              {l.native}
            </button>
          ))}
        </div>
      )}

      {sounds === null && !error && <div className="muted">Loading…</div>}

      {sounds && shown.length === 0 && (
        <div className="card empty">
          Nothing here yet. Practice a phrase with “Try it yourself” and the sounds in it will show up here,
          with how each one is going.
        </div>
      )}

      {SECTIONS.map(([status, title, blurb]) => {
        const rows = shown.filter((s) => s.status === status)
        if (!rows.length) return null
        return (
          <section className="stack" style={{ gap: 12 }} key={status} aria-label={title}>
            <div>
              <h2>{title}</h2>
              <p className="muted small" style={{ margin: '4px 0 0' }}>{blurb}</p>
            </div>
            {rows.map((s) => (
              <div key={`${s.language}:${s.key}`}>
                {active === 'all' && <div className="eyebrow" style={{ margin: '0 0 6px 4px' }} lang={s.language}>{langName(s.language)}</div>}
                <SoundCard s={s} phrase={phraseFor(s)} onPractice={onOpen} />
              </div>
            ))}
          </section>
        )
      })}
    </>
  )
}
