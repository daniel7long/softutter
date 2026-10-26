// Bars from peaks (0..1). `played` (0..1) colors the first part as active.
export default function WaveBars({ peaks, played = 0, tone = 'blue', live = false }) {
  const bars = peaks && peaks.length ? peaks : []
  const cut = Math.round(bars.length * played)
  return (
    <div className={`wave ${tone === 'teal' ? 'teal' : ''} ${live ? 'live' : ''}`} aria-hidden="true">
      {bars.map((p, i) => (
        <span
          key={i}
          className={live || i < cut ? 'on' : ''}
          style={{ height: `${Math.max(6, Math.round(p * 44))}px` }}
        />
      ))}
    </div>
  )
}
