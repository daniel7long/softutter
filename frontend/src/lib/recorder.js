// Microphone recorder that produces a 16 kHz mono 16-bit WAV (works with OpenAI STT
// and Azure Speech without ffmpeg) plus waveform peaks for display.
import { useCallback, useEffect, useRef, useState } from 'react'
import { peaksFromSamples } from './audio.js'

const TARGET_RATE = 16000

function concat(parts) {
  const total = parts.reduce((n, p) => n + p.length, 0)
  const out = new Float32Array(total)
  let offset = 0
  for (const p of parts) {
    out.set(p, offset)
    offset += p.length
  }
  return out
}

function downsample(buf, from, to) {
  if (to >= from) return buf
  const ratio = from / to
  const len = Math.floor(buf.length / ratio)
  const out = new Float32Array(len)
  for (let i = 0; i < len; i++) {
    const s = Math.floor(i * ratio)
    const e = Math.min(buf.length, Math.floor((i + 1) * ratio))
    let sum = 0
    for (let k = s; k < e; k++) sum += buf[k]
    out[i] = sum / Math.max(1, e - s)
  }
  return out
}

function encodeWav(samples, rate) {
  const buffer = new ArrayBuffer(44 + samples.length * 2)
  const v = new DataView(buffer)
  const str = (o, s) => {
    for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i))
  }
  str(0, 'RIFF')
  v.setUint32(4, 36 + samples.length * 2, true)
  str(8, 'WAVE')
  str(12, 'fmt ')
  v.setUint32(16, 16, true)
  v.setUint16(20, 1, true) // PCM
  v.setUint16(22, 1, true) // mono
  v.setUint32(24, rate, true)
  v.setUint32(28, rate * 2, true)
  v.setUint16(32, 2, true)
  v.setUint16(34, 16, true)
  str(36, 'data')
  v.setUint32(40, samples.length * 2, true)
  let o = 44
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]))
    v.setInt16(o, s < 0 ? s * 0x8000 : s * 0x7fff, true)
    o += 2
  }
  return new Blob([buffer], { type: 'audio/wav' })
}

export function useRecorder() {
  const [state, setState] = useState('idle') // idle | recording
  const [levels, setLevels] = useState([])
  const [seconds, setSeconds] = useState(0)
  const r = useRef({})

  const cleanup = useCallback(() => {
    const s = r.current
    clearInterval(s.timer)
    try {
      s.proc?.disconnect()
      s.src?.disconnect()
      s.stream?.getTracks().forEach((t) => t.stop())
      if (s.ctx && s.ctx.state !== 'closed') s.ctx.close().catch(() => {})
    } catch {
      /* already closed */
    }
    r.current = {}
  }, [])

  useEffect(() => cleanup, [cleanup])

  const start = useCallback(async () => {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true },
    })
    const Ctx = window.AudioContext || window.webkitAudioContext
    const ctx = new Ctx()
    const src = ctx.createMediaStreamSource(stream)
    const proc = ctx.createScriptProcessor(4096, 1, 1)
    const parts = []
    proc.onaudioprocess = (e) => {
      const data = e.inputBuffer.getChannelData(0)
      parts.push(new Float32Array(data))
      let sum = 0
      for (let i = 0; i < data.length; i++) sum += data[i] * data[i]
      const rms = Math.min(1, Math.sqrt(sum / data.length) * 6)
      setLevels((prev) => [...prev.slice(-35), Math.max(0.08, rms)])
    }
    src.connect(proc)
    proc.connect(ctx.destination)
    const t0 = Date.now()
    const timer = setInterval(() => setSeconds(Math.floor((Date.now() - t0) / 1000)), 250)
    r.current = { stream, ctx, src, proc, parts, timer, t0 }
    setLevels([])
    setSeconds(0)
    setState('recording')
  }, [])

  // Resolves to { blob, url, peaks, duration }.
  const stop = useCallback(async () => {
    const s = r.current
    const rate = s.ctx?.sampleRate || 48000
    const samples = concat(s.parts || [])
    cleanup()
    setState('idle')
    const down = downsample(samples, rate, TARGET_RATE)
    const blob = encodeWav(down, TARGET_RATE)
    return {
      blob,
      url: URL.createObjectURL(blob),
      peaks: peaksFromSamples(down, 36),
      duration: down.length / TARGET_RATE,
    }
  }, [cleanup])

  return { state, levels, seconds, start, stop }
}
