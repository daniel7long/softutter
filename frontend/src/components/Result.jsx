import { useState } from 'react'
import AnnotatedText, { Legend, sentenceSegments, tagsIn } from './AnnotatedText.jsx'
import WaveBars from './WaveBars.jsx'
import { Icon, Pause, Play } from './Icon.jsx'
import { api } from '../lib/api.js'
import { useLazyAudio, useTargetAudio } from '../lib/hooks.js'

const LEVELS = [
  { id: 1, label: 'Nudge' },
  { id: 2, label: 'Frame' },
  { id: 3, label: 'Full recast' },
]

function ChunkRow({ chunk, index, total, lang, showIpa, showReading }) {
  const audio = useLazyAudio(chunk.text, lang.code)
  return (
    <div className="chunk-row">
      <button
        className="round blue"
        onClick={audio.toggle}
        aria-label={`${audio.playing ? 'Stop' : 'Play'} chunk ${index + 1}`}
      >
        {audio.playing ? <Pause /> : <Play />}
      </button>
      <div className="body">
        <AnnotatedText className="target-text sm" segments={chunk.segments} />
        {(showIpa && chunk.ipa) || (showReading && chunk.reading) ? (
          <div className="small">
            {showReading && chunk.reading && <span className="reading" style={{ fontSize: 14 }}>{chunk.reading} </span>}
            {showIpa && chunk.ipa && <span className="ipa">{chunk.ipa}</span>}
          </div>
        ) : null}
        {chunk.tip && <div className="small muted">{chunk.tip}</div>}
      </div>
      <span className="idx">{index + 1} of {total}</span>
    </div>
  )
}

