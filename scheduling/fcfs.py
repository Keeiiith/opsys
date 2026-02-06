from __future__ import annotations

from typing import List, Sequence

from .models import Process, Segment, merge_adjacent, validate_processes


def schedule_fcfs(processes: Sequence[Process]) -> List[Segment]:
    """FCFS (First-Come, First-Served), ties by arrival then PID."""
    validate_processes(processes)
    procs = sorted(processes, key=lambda p: (p.arrival, p.pid))
    t = 0
    segments: List[Segment] = []
    for p in procs:
        if t < p.arrival:
            segments.append(Segment(start=t, end=p.arrival, pid="IDLE"))
            t = p.arrival
        segments.append(Segment(start=t, end=t + p.burst, pid=p.pid))
        t += p.burst
    return merge_adjacent(segments)
