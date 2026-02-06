from __future__ import annotations

from typing import Dict, List, Sequence

from .models import Process, Segment, merge_adjacent, validate_processes


def schedule_sjf_nonpreemptive(processes: Sequence[Process]) -> List[Segment]:
    """Non-preemptive SJF.

    When CPU is free, run the available job with the smallest burst.
    Tie-breakers: burst, arrival, PID.
    """
    validate_processes(processes)

    remaining: Dict[str, Process] = {p.pid: p for p in processes}
    t = 0
    segments: List[Segment] = []

    while remaining:
        available = [p for p in remaining.values() if p.arrival <= t]
        if not available:
            next_arrival = min(p.arrival for p in remaining.values())
            if t < next_arrival:
                segments.append(Segment(start=t, end=next_arrival, pid="IDLE"))
                t = next_arrival
            continue

        chosen = min(available, key=lambda p: (p.burst, p.arrival, p.pid))
        segments.append(Segment(start=t, end=t + chosen.burst, pid=chosen.pid))
        t += chosen.burst
        del remaining[chosen.pid]

    return merge_adjacent(segments)
