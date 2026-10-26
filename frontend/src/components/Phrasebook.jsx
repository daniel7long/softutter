import { useEffect, useState } from 'react'
import { Icon, Pause, Play } from './Icon.jsx'
import { api } from '../lib/api.js'
import { useLazyAudio } from '../lib/hooks.js'

const STATUS_LABEL = { new: 'New', echo: 'Echo', own: 'Own it' }

function PhraseCard({ p, onOpen, onDelete }) {
  const audio = useLazyAudio(p.target, p.language)
  return (
    <div className="phrase">
      <button
        className="round blue"
        onClick={audio.toggle}
        aria-label={`${audio.playing ? 'Stop' : 'Play'} phrase`}
      >
        {audio.playing ? <Pause /> : <Play />}
      </button>
      <div className="body">
        <div className="tg" lang={p.language}>{p.target}</div>
        {p.reading && <div className="small reading" style={{ fontSize: 14 }}>{p.reading}</div>}
        <div className="small muted">{p.meaning}</div>
      </div>
      <span className={`status ${p.status}`}>{STATUS_LABEL[p.status] || p.status}</span>
      <button className="btn btn-ghost btn-sm" onClick={() => onOpen(p)}>
        Practice
      </button>
      <button className="icon-btn" aria-label="Delete phrase" onClick={() => onDelete(p)}>
        <Icon name="trash" size={18} />
      </button>
    </div>
  )
}

export default function Phrasebook({ langs, onOpen }) {
  const [phrases, setPhrases] = useState(null)
  const [filter, setFilter] = useState('all')
  const [error, setError] = useState('')

  useEffect(() => {
    api.phrases().then(setPhrases).catch((e) => setError(e.message))
  }, [])

  async function remove(p) {
    try {
      await api.deletePhrase(p.id)
      setPhrases((rows) => rows.filter((r) => r.id !== p.id))
    } catch (e) {
      setError(e.message)
    }
  }

  const shown = (phrases || []).filter((p) => filter === 'all' || p.language === filter)
  const present = langs.filter((l) => (phrases || []).some((p) => p.language === l.code))
  const nextUp = shown.find((p) => p.status !== 'own')

  return (
    <>
      <header>
        <h1>Phrasebook</h1>
        <p className="lede">Phrases you saved. Come back to echo them a few days later.</p>
      </header>

      {error && <div className="error-banner">{error}</div>}

      {nextUp && (
        <div className="promo">
          <div className="eyebrow" style={{ color: '#fff', opacity: 0.95 }}>Up next</div>
          <div className="t" lang={nextUp.language}>{nextUp.target}</div>
          <div style={{ opacity: 0.95 }}>{nextUp.meaning}</div>
          <button className="btn" onClick={() => onOpen(nextUp)}>Practice this phrase</button>
        </div>
      )}

      {present.length > 1 && (
        <div className="chips" role="group" aria-label="Filter by language">
          <button className="chip" aria-pressed={filter === 'all'} onClick={() => setFilter('all')}>All</button>
          {present.map((l) => (
            <button key={l.code} className="chip" aria-pressed={filter === l.code} onClick={() => setFilter(l.code)}>
              {l.native}
            </button>
          ))}
        </div>
      )}

      <div className="stack" style={{ gap: 12 }}>
        {phrases === null && !error && <div className="muted">Loading…</div>}
        {phrases && shown.length === 0 && (
          <div className="empty">
            Nothing saved yet. Scaffold a sentence, then tap “Save to phrasebook”.
          </div>
        )}
        {shown.map((p) => (
          <PhraseCard key={p.id} p={p} onOpen={onOpen} onDelete={remove} />
        ))}
      </div>
    </>
  )
}
