from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence


@dataclass(frozen=True)
class Process:
    pid: str
    arrival: int
    burst: int
    priority: int = 0


@dataclass(frozen=True)
class Segment:
    """Represents an execution segment on the CPU timeline."""

    start: int
    end: int
    pid: str  # "IDLE" allowed


@dataclass(frozen=True)
class Metrics:
    completion: int
    turnaround: int
    waiting: int


def validate_processes(processes: Sequence[Process]) -> None:
    if not processes:
        raise ValueError("No processes provided.")
    seen = set()
    for p in processes:
        if p.pid in seen:
            raise ValueError(f"Duplicate PID: {p.pid}")
        seen.add(p.pid)
        if p.arrival < 0:
            raise ValueError(f"Arrival time must be >= 0 for {p.pid}")
        if p.burst <= 0:
            raise ValueError(f"Burst time must be > 0 for {p.pid}")
        if p.priority < 0:
            raise ValueError(f"Priority must be >= 0 for {p.pid}")


def merge_adjacent(segments: List[Segment]) -> List[Segment]:
    if not segments:
        return []
    merged: List[Segment] = [segments[0]]
    for seg in segments[1:]:
        last = merged[-1]
        if seg.pid == last.pid and seg.start == last.end:
            merged[-1] = Segment(start=last.start, end=seg.end, pid=last.pid)
        else:
            merged.append(seg)
    return merged


def compute_metrics(processes: Sequence[Process], segments: Sequence[Segment]) -> Dict[str, Metrics]:
    completion: Dict[str, int] = {}
    for seg in segments:
        if seg.pid == "IDLE":
            continue
        completion[seg.pid] = seg.end

    metrics: Dict[str, Metrics] = {}
    for p in processes:
        ct = completion.get(p.pid)
        if ct is None:
            raise RuntimeError(f"No completion time computed for {p.pid}")
        tat = ct - p.arrival
        wt = tat - p.burst
        metrics[p.pid] = Metrics(completion=ct, turnaround=tat, waiting=wt)
    return metrics
