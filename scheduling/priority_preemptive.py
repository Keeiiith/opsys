from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from .models import Process, Segment, merge_adjacent, validate_processes


def schedule_priority_preemptive(processes: Sequence[Process]) -> List[Segment]:
    """Preemptive Priority scheduling (lower number => higher priority).

    Always runs the available process with the highest priority (lowest value).
    Preempts when a higher-priority process arrives.

    Tie-breakers: priority, arrival, PID.
    """

    validate_processes(processes)

    procs = sorted(processes, key=lambda p: (p.arrival, p.pid))
    remaining_time: Dict[str, int] = {p.pid: p.burst for p in procs}

    not_arrived = list(procs)
    ready: Dict[str, Process] = {}

    t = 0
    segments: List[Segment] = []

    def push_arrivals(up_to_time: int) -> None:
        nonlocal not_arrived
        while not_arrived and not_arrived[0].arrival <= up_to_time:
            p = not_arrived.pop(0)
            ready[p.pid] = p

    while ready or not_arrived:
        if not ready:
            next_t = not_arrived[0].arrival
            if t < next_t:
                segments.append(Segment(start=t, end=next_t, pid="IDLE"))
                t = next_t
            push_arrivals(t)
            continue

        chosen = min(ready.values(), key=lambda p: (p.priority, p.arrival, p.pid))

        time_to_finish = remaining_time[chosen.pid]
        next_arrival_time: Optional[int] = not_arrived[0].arrival if not_arrived else None

        if next_arrival_time is None:
            run_for = time_to_finish
        else:
            run_for = min(time_to_finish, max(0, next_arrival_time - t))
            if run_for == 0:
                push_arrivals(t)
                continue

        segments.append(Segment(start=t, end=t + run_for, pid=chosen.pid))
        t += run_for
        remaining_time[chosen.pid] -= run_for

        push_arrivals(t)

        if remaining_time[chosen.pid] == 0:
            del ready[chosen.pid]

    return merge_adjacent(segments)
