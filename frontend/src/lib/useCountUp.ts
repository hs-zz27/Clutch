import { useEffect, useRef, useState } from 'react'

/**
 * Animate a number from its previous value to the current one whenever it
 * changes (and from 0 on first mount). Honors prefers-reduced-motion.
 * All state writes happen inside rAF callbacks, never synchronously in the
 * effect body (keeps the react-hooks lint rules happy).
 */
export function useCountUp(value: number, durationMs = 900): number {
  const [display, setDisplay] = useState(0)
  const fromRef = useRef(0)

  useEffect(() => {
    const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false
    const from = fromRef.current

    if (reduce || !Number.isFinite(value) || from === value) {
      fromRef.current = value
      const id = requestAnimationFrame(() => setDisplay(value))
      return () => cancelAnimationFrame(id)
    }

    const start = performance.now()
    let raf = requestAnimationFrame(function tick(t) {
      const p = Math.min(1, (t - start) / durationMs)
      const eased = 1 - Math.pow(1 - p, 3)
      setDisplay(from + (value - from) * eased)
      if (p < 1) {
        raf = requestAnimationFrame(tick)
      } else {
        fromRef.current = value
      }
    })
    return () => cancelAnimationFrame(raf)
  }, [value, durationMs])

  return display
}
