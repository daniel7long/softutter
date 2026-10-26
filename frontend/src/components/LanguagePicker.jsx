export default function LanguagePicker({ langs, value, onChange }) {
  return (
    <div className="chips" role="group" aria-label="Language you are learning">
      {langs.map((l) => (
        <button
          key={l.code}
          className="chip"
          aria-pressed={value === l.code}
          onClick={() => onChange(l.code)}
          lang={l.locale}
        >
          <span className="native">{l.native}</span>
          <span className="en">{l.name.replace(' (Mandarin)', '')}</span>
        </button>
      ))}
    </div>
  )
}
