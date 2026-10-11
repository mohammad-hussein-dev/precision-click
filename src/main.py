#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# kate: syntax python; hl 1; space-indent on; indent-width 4; tab-width 4;

"""Application entry point for PrecisionClick.

Initializes the Tkinter root window, centers it on the screen,
and starts the main event loop.
"""

import os
import sys
import tkinter as tk

# Ensure project root is in path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ui.main_window import MainWindow


def center_window(root: tk.Tk) -> None:
    """Centers the given Tkinter window on the primary monitor.

    Args:
        root: The Tkinter root window instance.
    """
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"+{x}+{y}")


def main() -> None:
    """Launches the PrecisionClick application."""
    root = tk.Tk()

    # Initialize UI Controller
    app = MainWindow(root)

    # Center window visually
    center_window(root)

    # Start Main Loop
    root.mainloop()


if __name__ == "__main__":
    main()
