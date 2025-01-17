from collections import deque
from typing import Deque, Dict, Any

# =============================================================================
# Task Manager Module
# =============================================================================

"""
task_manager.py

This module provides a shared task queue used for communication between different
components of the simulation system. The task queue is primarily used to notify
the AnalyticsData component of changes in queue sizes and bed occupancies within
the system.

Attributes:
    task_queue (Deque[Dict[str, Any]]): A double-ended queue that stores tasks as
        dictionaries. Each task represents an event or state change that needs to be
        recorded for analytics purposes.
"""

# Shared task queue for notifying analytics of simulation queue size changes
# Each task is represented as a dictionary with keys such as:
# - "task": Type of task (e.g., "queue", "section")
# - "queue" or "section": Name of the queue or section affected
# - "time": Simulation time when the event occurred
# - "size" or "number": New size of the queue or number of occupied beds
task_queue: Deque[Dict[str, Any]] = deque()
