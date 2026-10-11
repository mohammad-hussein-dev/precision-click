#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# kate: syntax python; hl 1; space-indent on; indent-width 4; tab-width 4;

"""Tkinter-based Graphical User Interface for PrecisionClick.

Provides input fields for configuration, real-time activity logging,
and hotkey bindings for seamless user experience. Implements thread-safe
updates from the background engine to the main UI thread.

Design Philosophy:
------------------
- Responsiveness: UI never freezes during long operations.
- Clarity: Visual hierarchy guides the user naturally.
- Feedback: Immediate confirmation of every action.

Usage:
------
    import tkinter as tk
    from src.ui.main_window import MainWindow
    
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()
"""

import tkinter as tk
from tkinter import ttk
import threading
import datetime
from typing import Optional

from src.core.engine import PrecisionEngine


class MainWindow:
    """Main application controller managing view and interaction logic.

    Attributes:
        root: The primary Tkinter root window.
        engine: The backend PrecisionEngine instance.
        worker_thread: Reference to the background execution thread.
    """

    def __init__(self, root: tk.Tk) -> None:
        """Initializes the UI components and binds event handlers.

        Args:
            root: The parent Tkinter root window.
        """
        self.root = root
        self.engine = PrecisionEngine()
        self.worker_thread: Optional[threading.Thread] = None
        
        self._setup_ui()
        self._bind_hotkeys()
        self._log_info("System initialized. Ready for configuration.")

    def _setup_ui(self) -> None:
        """Constructs the visual layout using standard Tkinter widgets."""
        self.root.title("PrecisionClick v1.0")
        self.root.geometry("500x650")
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f0f0")

        # --- Header Section ---
        header_frame = ttk.Frame(self.root, padding=(10, 5))
        header_frame.pack(fill="x")
        
        ttk.Label(
            header_frame, 
            text="PrecisionClick", 
            font=("Segoe UI", 16, "bold")
        ).pack(anchor="w")
        
        ttk.Label(
            header_frame, 
            text="High-Precision Automation Tool", 
            foreground="#666"
        ).pack(anchor="w")

        # --- Configuration Panel ---
        config_frame = ttk.LabelFrame(
            self.root, 
            text="Configuration", 
            padding=(15, 10)
        )
        config_frame.pack(fill="x", padx=10, pady=5)

        # Coordinates Row
        coord_row = ttk.Frame(config_frame)
        coord_row.pack(fill="x", pady=2)
        
        ttk.Label(coord_row, text="X:").grid(row=0, column=0, sticky="e", padx=(0, 5))
        self.entry_x = ttk.Entry(coord_row, width=10)
        self.entry_x.grid(row=0, column=1, sticky="w")
        
        ttk.Label(coord_row, text="Y:").grid(row=0, column=2, sticky="e", padx=(10, 5))
        self.entry_y = ttk.Entry(coord_row, width=10)
        self.entry_y.grid(row=0, column=3, sticky="w")
        
        btn_pos = ttk.Button(
            coord_row, 
            text="Capture Pos", 
            command=self._capture_position, 
            width=12
        )
        btn_pos.grid(row=0, column=4, padx=(10, 0), sticky="e")

        # Timing Row
        time_row = ttk.Frame(config_frame)
        time_row.pack(fill="x", pady=5)
        
        ttk.Label(time_row, text="Start Time (HH:MM:SS.ms):").grid(
            row=0, column=0, sticky="w"
        )
        self.entry_time = ttk.Entry(time_row, width=20)
        
        # Default to current time + 5 seconds for convenience
        future_time = datetime.datetime.now() + datetime.timedelta(seconds=5)
        default_time_str = future_time.strftime("%H:%M:%S.") + f"{future_time.microsecond // 1000:03d}"
        self.entry_time.insert(0, default_time_str)
        self.entry_time.grid(row=0, column=1, sticky="w", padx=(10, 0))

        # Counts Row
        count_row = ttk.Frame(config_frame)
        count_row.pack(fill="x", pady=5)
        
        ttk.Label(count_row, text="Total Clicks:").grid(row=0, column=0, sticky="w")
        self.entry_clicks = ttk.Spinbox(count_row, from_=1, to=100000, width=10)
        self.entry_clicks.set(10)
        self.entry_clicks.grid(row=0, column=1, sticky="w", padx=(10, 0))

        ttk.Label(count_row, text="Interval (ms):").grid(
            row=0, column=2, sticky="e", padx=(20, 5)
        )
        self.entry_interval = ttk.Spinbox(count_row, from_=1, to=10000, width=10)
        self.entry_interval.set(100)
        self.entry_interval.grid(row=0, column=3, sticky="w")

        # --- Control Buttons ---
        ctrl_frame = ttk.Frame(self.root, padding=(10, 5))
        ctrl_frame.pack(fill="x")
        
        self.btn_start = ttk.Button(
            ctrl_frame, 
            text="▶ Start (F9)", 
            command=self._start_process
        )
        self.btn_start.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        self.btn_stop = ttk.Button(
            ctrl_frame, 
            text="■ Stop (F10)", 
            command=self._stop_process, 
            state="disabled"
        )
        self.btn_stop.pack(side="right", expand=True, fill="x", padx=(5, 0))

        # --- Activity Log Console ---
        log_frame = ttk.LabelFrame(
            self.root, 
            text="Activity Log", 
            padding=(5, 5)
        )
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.text_log = tk.Text(
            log_frame, 
            height=15, 
            wrap="word", 
            bg="#ffffff", 
            relief="sunken"
        )
        scrollbar = ttk.Scrollbar(
            log_frame, 
            orient="vertical", 
            command=self.text_log.yview
        )
        self.text_log.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.text_log.pack(side="left", fill="both", expand=True)

    def _bind_hotkeys(self) -> None:
        """Registers global keyboard shortcuts for quick control."""
        self.root.bind('<F9>', lambda e: self._start_process())
        self.root.bind('<F10>', lambda e: self._stop_process())

    def _capture_position(self) -> None:
        """Updates X/Y entries with current mouse coordinates."""
        from pynput.mouse import Controller
        pos = Controller().position
        
        self.entry_x.delete(0, tk.END)
        self.entry_x.insert(0, str(int(pos.x)))
        
        self.entry_y.delete(0, tk.END)
        self.entry_y.insert(0, str(int(pos.y)))
        
        self._log_info(f"Position captured: ({pos.x}, {pos.y})")

    def _log_info(self, message: str) -> None:
        """Writes a timestamped informational message to the log console.

        Args:
            message: The string content to display.
        """
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        formatted_msg = f"[{timestamp}] INFO: {message}\n"
        
        self.text_log.insert(tk.END, formatted_msg)
        self.text_log.see(tk.END)

    def _log_success(self, message: str) -> None:
        """Writes a timestamped success message to the log console."""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        formatted_msg = f"[{timestamp}] SUCCESS: {message}\n"
        
        self.text_log.insert(tk.END, formatted_msg)
        # Simple tag coloring for visual distinction
        self.text_log.tag_add("success_tag", f"{len(formatted_msg)-1}c-{len(formatted_msg)}c", "end")
        self.text_log.tag_config("success_tag", foreground="green")
        self.text_log.see(tk.END)

    def _on_click_event(self, index: int, time_obj: datetime.datetime) -> None:
        """Callback handler invoked by the engine upon each click.

        Ensures UI updates occur on the main thread to prevent race conditions.

        Args:
            index: The sequential number of the click performed.
            time_obj: The precise datetime when the click occurred.
        """
        msg = f"Click #{index} executed at {time_obj.strftime('%H:%M:%S.%f')[:-3]}"
        # Schedule update on main thread
        self.root.after(0, lambda: self._log_success(msg))

    def _start_process(self) -> None:
        """Validates inputs and launches the background execution thread."""
        if self.worker_thread and self.worker_thread.is_alive():
            self._log_info("Warning: Process already running.")
            return

        try:
            x = int(float(self.entry_x.get()))
            y = int(float(self.entry_y.get()))
            clicks = int(self.entry_clicks.get())
            interval = float(self.entry_interval.get())
            start_time_str = self.entry_time.get()
            
            self._log_info(
                f"Starting Sequence... Target: {start_time_str}, "
                f"Clicks: {clicks}, Interval: {interval}ms"
            )
            
            self.btn_start.config(state="disabled")
            self.btn_stop.config(state="normal")
            
            # Reset engine state
            self.engine.stop() 
            self.engine._stop_event.clear()
            self.engine._pause_event.clear()
            self.engine._is_active = True

            # Launch worker thread
            self.worker_thread = threading.Thread(
                target=self.engine.execute_sequence,
                args=(start_time_str, clicks, interval, x, y, self._on_click_event),
                daemon=True
            )
            self.worker_thread.start()

        except ValueError as ve:
            self._log_info(f"Input Error: {ve}")
        except Exception as e:
            self._log_info(f"Unexpected Error: {e}")

    def _stop_process(self) -> None:
        """Halts the running sequence and resets UI controls."""
        self._log_info("Stopping process...")
        self.engine.stop()
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
