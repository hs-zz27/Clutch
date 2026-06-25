import { Link } from 'react-router-dom'
import { ArrowLeft, Sparkles } from 'lucide-react'
import { Shell } from '../components/Shell'
import { CrisisMode } from '../components/CrisisMode'
import { Panel } from '../components/ui'

const PROMPTS = [
  '“Clutch, what do I do right now?”',
  '“Am I going to make it? How bad is the deficit?”',
  '“What should I drop?”',
  '“Draft an extension message for the code review.”',
  '“What does the essay actually need to pass?”',
]

export default function Crisis() {
  return (
    <Shell>
      <div className="mx-auto flex max-w-3xl flex-col gap-6">
        <div className="flex flex-col gap-2">
          <Link
            to="/war-room"
            className="inline-flex w-fit items-center gap-1.5 text-sm text-muted hover:text-paper"
          >
            <ArrowLeft className="h-4 w-4" /> Back to War Room
          </Link>
          <h1 className="font-display text-3xl font-700 tracking-tight text-paper">
            Voice Crisis Mode
          </h1>
          <p className="max-w-xl text-muted">
            Hands-free triage for when you can’t even type. Tap the mic and talk
            — Clutch runs the same plan and sacrifice logic as the War Room and
            answers out loud.
          </p>
        </div>

        <CrisisMode />

        <Panel
          title="What you can ask"
          rail="iris"
          icon={<Sparkles className="h-4 w-4 text-iris" />}
        >
          <ul className="flex flex-col gap-1.5">
            {PROMPTS.map((p) => (
              <li key={p} className="text-sm text-paper">
                {p}
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-faint">
            Renegotiation messages are always prepared as drafts — Clutch never
            sends anything without your one-tap approval in the outbox.
          </p>
        </Panel>
      </div>
    </Shell>
  )
}
