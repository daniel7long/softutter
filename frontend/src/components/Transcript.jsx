import { useMemo, useState } from 'react'

const PUNCT = /[\s.,!?;:。！？、，'’"“”()]/g
const norm = (s) => s.toLowerCase().replace(PUNCT, '')

function tokenize(text, locale) {
  try {
    const seg = new Intl.Segmenter(locale, { granularity: 'word' })
    return [...seg.segment(text)].map((s) => ({ t: s.segment, word: !!s.isWordLike }))
  } catch {
    return text.split(/(\s+)/).filter(Boolean).map((t) => ({ t, word: !/^\s+$/.test(t) }))
  }
}

// Shows what speech recognition heard. Tap any word to correct it; uncertain words are flagged.
export default function Transcript({ text, uncertain = [], locale, onChange }) {
  const tokens = useMemo(() => tokenize(text, locale), [text, locale])
  const unsure = useMemo(() => new Set(uncertain.map(norm)), [uncertain])
  const [editing, setEditing] = useState(-1)
  const [draft, setDraft] = useState('')

  const flagged = tokens.filter((tk) => tk.word && unsure.has(norm(tk.t)))

  function commit() {
    if (editing < 0) return
    const next = tokens.map((tk, i) => (i === editing ? draft : tk.t)).join('')
    setEditing(-1)
    if (next !== text) onChange(next)
  }

  return (
    <div className="transcript">
      <div className="label">What I heard · tap a word to fix it</div>
      <div className="words" lang={locale}>
        {tokens.map((tk, i) => {
          if (!tk.word) return <span key={i}>{tk.t}</span>
          if (editing === i) {
            return (
              <input
                key={i}
                className="tok-edit"
                autoFocus
                value={draft}
                aria-label={`Correct “${tk.t}”`}
                style={{ width: `${Math.max(4, draft.length + 2)}ch` }}
                onChange={(e) => setDraft(e.target.value)}
                onBlur={commit}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') commit()
                  if (e.key === 'Escape') setEditing(-1)
                }}
              />
            )
          }
          return (
            <button
              key={i}
              className={`tok ${unsure.has(norm(tk.t)) ? 'unsure' : ''}`}
              onClick={() => {
                setEditing(i)
                setDraft(tk.t)
              }}
            >
              {tk.t}
            </button>
          )
        })}
      </div>
      {flagged.length > 0 && (
        <div className="unsure-note">
          Not sure about {flagged.map((f) => `“${f.t}”`).join(', ')}. Is that what you said?
        </div>
      )}
    </div>
  )
}
