import { Target } from 'lucide-react'
import type { Calibration } from '../types'
import { Chip } from './ui'

export function CalibrationBadge({ calibration }: { calibration?: Calibration }) {
  if (!calibration) return null

  let tone: 'teal' | 'amber' | 'coral' = 'teal'
  if (calibration.effective_factor > 1.25 || calibration.effective_factor < 0.8) tone = 'coral'
  else if (calibration.effective_factor > 1.1 || calibration.effective_factor < 0.9) tone = 'amber'

  const label =
    calibration.effective_factor === 1.0
      ? 'well calibrated'
      : `${calibration.tendency} (${calibration.effective_factor.toFixed(2)}x)`

  const detail = `Based on ${calibration.sample_size} past tasks. ${calibration.applied ? 'Factor applied to estimates.' : 'Sample size too small to apply.'
    }`

  return (
    <span title={detail}>
      <Chip tone={tone}>
        <Target className="mr-1 h-3 w-3 inline" />
        {label}
      </Chip>
    </span>
  )
}
