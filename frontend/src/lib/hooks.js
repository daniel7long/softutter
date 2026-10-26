import { useCallback, useEffect, useRef, useState } from 'react'
import { loadSpeech, playItem } from './audio.js'

// Generic player. getItem() resolves to { url?, text?, lang?, speed?, peaks }.
export function usePlayer(getItem) {
  const [playing, setPlaying] = useState(false)
  const [progress, setProgress] = useState(0)
  const stopRef = useRef(null)
  const getRef = useRef(getItem)
  getRef.current = getItem

  const stop = useCallback(() => {
    stopRef.current?.()
    stopRef.current = null
    setPlaying(false)
    setProgress(0)
  }, [])

  const toggle = useCallback(async () => {
    if (stopRef.current) {
      stop()
      return
    }
    const item = await getRef.current()
    if (!item) return
    setPlaying(true)
    stopRef.current = playItem(item, {
      onProgress: setProgress,
      onEnd: () => {
        stopRef.current = null
        setPlaying(false)
        setProgress(0)
      },
    })
  }, [stop])

  useEffect(() => () => stopRef.current?.(), [])
  return { playing, progress, toggle, stop }
}

// Target speech with eagerly loaded waveform peaks.
export function useTargetAudio(text, lang, speed = 1) {
  const [item, setItem] = useState(null)
  useEffect(() => {
    let alive = true
    setItem(null)
    if (text) loadSpeech(text, lang, speed).then((i) => alive && setItem(i))
    return () => {
      alive = false
    }
  }, [text, lang, speed])
  const player = usePlayer(() => (text ? loadSpeech(text, lang, speed) : null))
  return { item, ...player }
}

// Target speech loaded only when played (for lists).
export function useLazyAudio(text, lang, speed = 1) {
  return usePlayer(() => loadSpeech(text, lang, speed))
}
