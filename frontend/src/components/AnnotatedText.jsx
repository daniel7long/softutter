export const TAG_LABELS = {
  care: 'Needs care',
  silent: 'Silent or reduced',
  link: 'Linked',
  tone: 'Tone or pitch',
}

// Renders segments [{text, tag}] with sound-annotation styling.
export default function AnnotatedText({ segments, className = '' }) {
  return (
    <span className={className}>
      {segments.map((s, i) =>
        s.tag && s.tag !== 'none' ? (
          <span key={i} className={`tag-${s.tag}`}>
            {s.text}
          </span>
        ) : (
          <span key={i}>{s.text}</span>
        ),
      )}
    </span>
  )
}

export function tagsIn(segments) {
  return [...new Set(segments.map((s) => s.tag).filter((t) => t && t !== 'none'))]
}

export function Legend({ tags }) {
  if (!tags.length) return null
  return (
    <div className="legend">
      {tags.map((t) => (
        <span className="item" key={t}>
          <span className={`tag-${t}`} style={{ fontWeight: 700 }}>
            ab
          </span>
          {TAG_LABELS[t]}
        </span>
      ))}
    </div>
  )
}

// All chunks of a scaffold as one segment list, separated the way the language is written.
export function sentenceSegments(chunks, join) {
  const out = []
  chunks.forEach((c, i) => {
    if (i > 0 && join) out.push({ text: join, tag: 'none' })
    out.push(...c.segments)
  })
  return out
}
