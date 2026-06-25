import datetime
from app.models.commitment import Commitment, Status

def remaining_minutes(commitment: Commitment) -> float:
    total_time = commitment.est_effort_minutes
    completed = (total_time * commitment.progress_pct / 100.0)
    return total_time - completed

def build_plan(commitments: list[Commitment], now: datetime.datetime) -> dict:
    filtered_commitments = [
        c for c in commitments
        if c.status in (Status.not_started, Status.in_progress)
    ]
    
    filtered_commitments.sort(key=lambda c: (c.deadline, -c.importance))
    
    clock = now
    schedule = []
    total_deficit_minutes = 0.0
    
    for c in filtered_commitments:
        rem_mins = remaining_minutes(c)
        if rem_mins <= 0:
            continue
            
        projected_finish = clock + datetime.timedelta(minutes=rem_mins)
        latest_start = c.deadline - datetime.timedelta(minutes=rem_mins)
        
        late_minutes = 0.0
        if projected_finish > c.deadline:
            late_minutes = (projected_finish - c.deadline).total_seconds() / 60.0
            
        if late_minutes > 0:
            risk = "deficit"
        elif latest_start <= now:
            risk = "at_risk"
        else:
            risk = "on_track"
            
        schedule.append({
            "id": c.id,
            "title": c.title,
            "importance": c.importance,
            "deadline": c.deadline,
            "remaining_minutes": rem_mins,
            "projected_finish": projected_finish,
            "latest_start": latest_start,
            "late_minutes": late_minutes,
            "risk": risk,
        })
        
        total_deficit_minutes += late_minutes
        clock = projected_finish
        
    return {
        "now": now,
        "schedule": schedule,
        "total_deficit_minutes": total_deficit_minutes,
        "feasible": total_deficit_minutes == 0,
    }

