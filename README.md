# CPU Scheduling Simulator (Python)

A CPU scheduling simulator with a **Tkinter GUI**. Enter processes manually, choose an algorithm from a dropdown, then view the computed results in a table.

## Run (recommended: virtual environment)

### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py scheduler_sim.py
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python scheduler_sim.py
```

## How to use the GUI

1. Select an **Algorithm**.
2. Enter a process in the input fields:
	- **Process ID** (example: `P1`)
	- **Arrival Time** (integer, must be >= 0)
	- **Processing Time** (integer, must be >= 1)
	- **Priority** (only used for Priority algorithms; lower number = higher priority)
3. Click **Add/Update** to add the process to the table.
4. Repeat for all processes.
5. If you choose **Round Robin**, enter **Time Quantum**.
6. Click **Run**.

The table will fill in:

- **Completion Time**, **Turnaround Time**, **Waiting Time**

## Algorithms included

- First-Come-First-Served (FCFS)
- Shortest-Job-Next/First (SJN/SJF)
- Non-preemptive Priority
- Shortest Remaining Time First (SRTF)
- Preemptive Priority
- Round Robin

## Troubleshooting

### Windows: “Python was not found… Microsoft Store”

If running `python scheduler_sim.py` opens the Microsoft Store, use the Python Launcher:

```powershell
py scheduler_sim.py
```

Or disable the Store alias:

- Settings → Apps → Advanced app settings → App execution aliases
- Turn off `python.exe` and `python3.exe`

## Project structure

- [scheduler_sim.py](scheduler_sim.py): entrypoint (launches GUI)
- [scheduler_gui.py](scheduler_gui.py): Tkinter UI
- [scheduling/](scheduling/): algorithms + models
