"""Phase 9 feature #4 - estimate calibration loop.

Learn how this person's estimates compare to reality. For every completed
commitment that has both an estimate and a recorded actual time, we take the
ratio actual/estimate; the personal bias factor is the median of those ratios
(clamped to a sane range). Once there are enough samples the planner multiplies
every estimate by this factor, so projections self-correct over time.

Pure read - never writes. Defaults to an identity factor (1.0) when there is no
history, so behaviour is unchanged on a fresh install.
"""
from __future__ import annotations

from statistics import median

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commitment import Commitment, Status

# need a few data points before we trust (and apply) the learned factor
MIN_SAMPLES = 3
# never let one wild data point swing estimates more than 4x in either direction
_MIN_FACTOR = 0.25
_MAX_FACTOR = 4.0


async def get_calibration(db: AsyncSession, user_id: int) -> dict:
    result = await db.execute(
        select(Commitment).where(Commitment.status == Status.done, Commitment.user_id == user_id)
    )
    done = result.scalars().all()

    ratios: list[float] = []
    for c in done:
        if (
            c.actual_minutes
            and c.actual_minutes > 0
            and c.est_effort_minutes
            and c.est_effort_minutes > 0
        ):
            ratios.append(c.actual_minutes / c.est_effort_minutes)

    sample_size = len(ratios)
    raw = float(median(ratios)) if sample_size else 1.0
    factor = max(_MIN_FACTOR, min(raw, _MAX_FACTOR))
    applied = sample_size >= MIN_SAMPLES

    if not ratios:
        tendency = "unknown"
    elif factor > 1.1:
        tendency = "underestimating"   # tasks take longer than planned
    elif factor < 0.9:
        tendency = "overestimating"    # tasks finish faster than planned
    else:
        tendency = "well_calibrated"

    return {
        "factor": round(factor, 3),
        "sample_size": sample_size,
        "min_samples": MIN_SAMPLES,
        "applied": applied,
        "effective_factor": round(factor, 3) if applied else 1.0,
        "tendency": tendency,
    }
