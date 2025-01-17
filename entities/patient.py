import heapq
from enum import Enum

from task_manager import task_queue
from utils.queue import Queue


class PatientType(Enum):
    URGENT = "urgent"
    ORDINARY = "ordinary"


class PatientSurgery(Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class Patient:
    """
    Represents a single patient.

    Attributes:
    - patient_id: unique identifier
    - enter_time: simulation time the patient arrived
    - patient_type: "ordinary" or "urgent"
    - other fields as needed (e.g. group_id, severity, etc.)
    """

    def __init__(
            self, patient_id, patient_type: PatientType, patient_surgery: PatientSurgery,
            has_heart_problem, enter_time: int
    ):
        self.patient_id = patient_id
        self.patient_type = patient_type
        self.patient_surgery = patient_surgery
        self.has_heart_problem = has_heart_problem
        self.enter_time = enter_time
        self.exit_time = None

    def __repr__(self):
        return (f"Patient(id={self.patient_id}, "
                f"type={self.patient_type}, "
                f"arrival={self.enter_time})")


class PatientPriorityQueue(Queue):
    def __init__(self, name, state):
        super().__init__(name, state)
        self._queue = []  # Override with a heap-based list for priority management

    def push(self, patient):
        # Assign priority based on patient type: URGENT patients have higher priority (lower value)
        priority = 0 if patient.patient_type == PatientType.URGENT else 1
        # Use a tuple of (priority, index, patient) to ensure stability
        heapq.heappush(self._queue, (priority, self._index, patient))
        self._index += 1
        task_queue.append(
            {"task": "queue", "queue": self.name, "time": self.state.current_time, "size": len(self._queue)}
        )

    def pop(self):
        # Pop the patient with the highest priority (lowest value of priority)
        if self._queue:
            task_queue.append(
                {"task": "queue", "queue": self.name, "time": self.state.current_time, "size": len(self._queue)}
            )
            return heapq.heappop(self._queue)[-1]
        raise IndexError("pop from an empty priority queue")

    def peek(self):
        # Peek at the patient with the highest priority without removing it
        if self._queue:
            return self._queue[0][-1]
        return None
