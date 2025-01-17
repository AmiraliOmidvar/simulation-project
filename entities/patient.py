"""
Patient and PatientPriorityQueue Module

This module defines the Patient class and the PatientPriorityQueue class, which are essential
for managing patients within the hospital simulation. The Patient class represents individual
patients with their attributes, while the PatientPriorityQueue manages the ordering of patients
based on their priority (urgent or ordinary) using a heap-based priority queue.
"""

import heapq
from enum import Enum

from task_manager import task_queue
from utils.queue import Queue


class PatientType(Enum):
    """
    Enumeration for Patient Types.

    Defines the two types of patients in the simulation:
    - URGENT: Patients requiring immediate attention.
    - ORDINARY: Patients with standard care requirements.
    """
    URGENT = "urgent"
    ORDINARY = "ordinary"


class PatientSurgery(Enum):
    """
    Enumeration for Patient Surgery Types.

    Defines the three levels of surgery complexity:
    - SIMPLE: Basic surgical procedures.
    - MEDIUM: Procedures requiring moderate resources.
    - COMPLEX: Advanced surgical operations with high resource requirements.
    """
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class Patient:
    """
    Represents a single patient in the hospital simulation.

    Attributes:
        patient_id (int): Unique identifier for the patient.
        enter_time (int): Simulation time when the patient arrived.
        patient_type (PatientType): Type of the patient (URGENT or ORDINARY).
        patient_surgery (PatientSurgery): Complexity of the patient's surgery.
        has_heart_problem (bool): Indicates if the patient has heart-related issues.
        exit_time (int or None): Simulation time when the patient exited the system.
    """

    def __init__(
            self, patient_id, patient_type: PatientType, patient_surgery: PatientSurgery,
            has_heart_problem, enter_time: int
    ):
        """
        Initializes a new Patient instance.

        Args:
            patient_id (int): Unique identifier for the patient.
            patient_type (PatientType): Type of the patient (URGENT or ORDINARY).
            patient_surgery (PatientSurgery): Complexity of the patient's surgery.
            has_heart_problem (bool): Indicates if the patient has heart-related issues.
            enter_time (int): Simulation time when the patient arrived.
        """
        self.patient_id = patient_id
        self.patient_type = patient_type
        self.patient_surgery = patient_surgery
        self.has_heart_problem = has_heart_problem
        self.enter_time = enter_time
        self.exit_time = None  # To be set when the patient exits the system

    def __repr__(self):
        """
        Returns a string representation of the Patient instance.

        Returns:
            str: String representation including patient ID, type, and arrival time.
        """
        return (f"Patient(id={self.patient_id}, "
                f"type={self.patient_type.value}, "
                f"arrival={self.enter_time})")


class PatientPriorityQueue(Queue):
    """
    Priority Queue for Managing Patients Based on Priority.

    Inherits from the generic Queue class and overrides its methods to implement a
    priority-based ordering using a heap. Urgent patients have higher priority over
    ordinary patients.

    Attributes:
        _queue (list): Internal heap-based list storing patients with their priorities.
        _index (int): Counter to maintain the order of insertion for stability.
    """

    def __init__(self, name, state):
        """
        Initializes the PatientPriorityQueue.

        Args:
            name (str): Name of the queue (e.g., 'emergency_queue').
            state (SystemState): Reference to the current system state.
        """
        super().__init__(name, state)
        self._queue = []  # Override with a heap-based list for priority management
        self._index = 0   # Counter to ensure FIFO order for patients with the same priority

    def push(self, patient):
        """
        Adds a patient to the priority queue based on their priority.

        Urgent patients are given higher priority (lower numerical value) than ordinary patients.
        The insertion order is maintained for patients with the same priority.

        Args:
            patient (Patient): The patient to be added to the queue.
        """
        # Assign priority based on patient type: URGENT patients have higher priority (lower value)
        priority = 0 if patient.patient_type == PatientType.URGENT else 1
        # Use a tuple of (priority, index, patient) to ensure stability in ordering
        heapq.heappush(self._queue, (priority, self._index, patient))
        self._index += 1
        # Update analytics with the new queue size
        task_queue.append(
            {"task": "queue", "queue": self.name, "time": self.state.current_time, "size": len(self._queue)}
        )

    def pop(self):
        """
        Removes and returns the patient with the highest priority from the queue.

        Raises:
            IndexError: If the queue is empty when attempting to pop.

        Returns:
            Patient: The patient with the highest priority.
        """
        if self._queue:
            # Update analytics with the queue size before popping
            task_queue.append(
                {"task": "queue", "queue": self.name, "time": self.state.current_time, "size": len(self._queue)}
            )
            return heapq.heappop(self._queue)[-1]
        raise IndexError("pop from an empty priority queue")

    def peek(self):
        """
        Returns the patient with the highest priority without removing them from the queue.

        Returns:
            Patient or None: The patient with the highest priority, or None if the queue is empty.
        """
        if self._queue:
            return self._queue[0][-1]
        return None
