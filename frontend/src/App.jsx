import { useEffect, useState } from 'react'
import Sidebar from './components/Sidebar.jsx'
import Compose from './components/Compose.jsx'
import Result from './components/Result.jsx'
import Shadow from './components/Shadow.jsx'
import Phrasebook from './components/Phrasebook.jsx'
import Sounds from './components/Sounds.jsx'
import Conversation from './components/Conversation.jsx'
import { api } from './lib/api.js'
import { setLocales, setMockMode } from './lib/audio.js'
import { useStoredState } from './lib/storage.js'

const DEFAULTS = { lang: 'fr', l1: 'en', level: 2, ctx: 'cafe', register: 'polite' }

export default function App() {
  const [settings, setSettings] = useStoredState('softutter.settings', DEFAULTS)
  const [langs, setLangs] = useState([])
  const [health, setHealth] = useState(null)
  const [bootError, setBootError] = useState('')
  const [screen, setScreen] = useState('compose')
  const [scaffold, setScaffold] = useState(null)
  const [phrase, setPhrase] = useState(null) // saved phrase currently being practiced
  const [convo, setConvo] = useState(null) // conversation in progress (kept while you visit other screens)
  const [backTo, setBackTo] = useState(null) // where Shadow returns to when it was opened from a conversation

  useEffect(() => {
    Promise.all([api.languages(), api.health()])
      .then(([l, h]) => {
        setLangs(l)
        setHealth(h)
        setMockMode(h.mock)
        setLocales(Object.fromEntries(l.map((x) => [x.code, x.locale])))
      })
      .catch((e) =>
        setBootError(
          `Can't reach the SoftUtter backend (${e.message}). Start it with: uvicorn app.main:app --reload --port 8000`,
        ),
      )
  }, [])

  if (bootError) {
    return (
      <div className="main" style={{ maxWidth: 720, margin: '0 auto' }}>
        <h1>SoftUtter</h1>
        <div className="error-banner" role="alert">{bootError}</div>
      </div>
    )
  }
  if (!langs.length) return <div className="main muted">Loading…</div>

  const lang = langs.find((l) => l.code === settings.lang) || langs[0]
  const activeLang = scaffold ? langs.find((l) => l.code === scaffold.language) || lang : lang

  const openPhrase = (p, from = 'phrasebook') => {
    const s = p.payload && p.payload.chunks ? p.payload : null
    if (!s) return
    setPhrase({ ...p, from })
    setBackTo(null)
    setScaffold(s)
    setScreen('shadow')
  }

  return (
    <div className="app">
      <Sidebar
        screen={screen}
        langName={lang.name.replace(' (Mandarin)', '')}
        onNavigate={(s) => {
          setScreen(s)
          if (s === 'compose') {
            setScaffold(null)
            setPhrase(null)
            setBackTo(null)
          }
        }}
      />
      <main className="main">
        {health?.mock && (
          <div className="demo-banner">
            Demo mode: no OpenAI key found, so you'll see sample content and your browser's own voices. Add a key
            to backend/.env to scaffold your own sentences.
          </div>
        )}

        {screen === 'compose' && (
          <Compose
            langs={langs}
            settings={settings}
            setSettings={setSettings}
            onOpenPhrase={(p) => openPhrase(p, 'compose')}
            onOpenSounds={() => setScreen('sounds')}
            onScaffold={(s) => {
              setScaffold(s)
              setPhrase(null)
              setBackTo(null)
              setScreen('result')
            }}
          />
        )}
        {screen === 'result' && scaffold && (
          <Result
            key={scaffold.target}
            scaffold={scaffold}
            lang={activeLang}
            settings={settings}
            onBack={() => setScreen('compose')}
            onPractice={() => setScreen('shadow')}
          />
        )}
        {screen === 'shadow' && scaffold && (
          <Shadow
            key={scaffold.target}
            scaffold={scaffold}
            lang={activeLang}
            settings={settings}
            phrase={phrase}
            onBack={() => setScreen(phrase ? phrase.from || 'phrasebook' : backTo || 'result')}
            onDone={() => {
              setScaffold(null)
              setPhrase(null)
              setScreen(backTo || 'compose')
              setBackTo(null)
            }}
          />
        )}
        {screen === 'conversation' && (
          <Conversation
            langs={langs}
            settings={settings}
            setSettings={setSettings}
            mock={!!health?.mock}
            session={convo}
            setSession={setConvo}
            onPractice={(s) => {
              setScaffold(s)
              setPhrase(null)
              setBackTo('conversation')
              setScreen('shadow')
            }}
          />
        )}
        {screen === 'phrasebook' && <Phrasebook langs={langs} onOpen={openPhrase} />}
        {screen === 'sounds' && <Sounds langs={langs} settings={settings} onOpen={(p) => openPhrase(p, 'sounds')} />}
      </main>
    </div>
  )
}
