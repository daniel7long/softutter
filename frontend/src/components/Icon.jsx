const PATHS = {
  mic: (
    <>
      <path d="M12 3a3 3 0 0 0-3 3v5a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3z" />
      <path d="M5 11a7 7 0 0 0 14 0M12 18v3" />
    </>
  ),
  keyboard: (
    <>
      <rect x="3" y="6" width="18" height="12" rx="2" />
      <path d="M7 10h.01M11 10h.01M15 10h.01M7 14h10" />
    </>
  ),
  globe: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18" />
    </>
  ),
  chat: <path d="M4 5h16v11H9l-5 4z" />,
  book: (
    <>
      <path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3z" />
      <path d="M5 17a3 3 0 0 1 3-3h11" />
    </>
  ),
  waves: <path d="M4 12h.01M8 8v8M12 4v16M16 8v8M20 12h.01" />,
  arrow: <path d="M5 12h14M13 6l6 6-6 6" />,
  back: <path d="M19 12H5M11 6l-6 6 6 6" />,
  check: <path d="M5 12l5 5 9-10" />,
  info: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 8v5M12 16h.01" />
    </>
  ),
  bookmark: <path d="M6 4h12v17l-6-4-6 4z" />,
  lock: (
    <>
      <rect x="5" y="11" width="14" height="9" rx="2" />
      <path d="M8 11V8a4 4 0 0 1 8 0v3" />
    </>
  ),
  trash: <path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3" />,
}

export function Icon({ name, size = 20, stroke = 2 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={stroke}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {PATHS[name]}
    </svg>
  )
}

export function Play({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M7 4l13 8-13 8z" />
    </svg>
  )
}

export function Stop({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 20 20" aria-hidden="true">
      <rect x="3" y="3" width="14" height="14" rx="3" fill="currentColor" />
    </svg>
  )
}

export function Pause({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M6 4h4v16H6zM14 4h4v16h-4z" />
    </svg>
  )
}

export function Logo({ size = 40 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" aria-hidden="true">
      <defs>
        <linearGradient id="su-logo" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#2B6BE0" />
          <stop offset="1" stopColor="#0B9C94" />
        </linearGradient>
      </defs>
      <path
        d="M20 4C10.600 4 3 10.300 3 18.200c0 4.300 2.300 8.100 5.900 10.700L7.500 35l6.600-3.400c1.900.5 3.900.8 5.900.8 9.400 0 17-6.300 17-14.200S29.400 4 20 4z"
        fill="url(#su-logo)"
      />
      <rect x="11" y="15" width="3" height="6" rx="1.5" fill="#fff" />
      <rect x="16.5" y="11.5" width="3" height="13" rx="1.5" fill="#fff" />
      <rect x="22" y="14" width="3" height="8" rx="1.5" fill="#fff" />
      <rect x="27.5" y="16" width="3" height="4" rx="1.5" fill="#fff" />
    </svg>
  )
}
