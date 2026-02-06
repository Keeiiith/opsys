"""CPU Scheduling Simulation (GUI entrypoint).

Launches the Tkinter GUI.
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True


def main() -> None:
    from scheduler_gui import main as gui_main

    gui_main()


if __name__ == "__main__":
    main()
