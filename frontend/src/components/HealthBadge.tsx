import { useQuery } from '@tanstack/react-query'
import { ClutchApi } from '../api'
import { cx } from '../lib/format'

/** Live backend reachability pill. Polls /healthz every 20s. */
export function HealthBadge() {
  const { data, isError, isLoading } = useQuery({
    queryKey: ['health'],
    queryFn: ClutchApi.health,
    refetchInterval: 20_000,
    retry: false,
  })

  const ok = !!data && !isError
  const tone = isLoading ? 'muted' : ok ? 'teal' : 'coral'
  const label = isLoading ? 'connecting' : ok ? 'online' : 'offline'

  return (
    <span
      className={cx(
        'chip',
        tone === 'teal' && 'border-teal/40 text-teal',
        tone === 'coral' && 'border-coral/40 text-coral',
        tone === 'muted' && 'border-line text-muted',
      )}
      title={ok ? 'Backend reachable' : 'Backend unreachable'}
    >
      <span
        className={cx(
          'inline-block h-1.5 w-1.5 rounded-full',
          tone === 'teal' && 'bg-teal',
          tone === 'coral' && 'bg-coral',
          tone === 'muted' && 'bg-muted',
          ok && 'animate-pulse',
        )}
      />
      api {label}
    </span>
  )
}
