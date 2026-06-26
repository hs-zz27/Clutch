import { useMemo, type ComponentType } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ArrowLeft, BookOpen, ChevronRight, FlaskConical, History, Mail, Users, Wrench } from 'lucide-react'
import { Shell } from '../components/Shell'
import { KnowledgePanel } from '../components/KnowledgePanel'
import { RenegotiationOutbox } from '../components/RenegotiationOutbox'
import { WhatIfPanel } from '../components/WhatIfPanel'
import { StakeholdersPanel } from '../components/StakeholdersPanel'
import { DecisionLedger } from '../components/DecisionLedger'

type Tool = {
  id: string
  name: string
  blurb: string
  icon: ComponentType<{ className?: string }>
  Panel: ComponentType
}

const TOOLS: Tool[] = [
  {
    id: 'whatif',
    name: 'What-if planner',
    blurb: 'See how your chances change if you drop or finish something — without touching real data.',
    icon: FlaskConical,
    Panel: WhatIfPanel,
  },
  {
    id: 'knowledge',
    name: 'Knowledge base',
    blurb: 'Upload your notes or briefs, then ask questions and get answers based only on them.',
    icon: BookOpen,
    Panel: KnowledgePanel,
  },
  {
    id: 'people',
    name: 'People & contacts',
    blurb: 'Keep track of who you answer to, so your emails strike the right tone.',
    icon: Users,
    Panel: StakeholdersPanel,
  },
  {
    id: 'emails',
    name: 'Extension emails',
    blurb: 'Let Clutch draft an honest “I need more time” email. Nothing sends until you press Send.',
    icon: Mail,
    Panel: RenegotiationOutbox,
  },
  {
    id: 'history',
    name: 'Decision history',
    blurb: 'A log of every choice you made — what you dropped or deferred — that you can undo.',
    icon: History,
    Panel: DecisionLedger,
  },
]

function ToolDetail({ tool, onBack }: { tool: Tool; onBack: () => void }) {
  const Icon = tool.icon
  const Panel = tool.Panel
  return (
    <div className="flex flex-col gap-4">
      <button
        onClick={onBack}
        className="inline-flex w-fit items-center gap-1.5 text-sm font-700 text-muted transition-colors hover:text-ember"
      >
        <ArrowLeft className="h-4 w-4" /> All tools
      </button>
      <div className="flex items-center gap-3">
        <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl border-2 border-line bg-surface-2 text-ember shadow-hard-sm">
          <Icon className="h-5 w-5" />
        </span>
        <div>
          <h2 className="font-display text-xl font-700 tracking-tight text-paper">{tool.name}</h2>
          <p className="text-sm text-muted">{tool.blurb}</p>
        </div>
      </div>
      <Panel />
    </div>
  )
}

export default function Toolkit() {
  const [params, setParams] = useSearchParams()
  const activeId = params.get('tool')
  const active = useMemo(() => TOOLS.find((t) => t.id === activeId) ?? null, [activeId])

  return (
    <Shell>
      <div className="mx-auto flex max-w-3xl flex-col gap-6">
        {/* header */}
        <header className="flex items-start gap-3">
          <span className="mt-0.5 grid h-11 w-11 shrink-0 place-items-center rounded-xl border-2 border-line bg-ember text-line shadow-hard-sm">
            <Wrench className="h-5 w-5" />
          </span>
          <div>
            <h1 className="font-display text-3xl font-700 tracking-tight text-paper">Toolkit</h1>
            <p className="max-w-xl text-sm text-muted">
              Extra helpers that sit beside the War Room. Open one at a time — your live plan stays
              exactly as it is.
            </p>
          </div>
        </header>

        {active ? (
          <ToolDetail tool={active} onBack={() => setParams({})} />
        ) : (
          <ul className="divide-y divide-line-soft overflow-hidden rounded-xl border-2 border-line bg-surface shadow-hard">
            {TOOLS.map((t) => {
              const Icon = t.icon
              return (
                <li key={t.id}>
                  <button
                    onClick={() => setParams({ tool: t.id })}
                    className="group flex w-full items-center gap-3.5 px-4 py-3.5 text-left transition-colors hover:bg-surface-2"
                  >
                    <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg border-2 border-line bg-surface-2 text-ember transition-colors group-hover:bg-ember group-hover:text-line">
                      <Icon className="h-4 w-4" />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block font-display text-sm font-700 text-paper">{t.name}</span>
                      <span className="block truncate text-xs text-muted">{t.blurb}</span>
                    </span>
                    <ChevronRight className="h-4 w-4 shrink-0 text-faint transition-transform group-hover:translate-x-0.5 group-hover:text-ember" />
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </Shell>
  )
}
