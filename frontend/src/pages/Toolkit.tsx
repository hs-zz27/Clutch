import type { ReactNode } from 'react'
import { BookOpen, Mail } from 'lucide-react'
import { Shell } from '../components/Shell'
import { KnowledgePanel } from '../components/KnowledgePanel'
import { RenegotiationOutbox } from '../components/RenegotiationOutbox'

function SectionHead({ icon, title, hint }: { icon: ReactNode; title: string; hint: string }) {
  return (
    <div className="flex items-start gap-2.5">
      <span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-surface-2 text-ember">
        {icon}
      </span>
      <div>
        <h2 className="font-display text-base font-700 leading-tight tracking-tight text-paper">{title}</h2>
        <p className="text-xs text-muted">{hint}</p>
      </div>
    </div>
  )
}

export default function Toolkit() {
  return (
    <Shell>
      <div className="mx-auto flex max-w-5xl flex-col gap-7">
        <div className="flex flex-col gap-2">
          <h1 className="font-display text-3xl font-700 tracking-tight text-paper">Toolkit</h1>
          <p className="max-w-2xl text-muted">
            Your support tools, kept separate from the live triage board — ground the agent in your
            own documents, and draft the awkward “I need more time” emails without sweating the wording.
          </p>
        </div>

        <section className="flex flex-col gap-3">
          <SectionHead
            icon={<BookOpen className="h-4 w-4" />}
            title="Knowledge base"
            hint="Upload briefs, rubrics or specs, then ask questions about them. Answers are grounded only in what you uploaded (RAG) — it won't make things up."
          />
          <KnowledgePanel />
        </section>

        <section className="flex flex-col gap-3">
          <SectionHead
            icon={<Mail className="h-4 w-4" />}
            title="Renegotiation outbox"
            hint="Pick a commitment you can't finish in time and let Clutch draft an honest extension or scope-cut email. Edit it freely — nothing sends until you click Send."
          />
          <RenegotiationOutbox />
        </section>
      </div>
    </Shell>
  )
}
