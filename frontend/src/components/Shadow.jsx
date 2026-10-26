import { useEffect, useMemo, useRef, useState } from 'react'
import AnnotatedText, { Legend, sentenceSegments, tagsIn } from './AnnotatedText.jsx'
import WaveBars from './WaveBars.jsx'
import { Icon, Pause, Play, Stop } from './Icon.jsx'
import { api } from '../lib/api.js'
import { usePlayer, useTargetAudio } from '../lib/hooks.js'
import { useRecorder } from '../lib/recorder.js'

export default function Shadow({ scaffold, lang, settings, phrase, onBack, onDone }) {
  const chunks = scaffold.chunks
  // Back-chaining: last chunk first, then build toward the whole sentence.
  const steps = useMemo(
    () =>
      chunks.length > 1
        ? [...chunks.keys()].reverse().map((i) => ({ type: 'chunk', i })).concat([{ type: 'whole' }])
        : [{ type: 'whole' }],
    [chunks],
  )

  const [stepIdx, setStepIdx] = useState(0)
  const [heard, setHeard] = useState(false)
  const [attempt, setAttempt] = useState(null) // { clip, loading?, result?, error? }
  const [outcomes, setOutcomes] = useState([])
  const [finished, setFinished] = useState(false)
  const [slow, setSlow] = useState(false)
  const [micError, setMicError] = useState('')
  const [saved, setSaved] = useState(!!phrase)

  const rec = useRecorder()
  const loggedSeen = useRef(false)

  // Opening a phrase counts as "seeing" its sounds; attempts add clear / needs-another-go.
  useEffect(() => {
    if (loggedSeen.current || !scaffold.sounds?.length) return
    loggedSeen.current = true
    api
      .logSounds(
        lang.code,
        scaffold.sounds.map((s) => ({ title: s.title, symbol: s.symbol, tag: s.tag, tip: s.tip, outcome: 'seen' })),
      )
      .catch(() => {})
  }, [])

  const step = steps[Math.min(stepIdx, steps.length - 1)]
  const unit = step.type === 'chunk' ? chunks[step.i] : null
  const targetText = unit ? unit.text : scaffold.target
  const checkChunks = unit ? [unit.text] : chunks.map((c) => c.text)
  const segments = unit ? unit.segments : sentenceSegments(chunks, lang.join)
  const ipa = unit ? unit.ipa : scaffold.ipa
  const reading = unit ? unit.reading : scaffold.reading

  const target = useTargetAudio(targetText, lang.code, slow ? 0.6 : 1)
  const yours = usePlayer(() => Promise.resolve(attempt?.clip))

  const recording = rec.state === 'recording'
  const stage = finished || step.type === 'whole' ? 3 : heard || attempt ? 2 : 1

  async function toggleRecording() {
    setMicError('')
    if (recording) {
      const clip = await rec.stop()
      setAttempt({ clip, loading: true })
      try {
        const result = await api.assess(clip.blob, lang.code, checkChunks, settings.l1)
        setAttempt({ clip, result })
        logSoundOutcomes(result)
      } catch (e) {
        setAttempt({ clip, error: e.message })
      }
    } else {
      yours.stop()
      target.stop()
      setHeard(true)
      setAttempt(null)
      try {
        await rec.start()
      } catch {
        setMicError('The microphone is not available. Check the browser permission and try again.')
      }
    }
  }

  // Attribute each chunk's result to the sounds that occur in it.
  function logSoundOutcomes(result) {
    const checked = unit ? [step.i] : chunks.map((_, i) => i)
    const status = {}
    result.chunks.forEach((c, j) => {
      status[checked[j]] = c.status
    })
    const events = []
    for (const s of scaffold.sounds || []) {
      const where = (s.chunks && s.chunks.length ? s.chunks : chunks.map((_, i) => i)).filter((i) => i in status)
      if (!where.length) continue
      events.push({
        title: s.title,
        symbol: s.symbol,
        tag: s.tag,
        tip: s.tip,
        outcome: where.some((i) => status[i] === 'care') ? 'care' : 'clear',
      })
    }
    if (events.length) api.logSounds(lang.code, events).catch(() => {})
  }

  function playTarget() {
    setHeard(true)
    target.toggle()
  }

  async function next() {
    const outcome = attempt?.result && !attempt.result.focus ? 'own' : 'echo'
    const all = [...outcomes, outcome]
    setOutcomes(all)
    target.stop()
    yours.stop()
    setAttempt(null)
    setHeard(false)
    if (stepIdx >= steps.length - 1) {
      setFinished(true)
      if (phrase) {
        try {
          await api.setPhraseStatus(phrase.id, outcome)
        } catch {
          /* non-critical */
        }
      }
    } else {
      setStepIdx(stepIdx + 1)
    }
  }

  async function saveFinal() {
    const status = outcomes[outcomes.length - 1] || 'echo'
    try {
      const p = await api.addPhrase({
        language: scaffold.language,
        target: scaffold.target,
        meaning: scaffold.meaning,
        reading: scaffold.reading,
        ipa: scaffold.ipa,
        payload: scaffold,
      })
      await api.setPhraseStatus(p.id, status)
      setSaved(true)
    } catch (e) {
      setMicError(e.message)
    }
  }

  const result = attempt?.result
  const stageItems = [
    ['Listen', 1],
    ['Echo', 2],
    ['Own it', 3],
  ]

  if (finished) {
    return (
      <>
        <section className="card celebrate">
          <div className="eyebrow">All chunks done</div>
          <h1>Nicely done.</h1>
          <div className="target-text" lang={lang.locale}>
            <AnnotatedText segments={sentenceSegments(chunks, lang.join)} />
          </div>
          <p className="muted">{scaffold.meaning}</p>
          <div className="row" style={{ justifyContent: 'center' }}>
            <button className="btn btn-primary" onClick={onDone}>
              Say something new <Icon name="arrow" size={18} stroke={2.5} />
            </button>
            <button className="btn btn-ghost" onClick={saveFinal} disabled={saved}>
              <Icon name="bookmark" size={18} /> {saved ? 'In your phrasebook' : 'Save to phrasebook'}
            </button>
          </div>
          {micError && <div className="error-banner">{micError}</div>}
        </section>
      </>
    )
  }

  return (
    <>
      <header className="row" style={{ justifyContent: 'space-between' }}>
        <div className="stack" style={{ gap: 6 }}>
          <button className="back-link" onClick={onBack}>
            <Icon name="back" size={16} stroke={2.5} /> Back to the sentence
          </button>
          <h1 style={{ fontSize: 30 }}>Echo it, then compare</h1>
        </div>
        <ol className="stepper" aria-label="Progress">
          {stageItems.map(([label, n], i) => (
            <li key={label} className={stage > n ? 'done' : stage === n ? 'now' : ''} aria-current={stage === n ? 'step' : undefined}>
              {i > 0 && <span className="bar" aria-hidden="true" />}
              <span className="dot">{stage > n ? <Icon name="check" size={14} stroke={3.5} /> : n}</span>
              {label}
            </li>
          ))}
        </ol>
      </header>

      <section className="cols">
        <div className="stack" style={{ flex: '3 1 520px' }}>
          <div className="card" style={{ padding: 26 }}>
            <div className="row" style={{ justifyContent: 'space-between' }}>
              <div className="eyebrow">
                {unit ? `Chunk ${step.i + 1} of ${chunks.length}` : 'The whole sentence'}
              </div>
              <div className="small">
                {reading && <span className="reading" style={{ fontSize: 15 }}>{reading} </span>}
                {ipa && <span className="ipa">{ipa}</span>}
              </div>
            </div>

            <div className="target-text md" lang={lang.locale}>
              <AnnotatedText segments={segments} />
            </div>
            <Legend tags={tagsIn(segments)} />
            {unit?.tip && <div className="muted">{unit.tip}</div>}

            <div className="compare">
              <div className="line">
                <button
                  className="round solid-blue"
                  onClick={playTarget}
                  aria-label={target.playing ? 'Stop target' : 'Play target'}
                >
                  {target.playing ? <Pause /> : <Play />}
                </button>
                <div className="who" style={{ color: 'var(--blue-ink)' }}>Target</div>
                <WaveBars peaks={target.item?.peaks || []} played={target.progress} />
              </div>
              <div className="line">
                <button
                  className="round solid-teal"
                  onClick={yours.toggle}
                  disabled={!attempt?.clip}
                  aria-label={yours.playing ? 'Stop your recording' : 'Play your recording'}
                >
                  {yours.playing ? <Pause /> : <Play />}
                </button>
                <div className="who" style={{ color: 'var(--teal-ink)' }}>You</div>
                {recording ? (
                  <WaveBars peaks={rec.levels.length ? rec.levels : [0.1]} live />
                ) : attempt?.clip ? (
                  <WaveBars peaks={attempt.clip.peaks} played={yours.progress} tone="teal" />
                ) : (
                  <div className="muted small" style={{ flex: 1 }}>Your recording appears here.</div>
                )}
              </div>
            </div>

            <div className="row">
              <button className="btn btn-rec" onClick={toggleRecording} style={{ padding: '0 24px' }}>
                {recording ? <Stop size={16} /> : <Icon name="mic" size={18} stroke={2.2} />}
                {recording ? `Stop · 00:${String(rec.seconds).padStart(2, '0')}` : attempt ? 'Record again' : 'Record'}
              </button>
              <button className="toggle" aria-pressed={slow} onClick={() => setSlow((v) => !v)} style={{ height: 48 }}>
                Slow target 0.6×
              </button>
              <span className="muted small">Take your time. Every try is private.</span>
            </div>
            {micError && <div className="error-banner" role="alert">{micError}</div>}
          </div>

          {attempt && (
            <div className="card">
              {attempt.loading && <div className="muted">Listening back…</div>}
              {attempt.error && <div className="error-banner" role="alert">{attempt.error}</div>}
              {result && (
                <>
                  <div>
                    <h2>{result.focus ? 'Nearly there' : 'That matched well'}</h2>
                    <p className="muted small" style={{ margin: '4px 0 0' }}>
                      No score. Just the one thing worth fixing next.
                    </p>
                  </div>
                  {result.wins.map((w, i) => (
                    <div className="fb win" key={i}>
                      <Icon name="check" size={22} stroke={2.5} />
                      <div>{w}</div>
                    </div>
                  ))}
                  {result.focus && (
                    <div className="fb focus">
                      <Icon name="info" size={22} />
                      <div className="txt">
                        <b lang={lang.locale}>“{result.focus.unit}”</b> {result.focus.tip}
                      </div>
                      <div className="row" style={{ gap: 8 }}>
                        <button className="btn btn-ghost btn-sm" style={{ borderColor: 'var(--amber)' }} onClick={playTarget}>
                          Hear target
                        </button>
                        <button className="btn btn-ghost btn-sm" style={{ borderColor: 'var(--amber)' }} onClick={yours.toggle}>
                          Hear you
                        </button>
                      </div>
                    </div>
                  )}
                  <div className="small muted">
                    I heard: <span lang={lang.locale}>{result.heard || '…'}</span>
                    {result.mock && ' (demo mode: sample feedback)'}
                  </div>
                </>
              )}
            </div>
          )}
        </div>

        <aside className="card" style={{ flex: '1 1 280px', maxWidth: 380, minWidth: 0 }}>
          <h2>Your build-up</h2>
          <p className="muted small" style={{ margin: 0, lineHeight: 1.45 }}>
            We start at the end and work backward, so the sentence keeps its melody.
          </p>
          {steps.map((s, i) => {
            const state = i < stepIdx ? 'done' : i === stepIdx ? 'now' : s.type === 'whole' ? 'locked' : ''
            const label = s.type === 'chunk' ? chunks[s.i].text : 'Then the whole sentence'
            return (
              <div className={`queue-item ${state}`} key={i} lang={s.type === 'chunk' ? lang.locale : undefined}>
                {state === 'locked' ? (
                  <Icon name="lock" size={20} />
                ) : (
                  <span className="badge">{state === 'done' ? <Icon name="check" size={14} stroke={3.5} /> : i + 1}</span>
                )}
                {label}
              </div>
            )
          })}
          <div className="stack" style={{ gap: 10, paddingTop: 8 }}>
            <button className="btn btn-primary" onClick={next}>
              {stepIdx >= steps.length - 1 ? 'Finish' : 'Good enough, next chunk'}
            </button>
            <button className="btn btn-ghost" onClick={() => { setAttempt(null); setHeard(false) }}>
              Try this {unit ? 'chunk' : 'sentence'} again
            </button>
          </div>
        </aside>
      </section>
    </>
  )
}
