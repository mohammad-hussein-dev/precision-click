#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# kate: syntax python; hl 1; space-indent on; indent-width 4; tab-width 4;

"""High-precision timing engine for scheduled automation tasks.

Implements a hybrid sleeping strategy combining coarse-grained OS sleeps
(for CPU efficiency) and fine-grained busy-waiting (for millisecond accuracy).
Decoupled from UI logic to allow headless testing and reuse.

Design Philosophy:
------------------
- Separation of Concerns: Logic is independent of View.
- Resource Efficiency: Minimizes CPU usage during long waits.
- Precision: Achieves sub-millisecond timing where possible.

Usage:
------
    from src.core.engine import PrecisionEngine

    engine = PrecisionEngine()
    # Execute sequence in background thread
    engine.execute_sequence(...)

References:
-----------
- Windows Timer Resolution API concepts.
- Busy-Wait vs Sleep trade-offs.
"""

import datetime
import time
from threading import Event
from typing import Callable

from src.core.mouse import MouseDriver


class PrecisionEngine:
    """Orchestrates timed execution sequences with sub-millisecond precision.

    Attributes:
        _stop_event: Signal to terminate the sequence immediately.
        _pause_event: Signal to suspend execution temporarily.
        _is_active: Boolean flag indicating current operational state.
        _mouse_driver: Instance of MouseDriver for executing actions.
    """

    def __init__(self) -> None:
        """Initializes the engine with neutral states and a mouse driver."""
        self._stop_event = Event()
        self._pause_event = Event()
        self._is_active = False
        self._mouse_driver = MouseDriver()

    def stop(self) -> None:
        """Signals immediate termination of any active sequence.

        Sets the internal stop flag which breaks execution loops safely.
        """
        self._stop_event.set()
        self._is_active = False

    def pause(self) -> None:
        """Pauses execution without losing progress state.

        The engine will enter a low-power wait loop until resumed.
        """
        self._pause_event.set()

    def resume(self) -> None:
        """Resumes a previously paused execution sequence."""
        self._pause_event.clear()

    def is_paused(self) -> bool:
        """Checks if the engine is currently in a paused state.

        Returns:
            True if paused, False otherwise.
        """
        return self._pause_event.is_set()

    def _wait_until_precision(self, target_time: datetime.datetime) -> bool:
        """Internal helper for high-precision waiting.

        Uses a hybrid approach:
        1. Coarse sleep for intervals > 2ms to save CPU cycles.
        2. Busy-wait spin-loop for final < 2ms to guarantee timing accuracy.

        Args:
            target_time: The exact datetime object to wait for.

        Returns:
            True if target time was reached successfully.
            False if interrupted by a stop signal.
        """
        while self._is_active and not self._stop_event.is_set():
            if self._pause_event.is_set():
                time.sleep(0.1)  # Low-frequency check while paused
                continue

            now = datetime.datetime.now()
            delta = target_time - now

            if delta.total_seconds() <= 0:
                return True  # Target reached

            total_ms = delta.total_seconds() * 1000

            if total_ms > 2.0:
                # Sleep for bulk time, leaving 1ms buffer for spin
                sleep_sec = (total_ms - 1.0) / 1000.0
                time.sleep(sleep_sec)
            else:
                # Busy wait for critical precision window (< 2ms)
                pass

        return False

    def execute_sequence(
        self,
        start_time_str: str,
        total_clicks: int,
        interval_ms: float,
        x: int,
        y: int,
        on_click_callback: Callable[[int, datetime.datetime], None],
    ) -> None:
        """Executes the full automated clicking routine.

        Parses the start time, waits for synchronization, and performs
        the specified number of clicks at defined intervals.

        Args:
            start_time_str: Start time formatted as 'HH:MM:SS.mmm'.
            total_clicks: Number of iterations to perform. Must be > 0.
            interval_ms: Delay between consecutive clicks in milliseconds.
            x: Target horizontal coordinate.
            y: Target vertical coordinate.
            on_click_callback: Function invoked after each successful click
                               with arguments (click_index, timestamp).

        Raises:
            ValueError: If input parameters are invalid (e.g., negative counts).
        """
        try:
            # Input Validation
            if total_clicks <= 0:
                raise ValueError("Total clicks must be greater than zero.")
            if interval_ms < 0:
                raise ValueError("Interval cannot be negative.")

            today = datetime.date.today()
            parts = start_time_str.strip().split(":")

            if len(parts) != 3:
                raise ValueError("Time format must be HH:MM:SS.mmm")

            h, m = int(parts[0]), int(parts[1])
            s_parts = parts[2].split(".")
            s = int(s_parts[0])
            ms = int(s_parts[1][:3]) if len(s_parts) > 1 else 0

            target_dt = datetime.datetime.combine(
                today, datetime.time(h, m, s)
            ) + datetime.timedelta(milliseconds=ms)

            # Handle past times by starting immediately
            if datetime.datetime.now() > target_dt:
                target_dt = datetime.datetime.now()

            self._is_active = True
            success = self._wait_until_precision(target_dt)

            if not success:
                return  # Interrupted during wait phase

            for i in range(total_clicks):
                if self._stop_event.is_set():
                    break

                # Handle pause state within loop
                while self._pause_event.is_set() and not self._stop_event.is_set():
                    time.sleep(0.1)

                if self._stop_event.is_set():
                    break

                # Execute Action
                self._mouse_driver.move_to(x, y)
                self._mouse_driver.click_left()

                # Notify Observer (UI/Logger)
                on_click_callback(i + 1, datetime.datetime.now())

                # Interval Wait (skip after last click)
                if i < total_clicks - 1:
                    time.sleep(interval_ms / 1000.0)

        except Exception as e:
            print(f"Critical Engine Error: {e}")
            raise
        finally:
            self._is_active = False
