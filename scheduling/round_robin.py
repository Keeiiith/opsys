from __future__ import annotations

from typing import Dict, List, Sequence

from .models import Process, Segment, merge_adjacent, validate_processes


def schedule_round_robin(processes: Sequence[Process], quantum: int) -> List[Segment]:
    """Round Robin with a fixed time quantum (FIFO ready queue)."""
    validate_processes(processes)
    if quantum <= 0:
        raise ValueError("Quantum must be > 0")

    procs = sorted(processes, key=lambda p: (p.arrival, p.pid))
    remaining: Dict[str, int] = {p.pid: p.burst for p in procs}

    t = 0
    idx = 0
    queue: List[str] = []
    segments: List[Segment] = []

    def enqueue_arrivals() -> None:
        nonlocal idx
        while idx < len(procs) and procs[idx].arrival <= t:
            queue.append(procs[idx].pid)
            idx += 1

    enqueue_arrivals()

    while queue or idx < len(procs):
        if not queue:
            next_t = procs[idx].arrival
            if t < next_t:
                segments.append(Segment(start=t, end=next_t, pid="IDLE"))
                t = next_t
            enqueue_arrivals()
            continue

        pid = queue.pop(0)
        run_for = min(quantum, remaining[pid])
        segments.append(Segment(start=t, end=t + run_for, pid=pid))
        t += run_for
        remaining[pid] -= run_for

        enqueue_arrivals()

        if remaining[pid] > 0:
            queue.append(pid)

    return merge_adjacent(segments)
