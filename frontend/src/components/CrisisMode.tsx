import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import {
  BarVisualizer,
  LiveKitRoom,
  RoomAudioRenderer,
  VoiceAssistantControlBar,
  useRoomContext,
  useVoiceAssistant,
} from '@livekit/components-react'
import '@livekit/components-styles'
import { RoomEvent, type Participant, type TranscriptionSegment } from 'livekit-client'
import { Mic, PhoneOff, Radio } from 'lucide-react'
import { ApiError, ClutchApi, type VoiceToken } from '../api'
import { cx } from '../lib/format'
import { Button, Chip, ErrorNote, Panel, Spinner, type Tone } from './ui'

const STATE_META: Record<string, { tone: Tone; label: string }> = {
  disconnected: { tone: 'muted', label: 'Disconnected' },
  connecting: { tone: 'amber', label: 'Connecting' },
  initializing: { tone: 'amber', label: 'Warming up' },
  listening: { tone: 'teal', label: 'Listening' },
  thinking: { tone: 'iris', label: 'Thinking' },
  speaking: { tone: 'ember', label: 'Speaking' },
}

type Line = { id: string; text: string; from: 'you' | 'clutch'; at: number }

/** Subscribe to room transcriptions and keep them ordered by arrival. */
function useTranscript(): Line[] {
  const room = useRoomContext()
  const [byId, setById] = useState<Record<string, Line>>({})

  useEffect(() => {
    if (!room) return
    const onSeg = (segments: TranscriptionSegment[], participant?: Participant) => {
      const from: Line['from'] = participant?.isLocal ? 'you' : 'clutch'
      setById((prev) => {
        const next = { ...prev }
        for (const s of segments) {
          next[s.id] = { id: s.id, text: s.text, from, at: s.firstReceivedTime ?? Date.now() }
        }
        return next
      })
    }
    room.on(RoomEvent.TranscriptionReceived, onSeg)
    return () => {
      room.off(RoomEvent.TranscriptionReceived, onSeg)
    }
  }, [room])

  return Object.values(byId).sort((a, b) => a.at - b.at)
}

function Transcript({ lines }: { lines: Line[] }) {
  const endRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [lines.length])

  if (lines.length === 0) {
    return (
      <p className="text-sm text-faint">
        Say “Clutch, what do I do right now?” — the conversation will appear here.
      </p>
    )
  }
  return (
    <div className="flex max-h-64 flex-col gap-2 overflow-y-auto pr-1">
      {lines.map((l) => (
        <div key={l.id} className="flex flex-col">
          <span
            className={cx(
              'text-[10px] font-600 uppercase tracking-[0.18em]',
              l.from === 'you' ? 'text-faint' : 'text-ember',
            )}
          >
            {l.from === 'you' ? 'You' : 'Clutch'}
          </span>
          <span className="text-sm text-paper">{l.text}</span>
        </div>
      ))}
      <div ref={endRef} />
    </div>
  )
}

function VoiceSession({ onEnd }: { onEnd: () => void }) {
  const { state, audioTrack } = useVoiceAssistant()
  const lines = useTranscript()
  const meta = STATE_META[state] ?? STATE_META.disconnected

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <Chip tone={meta.tone}>{meta.label}</Chip>
        <Button variant="ghost" onClick={onEnd}>
          <PhoneOff className="h-4 w-4" /> End
        </Button>
      </div>

      <div className="grid h-24 place-items-center rounded-lg border border-line bg-ink-2/60 p-3">
        <BarVisualizer
          state={state}
          trackRef={audioTrack}
          barCount={7}
          className="h-full w-full"
        />
      </div>

      <Transcript lines={lines} />

      <div className="lk-controls rounded-lg border border-line bg-ink-2/40 p-2">
        <VoiceAssistantControlBar />
      </div>
    </div>
  )
}

/** Voice Crisis Mode: talk to Clutch hands-free over LiveKit + Gemini Live. */
export function CrisisMode() {
  const status = useQuery({ queryKey: ['voice-status'], queryFn: ClutchApi.voiceStatus })
  const [token, setToken] = useState<VoiceToken | null>(null)

  const connect = useMutation({
    mutationFn: () => ClutchApi.voiceToken(),
    onSuccess: (t) => setToken(t),
  })

  const voice = status.data?.voice
  const enabled = status.data?.enabled === true

  return (
    <Panel
      title="Voice Crisis Mode"
      rail="ember"
      icon={<Radio className="h-4 w-4 text-ember" />}
      actions={
        token ? (
          <Chip tone="ember">live</Chip>
        ) : voice ? (
          <Chip tone="muted">{voice}</Chip>
        ) : null
      }
    >
      {status.isLoading && (
        <div className="flex items-center gap-2 text-sm text-muted">
          <Spinner /> Checking voice availability…
        </div>
      )}

      {!status.isLoading && !enabled && (
        <ErrorNote>
          Voice Crisis Mode isn’t configured on the server yet. Set the LiveKit
          credentials and run the voice worker to enable hands-free triage.
        </ErrorNote>
      )}

      {!status.isLoading && enabled && !token && (
        <div className="flex flex-col gap-3">
          <p className="text-sm text-muted">
            Talk to Clutch hands-free. It listens, runs the same triage as the
            War Room, and tells you what to do next — out loud.
          </p>
          <div>
            <Button
              variant="ember"
              loading={connect.isPending}
              onClick={() => connect.mutate()}
            >
              <Mic className="h-4 w-4" /> Start voice session
            </Button>
          </div>
          {connect.isError && (
            <ErrorNote>
              {connect.error instanceof ApiError
                ? connect.error.detail
                : 'Could not start the voice session.'}
            </ErrorNote>
          )}
        </div>
      )}

      {token && (
        <LiveKitRoom
          serverUrl={token.url}
          token={token.token}
          connect
          audio
          video={false}
          data-lk-theme="default"
          onDisconnected={() => setToken(null)}
        >
          <VoiceSession onEnd={() => setToken(null)} />
          <RoomAudioRenderer />
        </LiveKitRoom>
      )}
    </Panel>
  )
}
