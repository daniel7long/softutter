const BASE = import.meta.env?.VITE_API_BASE || '/api'

async function json(res) {
  if (!res.ok) {
    let message = res.statusText
    try {
      message = (await res.json()).detail || message
    } catch {
      /* not JSON */
    }
    throw new Error(message)
  }
  if (res.status === 204) return null
  return res.json()
}

const post = (path, body) =>
  fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

export const api = {
  health: () => fetch(`${BASE}/health`).then(json),
  languages: () => fetch(`${BASE}/languages`).then(json),
  scaffold: (body) => post('/scaffold', body).then(json),
  converse: (body) => post('/converse', body).then(json),

  transcribe(blob, language) {
    const form = new FormData()
    form.append('audio', blob, 'speech.wav')
    form.append('language', language)
    return fetch(`${BASE}/transcribe`, { method: 'POST', body: form }).then(json)
  },

  assess(blob, language, chunks, l1) {
    const form = new FormData()
    form.append('audio', blob, 'speech.wav')
    form.append('language', language)
    form.append('chunks', JSON.stringify(chunks))
    form.append('l1', l1)
    return fetch(`${BASE}/assess`, { method: 'POST', body: form }).then(json)
  },

  // Resolves to an audio Blob, or null in demo mode (HTTP 204: the browser speaks instead).
  async tts(text, language, speed) {
    const res = await post('/tts', { text, language, speed })
    if (res.status === 204) return null
    if (!res.ok) throw new Error('Speech synthesis failed')
    return res.blob()
  },

  phrases: (language) =>
    fetch(`${BASE}/phrases${language ? `?language=${language}` : ''}`).then(json),
  addPhrase: (body) => post('/phrases', body).then(json),
  setPhraseStatus: (id, status) =>
    fetch(`${BASE}/phrases/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    }).then(json),
  deletePhrase: (id) => fetch(`${BASE}/phrases/${id}`, { method: 'DELETE' }).then(json),

  sounds: (language) =>
    fetch(`${BASE}/sounds${language ? `?language=${language}` : ''}`).then(json),
  logSounds: (language, events) => post('/sounds/events', { language, events }).then(json),
}
