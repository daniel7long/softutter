import { Icon, Logo } from './Icon.jsx'

export default function Sidebar({ screen, onNavigate, langName }) {
  const practiceScreens = ['compose', 'result', 'shadow']
  return (
    <aside className="sidebar">
      <div className="brand">
        <Logo />
        <div>
          <div className="brand-name">
            <span className="soft">Soft</span>
            <span className="utter">Utter</span>
          </div>
          <div className="brand-tag">Friendly speech scaffolding</div>
        </div>
      </div>

      <nav className="nav" aria-label="Main">
        <button
          aria-current={practiceScreens.includes(screen) ? 'page' : undefined}
          onClick={() => onNavigate('compose')}
        >
          <Icon name="mic" /> Practice
        </button>
        <button
          aria-current={screen === 'conversation' ? 'page' : undefined}
          onClick={() => onNavigate('conversation')}
        >
          <Icon name="chat" /> Conversation
        </button>
        <button
          aria-current={screen === 'phrasebook' ? 'page' : undefined}
          onClick={() => onNavigate('phrasebook')}
        >
          <Icon name="book" /> Phrasebook
        </button>
        <button
          aria-current={screen === 'sounds' ? 'page' : undefined}
          onClick={() => onNavigate('sounds')}
        >
          <Icon name="waves" /> My sounds
        </button>
      </nav>

      <div className="side-note">
        <b>Learning {langName}</b>
        <span>Low-pressure mode: no scores, no streaks. Say it your way.</span>
      </div>
    </aside>
  )
}
