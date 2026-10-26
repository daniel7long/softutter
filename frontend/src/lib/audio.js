// Target-speech loading and playback.
// Real mode: the backend returns mp3 (OpenAI TTS). Demo mode / failures: the browser's
// own speech synthesis speaks the text, and the waveform is synthetic.
import { api } from './api.js'

let MOCK = false
let LOCALES = {}
export const setMockMode = (m) => {
  MOCK = !!m
}
export const setLocales = (map) => {
  LOCALES = map
}

export function fakePeaks(text, n = 36) {
  let h = 0
  for (const ch of text) h = (h * 31 + ch.codePointAt(0)) >>> 0
  const out = []
  for (let i = 0; i < n; i++) {
    h = (h * 1664525 + 1013904223) >>> 0
    const env = Math.sin((Math.PI * i) / (n - 1)) * 0.5 + 0.35
    out.push(Math.min(1, 0.18 + (((h >>> 8) % 100) / 100) * env))
  }
  return out
}

export function peaksFromSamples(samples, n = 36) {
  const size = Math.max(1, Math.floor(samples.length / n))
  const rms = []
  let max = 0.0001
  for (let i = 0; i < n; i++) {
    let sum = 0
    const start = i * size
    const end = Math.min(samples.length, start + size)
    for (let k = start; k < end; k++) sum += samples[k] * samples[k]
    const v = Math.sqrt(sum / Math.max(1, end - start))
    rms.push(v)
    if (v > max) max = v
  }
  return rms.map((v) => Math.max(0.08, v / max))
}

async function peaksFromBlob(blob, n = 36) {
  const Ctx = window.AudioContext || window.webkitAudioContext
  const ctx = new Ctx()
  try {
    const buf = await ctx.decodeAudioData(await blob.arrayBuffer())
    return peaksFromSamples(buf.getChannelData(0), n)
  } finally {
    ctx.close()
  }
}

const cache = new Map()

export async function loadSpeech(text, lang, speed = 1) {
  const key = `${lang}|${speed}|${text}`
  if (cache.has(key)) return cache.get(key)
  let item = null
  if (!MOCK) {
    try {
      const blob = await api.tts(text, lang, speed)
      if (blob) {
        item = { url: URL.createObjectURL(blob), peaks: await peaksFromBlob(blob), synthetic: false }
      }
    } catch {
      item = null
    }
  }
  if (!item) item = { url: null, peaks: fakePeaks(text), synthetic: true, text, lang, speed }
  cache.set(key, item)
  return item
}

// Plays an item; returns a stop() function.
export function playItem(item, { onProgress, onEnd }) {
  if (item.url) {
    const audio = new Audio(item.url)
    let raf = 0
    const tick = () => {
      if (audio.duration) onProgress(audio.currentTime / audio.duration)
      raf = requestAnimationFrame(tick)
    }
    audio.onended = () => {
      cancelAnimationFrame(raf)
      onEnd()
    }
    audio.onerror = () => {
      cancelAnimationFrame(raf)
      onEnd()
    }
    audio.play().then(
      () => {
        raf = requestAnimationFrame(tick)
      },
      () => onEnd(),
    )
    return () => {
      cancelAnimationFrame(raf)
      audio.pause()
    }
  }

  const synth = window.speechSynthesis
  if (!synth) {
    onEnd()
    return () => {}
  }
  synth.cancel()
  const utter = new SpeechSynthesisUtterance(item.text)
  utter.lang = LOCALES[item.lang] || item.lang
  utter.rate = item.speed || 1
  const estimate = Math.max(1.2, (item.text.length * 0.085) / (item.speed || 1))
  const t0 = performance.now()
  let raf = 0
  let done = false
  let timer = 0
  const finish = () => {
    if (done) return
    done = true
    cancelAnimationFrame(raf)
    clearTimeout(timer)
    onEnd()
  }
  const tick = () => {
    onProgress(Math.min(0.98, (performance.now() - t0) / 1000 / estimate))
    raf = requestAnimationFrame(tick)
  }
  utter.onend = finish
  utter.onerror = finish
  synth.speak(utter)
  raf = requestAnimationFrame(tick)
  timer = setTimeout(finish, (estimate + 1.5) * 1000) // some browsers never fire onend
  return () => {
    done = true
    cancelAnimationFrame(raf)
    clearTimeout(timer)
    synth.cancel()
  }
}