export default function Result({ scaffold, lang, settings, onBack, onPractice }) {
  const [level, setLevel] = useState(settings.level || 2)
  const [showIpa, setShowIpa] = useState(true)
  const [showReading, setShowReading] = useState(true)
  const [speed, setSpeed] = useState(1)
  const [saved, setSaved] = useState(false)
  const [saveError, setSaveError] = useState('')

  const full = level === 3
  const audio = useTargetAudio(full ? scaffold.target : null, lang.code, speed)
  const segments = sentenceSegments(scaffold.chunks, lang.join)
  const tags = tagsIn(segments)
  const readingLabel = lang.reading_label

  async function save() {
    setSaveError('')
    try {
      await api.addPhrase({
        language: scaffold.language,
        target: scaffold.target,
        meaning: scaffold.meaning,
        reading: scaffold.reading,
        ipa: scaffold.ipa,
        payload: scaffold,
      })
      setSaved(true)
    } catch (e) {
      setSaveError(e.message)
    }
  }

  const next = level === 1 ? 'Show me a frame' : 'Reveal full sentence'

  return (
    <>
      <header className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div className="stack" style={{ gap: 6 }}>
          <button className="back-link" onClick={onBack}>
            <Icon name="back" size={16} stroke={2.5} /> New sentence
          </button>
          <h1 style={{ fontSize: 30 }}>Here's a way to say it</h1>
        </div>
        <div className="seg" role="group" aria-label="Help level">
          {LEVELS.map((l) => (
            <button key={l.id} aria-pressed={level === l.id} onClick={() => setLevel(l.id)} style={{ height: 42, fontSize: 14 }}>
              {l.label}
            </button>
          ))}
        </div>
      </header>

      <section className="cols">
        <div className="card" style={{ flex: '1 1 260px', maxWidth: 320, padding: 22, gap: 14 }}>
          <div className="eyebrow">You said</div>
          <div style={{ fontSize: 22, lineHeight: 1.45, fontWeight: 600 }} lang={lang.locale}>
            {scaffold.source_text}
          </div>
          {scaffold.feedback && (
            <div className="callout">
              <Icon name="info" size={18} />
              <div>{scaffold.feedback}</div>
            </div>
          )}
          {scaffold.gap_filled.length > 0 && (
            <div className="small muted">
              Filled in for you:{' '}
              {scaffold.gap_filled.map((g) => (
                <span key={g} className="gap-chip" lang={lang.locale}>{g}</span>
              ))}
            </div>
          )}
        </div>

        <div className="card" style={{ flex: '3 1 460px', minWidth: 0, padding: 26 }}>
          {level === 1 && (
            <>
              <div className="eyebrow">Hints · Level 1</div>
              <ul className="hint-list">
                {scaffold.hints.map((h, i) => (
                  <li key={i}>
                    <span className="n">{i + 1}</span>
                    {h}
                  </li>
                ))}
              </ul>
            </>
          )}

          {level === 2 && (
            <>
              <div className="eyebrow">Sentence frame · Level 2</div>
              <div className="frame-text" lang={lang.locale}>
                {(scaffold.frame?.text || scaffold.target).split(/(_{2,})/).map((part, i) =>
                  /^_{2,}$/.test(part) ? (
                    <span key={i} style={{ borderBottom: '4px solid var(--blue)', color: 'var(--blue)', padding: '0 14px' }}>
                      {'    '}
                    </span>
                  ) : (
                    <span key={i}>{part}</span>
                  ),
                )}
              </div>
              <div className="muted">{scaffold.frame?.note || 'Fill the blanks, then say the whole sentence out loud.'}</div>
            </>
          )}

          {full && (
            <>
              <div className="row" style={{ justifyContent: 'space-between' }}>
                <div className="eyebrow">Say this · Level 3</div>
                <div className="row" style={{ gap: 8 }}>
                  {readingLabel && scaffold.reading && (
                    <button className="toggle" aria-pressed={showReading} onClick={() => setShowReading((v) => !v)}>
                      Show {readingLabel.toLowerCase()}
                    </button>
                  )}
                  <button className="toggle" aria-pressed={showIpa} onClick={() => setShowIpa((v) => !v)}>
                    Show IPA
                  </button>
                </div>
              </div>

              <div className="target-text" lang={lang.locale}>
                <AnnotatedText segments={segments} />
              </div>
              {showReading && scaffold.reading && <div className="reading">{scaffold.reading}</div>}
              {showIpa && scaffold.ipa && <div className="ipa" style={{ fontSize: 20 }}>{scaffold.ipa}</div>}
              <div className="muted">{scaffold.meaning}</div>

              <div className="player">
                <button
                  className="round solid-blue"
                  style={{ width: 52, height: 52, flexBasis: 52, borderRadius: 26 }}
                  onClick={audio.toggle}
                  aria-label={audio.playing ? 'Stop' : 'Play sentence'}
                >
                  {audio.playing ? <Pause size={20} /> : <Play size={20} />}
                </button>
                <WaveBars peaks={audio.item?.peaks || []} played={audio.progress} />
                <div className="seg sm" role="group" aria-label="Playback speed">
                  <button aria-pressed={speed === 0.6} onClick={() => setSpeed(0.6)}>0.6×</button>
                  <button aria-pressed={speed === 1} onClick={() => setSpeed(1)}>1×</button>
                </div>
              </div>

              <Legend tags={tags} />
            </>
          )}

          <div className="row" style={{ paddingTop: 4 }}>
            {full ? (
              <>
                <button className="btn btn-primary" onClick={onPractice}>
                  Try it yourself <Icon name="arrow" size={18} stroke={2.5} />
                </button>
                <button className="btn btn-ghost" onClick={save} disabled={saved}>
                  <Icon name="bookmark" size={18} /> {saved ? 'Saved' : 'Save to phrasebook'}
                </button>
              </>
            ) : (
              <>
                <button className="btn btn-solid" onClick={() => setLevel(level + 1)}>
                  {next}
                </button>
                <button className="btn btn-ghost" onClick={onPractice}>
                  Say it now
                </button>
              </>
            )}
          </div>
          {saveError && <div className="error-banner">{saveError}</div>}
        </div>
      </section>

      {full && (
        <>
          <section className="cols">
            <div className="card" style={{ flex: '3 1 460px', minWidth: 0 }}>
              <div>
                <h2>Practice it in chunks</h2>
                <p className="muted small" style={{ margin: '4px 0 0' }}>
                  Start from the end and build backward. It keeps the melody natural.
                </p>
              </div>
              <div className="stack" style={{ gap: 12 }}>
                {[...scaffold.chunks.keys()].reverse().map((i) => (
                  <ChunkRow
                    key={i}
                    chunk={scaffold.chunks[i]}
                    index={i}
                    total={scaffold.chunks.length}
                    lang={lang}
                    showIpa={showIpa}
                    showReading={showReading}
                  />
                ))}
              </div>
            </div>

            {scaffold.sounds.length > 0 && (
              <div className="card" style={{ flex: '2 1 320px', minWidth: 0 }}>
                <h2>Sounds to watch</h2>
                {scaffold.sounds.map((s, i) => (
                  <div className="sound" key={i}>
                    <span className={`sym ${s.tag}`}>{s.symbol || '•'}</span>
                    <div>
                      <b>{s.title}</b>
                      <span className="d">{s.tip}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          {scaffold.variants.length > 0 && (
            <section className="card">
              <h2>Other ways to say it</h2>
              <div className="variants">
                {scaffold.variants.map((v, i) => (
                  <div className="variant" key={i}>
                    <span className="eyebrow">{v.label}</span>
                    <span className="tx" lang={lang.locale}>{v.text}</span>
                  </div>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </>
  )
}
