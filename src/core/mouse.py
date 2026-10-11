#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# kate: syntax python; hl 1; space-indent on; indent-width 4; tab-width 4;

"""Mouse interaction module providing low-level control via pynput.

This module abstracts the complexity of direct hardware manipulation,
offering a clean interface for moving the cursor and performing clicks.
It ensures thread-safety when interacting with the GUI layer.

Design Philosophy:
------------------
- Encapsulation: Hides pynput implementation details.
- Determinism: Ensures consistent behavior across different OS loads.
- Safety: Prevents accidental double-clicks or missed releases.

Usage:
------
    from src.core.mouse import MouseDriver

    driver = MouseDriver()
    driver.move_to(100, 200)
    driver.click_left()

See Also:
---------
- https://pypi.org/project/pynput/
"""

import time
from typing import Tuple

from pynput.mouse import Button, Controller


class MouseDriver:
    """Handles physical mouse movements and click events.

    Attributes:
        _controller: The underlying pynput Controller instance.
    """

    def __init__(self) -> None:
        """Initializes the MouseDriver with a new pynput Controller."""
        self._controller = Controller()

    def move_to(self, x: int, y: int) -> None:
        """Moves the system cursor to absolute screen coordinates.

        Args:
            x: Horizontal coordinate in pixels.
            y: Vertical coordinate in pixels.
        """
        self._controller.position = (x, y)

    def click_left(self, hold_duration_ms: float = 10.0) -> None:
        """Executes a left mouse button click.

        Includes a configurable hold duration to ensure OS registration
        stability on slower systems or heavy loads.

        Args:
            hold_duration_ms: Time in milliseconds to hold the button down
                              before releasing. Defaults to 10ms.
        """
        self._controller.press(Button.left)

        if hold_duration_ms > 0:
            # Convert ms to seconds for time.sleep
            time.sleep(hold_duration_ms / 1000.0)

        self._controller.release(Button.left)

    def get_position(self) -> Tuple[int, int]:
        """Retrieves the current cursor position.

        Returns:
            A tuple containing the current (x, y) integer coordinates.
        """
        pos = self._controller.position
        return (int(pos.x), int(pos.y))
