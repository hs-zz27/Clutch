import type { ReactNode } from 'react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { cx } from '../lib/format'

type ScrollHintPanelProps = {
  children: ReactNode
  className?: string
  maxHeightClass: string
  hint: string
}

type ScrollState = {
  hasOverflow: boolean
  nearBottom: boolean
}

export function ScrollHintPanel({
  children,
  className,
  maxHeightClass,
  hint,
}: ScrollHintPanelProps) {
  const ref = useRef<HTMLDivElement | null>(null)
  const [scrollState, setScrollState] = useState<ScrollState>({
    hasOverflow: false,
    nearBottom: false,
  })

  const measure = useCallback(() => {
    const el = ref.current
    if (!el) return

    const hasOverflow = el.scrollHeight > el.clientHeight + 8
    const nearBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 24

    setScrollState((prev) =>
      prev.hasOverflow === hasOverflow && prev.nearBottom === nearBottom
        ? prev
        : { hasOverflow, nearBottom },
    )
  }, [])

  useEffect(() => {
    const el = ref.current
    if (!el) return

    let frameId: number | null = null
    const scheduleMeasure = () => {
      if (frameId != null) window.cancelAnimationFrame(frameId)
      frameId = window.requestAnimationFrame(() => {
        frameId = null
        measure()
      })
    }

    scheduleMeasure()

    const resizeObserver = new ResizeObserver(scheduleMeasure)
    resizeObserver.observe(el)

    const mutationObserver = new MutationObserver(scheduleMeasure)
    mutationObserver.observe(el, { childList: true, subtree: true })

    return () => {
      resizeObserver.disconnect()
      mutationObserver.disconnect()
      if (frameId != null) window.cancelAnimationFrame(frameId)
    }
  }, [measure])

  const showHint = scrollState.hasOverflow && !scrollState.nearBottom

  return (
    <div className={cx('relative', className)}>
      <div
        ref={ref}
        onScroll={measure}
        tabIndex={scrollState.hasOverflow ? 0 : undefined}
        aria-label={scrollState.hasOverflow ? hint : undefined}
        className={cx(
          maxHeightClass,
          'scrollbar-polished overflow-y-auto overscroll-contain pr-2 focus:outline-none focus:ring-2 focus:ring-ember/40',
        )}
      >
        {children}
      </div>

      {showHint ? (
        <>
          <div className="pointer-events-none absolute inset-x-0 bottom-0 h-14 rounded-b-lg bg-gradient-to-t from-surface via-surface/90 to-transparent" />
          <div className="scroll-hint-pill pointer-events-none absolute bottom-2 left-1/2 -translate-x-1/2 rounded-full border-2 border-line bg-ember px-3 py-1 font-mono text-[10px] font-700 uppercase tracking-[0.14em] text-line">
            {hint}
          </div>
        </>
      ) : null}
    </div>
  )
}
