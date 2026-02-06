from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import tkinter as tk
from tkinter import ttk

from scheduling.fcfs import schedule_fcfs
from scheduling.models import Process, Segment, compute_metrics, validate_processes
from scheduling.priority_nonpreemptive import schedule_priority_nonpreemptive
from scheduling.priority_preemptive import schedule_priority_preemptive
from scheduling.round_robin import schedule_round_robin
from scheduling.sjf_nonpreemptive import schedule_sjf_nonpreemptive
from scheduling.srtf_preemptive import schedule_srtf_preemptive


def _format_timeline(segments: list[Segment]) -> str:
    return " ".join(f"[{s.start}-{s.end}:{s.pid}]" for s in segments)


class SchedulerApp(ttk.Frame):
    def __init__(self, master: tk.Misc):
        super().__init__(master)

        self._algorithms: list[tuple[str, str]] = [
            ("First-Come-First-Served (FCFS)", "fcfs"),
            ("Shortest-Job-Next/First (SJN/SJF)", "sjf"),
            ("Non-preemptive Priority", "prio_np"),
            ("Shortest Remaining Time First (SRTF)", "srtf"),
            ("Preemptive Priority", "prio_p"),
            ("Round Robin", "rr"),
        ]

        self.algo_var = tk.StringVar(value=self._algorithms[0][0])
        self.quantum_var = tk.StringVar(value="2")
        self.status_var = tk.StringVar(value="")
        self.avg_var = tk.StringVar(value="")
        self.timeline_var = tk.StringVar(value="")

        self.pid_var = tk.StringVar(value="")
        self.at_var = tk.StringVar(value="0")
        self.bt_var = tk.StringVar(value="1")
        self.pr_var = tk.StringVar(value="0")
        self._selected_iid: str | None = None

        self._build_ui()
        self._sync_quantum_state()
        self.status_var.set("Add processes below.")

    def _build_ui(self) -> None:
        controls = ttk.Frame(self)
        controls.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        controls.columnconfigure(1, weight=1)
        controls.columnconfigure(10, weight=1)

        ttk.Label(controls, text="Algorithm").grid(row=0, column=0, sticky="w")
        self.algo_cb = ttk.Combobox(
            controls,
            textvariable=self.algo_var,
            values=[a[0] for a in self._algorithms],
            state="readonly",
            width=48,
        )
        self.algo_cb.grid(row=0, column=1, sticky="ew", padx=(6, 14))
        self.algo_cb.bind("<<ComboboxSelected>>", lambda _evt: self._sync_quantum_state())

        ttk.Label(controls, text="Time Quantum").grid(row=0, column=2, sticky="w")
        self.quantum_entry = ttk.Entry(controls, textvariable=self.quantum_var, width=6)
        self.quantum_entry.grid(row=0, column=3, sticky="w", padx=(6, 14))

        ttk.Button(controls, text="Run", command=self._run).grid(row=0, column=4, sticky="w")

        entry_row = ttk.Frame(self)
        entry_row.grid(row=1, column=0, sticky="ew", padx=10)
        entry_row.columnconfigure(12, weight=1)

        ttk.Label(entry_row, text="Process ID").grid(row=0, column=0, sticky="w")
        ttk.Entry(entry_row, textvariable=self.pid_var, width=10).grid(row=0, column=1, sticky="w", padx=(6, 14))

        ttk.Label(entry_row, text="Arrival Time").grid(row=0, column=2, sticky="w")
        ttk.Entry(entry_row, textvariable=self.at_var, width=6).grid(row=0, column=3, sticky="w", padx=(6, 14))

        ttk.Label(entry_row, text="Processing Time").grid(row=0, column=4, sticky="w")
        ttk.Entry(entry_row, textvariable=self.bt_var, width=6).grid(row=0, column=5, sticky="w", padx=(6, 14))

        self.priority_label = ttk.Label(entry_row, text="Priority")
        self.priority_label.grid(row=0, column=6, sticky="w")
        self.priority_entry = ttk.Entry(entry_row, textvariable=self.pr_var, width=6)
        self.priority_entry.grid(row=0, column=7, sticky="w", padx=(6, 14))

        ttk.Button(entry_row, text="Add/Update", command=self._add_or_update_row).grid(row=0, column=8, sticky="w", padx=(0, 8))
        ttk.Button(entry_row, text="Delete", command=self._delete_selected).grid(row=0, column=9, sticky="w", padx=(0, 8))
        ttk.Button(entry_row, text="Clear", command=self._clear_processes).grid(row=0, column=10, sticky="w")

        self.status_label = ttk.Label(self, textvariable=self.status_var)
        self.status_label.grid(row=2, column=0, sticky="ew", padx=10, pady=(6, 0))

        table_frame = ttk.Frame(self)
        table_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
        self.rowconfigure(3, weight=1)
        self.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        columns = ("pid", "at", "bt", "pr", "ct", "tat", "wt")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        self.tree.grid(row=0, column=0, sticky="nsew")

        headings = {
            "pid": "Process ID",
            "at": "Arrival Time",
            "bt": "Processing Time",
            "pr": "Priority",
            "ct": "Completion Time",
            "tat": "Turnaround Time",
            "wt": "Waiting Time",
        }
        widths = {"pid": 110, "at": 110, "bt": 140, "pr": 90, "ct": 140, "tat": 150, "wt": 120}

        for c in columns:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c], anchor="center", stretch=True)

        self.tree.bind("<<TreeviewSelect>>", lambda _evt: self._on_row_select())

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        bottom = ttk.Frame(self)
        bottom.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 10))
        bottom.columnconfigure(0, weight=1)

        ttk.Label(bottom, textvariable=self.avg_var).grid(row=0, column=0, sticky="w")
        self.timeline_label = ttk.Label(bottom, textvariable=self.timeline_var, wraplength=980, justify="left")
        self.timeline_label.grid(row=1, column=0, sticky="ew", pady=(6, 0))

        def on_resize(_evt: tk.Event) -> None:
            # Keep the timeline text fully visible by wrapping to the available width.
            self.timeline_label.configure(wraplength=max(300, bottom.winfo_width() - 10))

        bottom.bind("<Configure>", on_resize)

    def _sync_quantum_state(self) -> None:
        is_rr = self.algo_var.get() == "Round Robin"
        self.quantum_entry.configure(state=("normal" if is_rr else "disabled"))

        is_priority = self.algo_var.get() in {"Non-preemptive Priority", "Preemptive Priority"}
        if is_priority:
            self.priority_label.grid()
            self.priority_entry.grid()
            self.priority_entry.configure(state="normal")
        else:
            self.pr_var.set("0")
            # Hide the priority input since it's not needed for other algorithms.
            self.priority_label.grid_remove()
            self.priority_entry.grid_remove()

    def _clear_process_entry(self) -> None:
        self.pid_var.set("")
        self.at_var.set("0")
        self.bt_var.set("1")
        self.pr_var.set("0")
        self._selected_iid = None

    def _clear_processes(self) -> None:
        self._clear_table()
        self._clear_process_entry()
        self.avg_var.set("")
        self.timeline_var.set("")

    def _on_row_select(self) -> None:
        selected = self.tree.selection()
        if not selected:
            self._selected_iid = None
            return

        iid = selected[0]
        vals = self.tree.item(iid, "values")
        if len(vals) < 4:
            return

        self._selected_iid = iid
        self.pid_var.set(str(vals[0]))
        self.at_var.set(str(vals[1]))
        self.bt_var.set(str(vals[2]))
        self.pr_var.set(str(vals[3]) if str(vals[3]).strip() != "" else "0")

    def _parse_int(self, label: str, raw: str, *, min_value: int | None = None) -> int:
        try:
            val = int(raw)
        except ValueError as e:
            raise ValueError(f"{label} must be an integer") from e
        if min_value is not None and val < min_value:
            raise ValueError(f"{label} must be >= {min_value}")
        return val

    def _add_or_update_row(self) -> None:
        self.status_var.set("")
        try:
            pid = self.pid_var.get().strip()
            if not pid:
                raise ValueError("PID is required")

            arrival = self._parse_int("Arrival Time", self.at_var.get().strip(), min_value=0)
            burst = self._parse_int("Processing Time", self.bt_var.get().strip(), min_value=1)

            if self.algo_var.get() in {"Non-preemptive Priority", "Preemptive Priority"}:
                priority = self._parse_int("Priority", self.pr_var.get().strip(), min_value=0)
            else:
                priority = 0

            # If the user didn't select a row, treat an existing PID as "edit that row"
            # instead of throwing a duplicate error.
            existing_iid_for_pid: str | None = None
            for iid in self.tree.get_children():
                vals = self.tree.item(iid, "values")
                if vals and str(vals[0]) == pid:
                    existing_iid_for_pid = iid
                    break

            target_iid = self._selected_iid
            if target_iid is None and existing_iid_for_pid is not None:
                target_iid = existing_iid_for_pid

            # If a row is selected, still prevent changing PID to another row's PID.
            if target_iid is not None and existing_iid_for_pid is not None and existing_iid_for_pid != target_iid:
                raise ValueError(f"Duplicate PID: {pid}")

            row_values = (pid, arrival, burst, priority, "", "", "")
            if target_iid is None:
                self.tree.insert("", "end", values=row_values)
            else:
                self.tree.item(target_iid, values=row_values)

            self._clear_process_entry()
            self.avg_var.set("")
            self.timeline_var.set("")
        except Exception as e:
            self.status_var.set(f"Error: {e}")

    def _delete_selected(self) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        for iid in selected:
            self.tree.delete(iid)
        self._clear_process_entry()
        self.avg_var.set("")
        self.timeline_var.set("")

    def _processes_from_table(self) -> list[Process]:
        processes: list[Process] = []
        for iid in self.tree.get_children():
            vals = self.tree.item(iid, "values")
            if not vals or len(vals) < 4:
                continue

            raw_priority = str(vals[3]).strip() if len(vals) > 3 else ""
            if raw_priority == "":
                priority_val = 0
            else:
                priority_val = int(raw_priority)

            processes.append(Process(pid=str(vals[0]), arrival=int(vals[1]), burst=int(vals[2]), priority=priority_val))

        validate_processes(processes)
        return processes

    def _schedule(self, processes: list[Process]) -> tuple[str, list[Segment]]:
        label = self.algo_var.get()
        key = next(k for (lbl, k) in self._algorithms if lbl == label)

        if key == "fcfs":
            return "First-Come-First-Served (FCFS)", schedule_fcfs(processes)
        if key == "sjf":
            return "Shortest-Job-Next/First (SJN/SJF)", schedule_sjf_nonpreemptive(processes)
        if key == "prio_np":
            return "Non-preemptive Priority", schedule_priority_nonpreemptive(processes)
        if key == "srtf":
            return "Shortest Remaining Time First (SRTF)", schedule_srtf_preemptive(processes)
        if key == "prio_p":
            return "Preemptive Priority", schedule_priority_preemptive(processes)
        if key == "rr":
            q = self._parse_int("Time Quantum", self.quantum_var.get().strip(), min_value=1)
            return f"Round Robin (q={q})", schedule_round_robin(processes, q)

        raise RuntimeError("Unknown algorithm")

    def _clear_table(self) -> None:
        for iid in self.tree.get_children():
            self.tree.delete(iid)

    def _run(self) -> None:
        self.status_var.set("")
        self.avg_var.set("")
        self.timeline_var.set("")

        # Clear computed columns only; keep user-entered processes
        for iid in self.tree.get_children():
            vals = list(self.tree.item(iid, "values"))
            if len(vals) >= 7:
                vals[4] = ""
                vals[5] = ""
                vals[6] = ""
                self.tree.item(iid, values=tuple(vals))

        try:
            processes = self._processes_from_table()

            title, segments = self._schedule(processes)
            metrics = compute_metrics(processes, segments)

            for iid in self.tree.get_children():
                vals = list(self.tree.item(iid, "values"))
                if not vals:
                    continue
                pid = str(vals[0])
                if pid not in metrics:
                    continue
                m = metrics[pid]
                while len(vals) < 7:
                    vals.append("")
                vals[4] = m.completion
                vals[5] = m.turnaround
                vals[6] = m.waiting
                self.tree.item(iid, values=tuple(vals))

            avg_wt = sum(m.waiting for m in metrics.values()) / len(metrics)
            avg_tat = sum(m.turnaround for m in metrics.values()) / len(metrics)

            self.status_var.set(title)
            self.avg_var.set(f"Averages: WT={avg_wt:.2f}, TAT={avg_tat:.2f}")
            self.timeline_var.set(f"Timeline: {_format_timeline(segments)}")

        except Exception as e:
            self.status_var.set(f"Error: {e}")


def main() -> None:
    root = tk.Tk()
    root.title("CPU Scheduling Simulator")
    root.geometry("1050x600")
    root.minsize(980, 520)

    app = SchedulerApp(root)
    app.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()
