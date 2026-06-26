import type { ReactNode } from 'react'

/**
 * Tiny, dependency-free Markdown renderer for short agent messages.
 * Handles: # / ## / ### headings, - / * / • bullets, 1. numbered lists,
 * **bold**, *italic*, `code`, and blank-line spacing. It never runs raw HTML,
 * so it is safe to render model output directly.
 */

function renderInline(text: string, keyBase: string): ReactNode[] {
  const out: ReactNode[] = []
  const re = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g
  let last = 0
  let i = 0
  let m: RegExpExecArray | null
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(text.slice(last, m.index))
    const tok = m[0]
    if (tok.startsWith('**')) {
      out.push(
        <strong key={`${keyBase}-b${i++}`} className="font-700 text-paper">
          {tok.slice(2, -2)}
        </strong>,
      )
    } else if (tok.startsWith('`')) {
      out.push(
        <code key={`${keyBase}-c${i++}`} className="rounded bg-surface-2 px-1 py-0.5 font-mono text-[0.85em] text-paper">
          {tok.slice(1, -1)}
        </code>,
      )
    } else {
      out.push(<em key={`${keyBase}-i${i++}`}>{tok.slice(1, -1)}</em>)
    }
    last = re.lastIndex
  }
  if (last < text.length) out.push(text.slice(last))
  return out
}

type Block =
  | { kind: 'h'; level: number; text: string }
  | { kind: 'ul'; items: string[] }
  | { kind: 'ol'; items: string[] }
  | { kind: 'p'; text: string }

function parseBlocks(src: string): Block[] {
  const lines = (src ?? '').replace(/\r\n/g, '\n').split('\n')
  const blocks: Block[] = []
  let para: string[] = []

  const flush = () => {
    if (para.length) {
      blocks.push({ kind: 'p', text: para.join(' ').trim() })
      para = []
    }
  }

  for (const raw of lines) {
    const line = raw.trim()
    if (line === '') {
      flush()
      continue
    }

    const h = /^(#{1,3})\s+(.*)$/.exec(line)
    if (h) {
      flush()
      blocks.push({ kind: 'h', level: h[1].length, text: h[2] })
      continue
    }

    const ul = /^[-*•]\s+(.*)$/.exec(line)
    if (ul) {
      flush()
      const prev = blocks[blocks.length - 1]
      if (prev && prev.kind === 'ul') prev.items.push(ul[1])
      else blocks.push({ kind: 'ul', items: [ul[1]] })
      continue
    }

    const ol = /^\d+[.)]\s+(.*)$/.exec(line)
    if (ol) {
      flush()
      const prev = blocks[blocks.length - 1]
      if (prev && prev.kind === 'ol') prev.items.push(ol[1])
      else blocks.push({ kind: 'ol', items: [ol[1]] })
      continue
    }

    para.push(line)
  }
  flush()
  return blocks
}

export function MarkdownLite({ text, className }: { text: string; className?: string }) {
  const blocks = parseBlocks(text)
  return (
    <div className={className ?? 'space-y-2 text-sm leading-relaxed text-paper'}>
      {blocks.map((b, i) => {
        if (b.kind === 'h') {
          return (
            <p key={i} className={`font-display font-700 tracking-tight text-paper ${b.level === 1 ? 'text-base' : 'text-sm'}`}>
              {renderInline(b.text, `h${i}`)}
            </p>
          )
        }
        if (b.kind === 'ul') {
          return (
            <ul key={i} className="space-y-1">
              {b.items.map((it, j) => (
                <li key={j} className="flex gap-2">
                  <span className="mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full bg-ember" />
                  <span>{renderInline(it, `ul${i}-${j}`)}</span>
                </li>
              ))}
            </ul>
          )
        }
        if (b.kind === 'ol') {
          return (
            <ol key={i} className="space-y-1">
              {b.items.map((it, j) => (
                <li key={j} className="flex gap-2">
                  <span className="shrink-0 font-mono text-xs font-700 text-ember">{j + 1}.</span>
                  <span>{renderInline(it, `ol${i}-${j}`)}</span>
                </li>
              ))}
            </ol>
          )
        }
        return <p key={i}>{renderInline(b.text, `p${i}`)}</p>
      })}
    </div>
  )
}
