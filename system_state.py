from typing import List

from entities.patient import Patient, PatientPriorityQueue
from task_manager import task_queue
from utils.queue import Queue


class SystemState:
    """
    Holds all global simulation variables at time t:

    - current_time (the simulation clock)
    - LEQ(t): the length of the ER queue
    - NBAG(t): number of beds allocated in the general ward (if applicable)
    - NBAOR(t): number of beds allocated in the OR
    - NBAE(t): number of beds allocated in the ER
    - NBAL(t): number of beds allocated in the lab
    - NBAICU(t): number of beds allocated in ICU
    - NBACCU(t): number of beds allocated in CCU
    - NBAPOR(t): number of beds allocated in Pre-op
    - P(t): power status at time t (1 = power on, 0 = power off)

    Additionally, store the maximum capacities for each ward/section
    (e.g., capacity_ER, capacity_pre_or, etc.).
    """

    def __init__(self):
        self.current_time = 0.0

        self.lab_queue: PatientPriorityQueue = PatientPriorityQueue("lab", self)  # lab_queue
        self.emergency_queue: PatientPriorityQueue = PatientPriorityQueue("emergency", self)  # ambulance beds
        self.or_queue: PatientPriorityQueue = PatientPriorityQueue("or", self)  # operation room queue

        self.ccu_queue: Queue = Queue("ccu", self)  # CCU queue
        self.icu_queue: Queue = Queue("icu", self)  # ICU queue
        self.general_queue: Queue = Queue("general", self)  # General queue

        self.ccu_patients: List[Patient] = []  # Patients that are in the ccu rooms
        self.icu_patients: List[Patient] = []  # Patients that are in the icu rooms

        self.num_occupied_beds_general = NumOccupied("general", self)
        self.num_occupied_beds_or = NumOccupied("or", self)
        self.num_occupied_beds_emergency = NumOccupied("emergency", self)
        self.num_occupied_beds_lab = NumOccupied("lab", self)
        self.num_occupied_beds_icu = NumOccupied("icu", self)
        self.num_occupied_beds_ccu = NumOccupied("ccu", self)
        self.num_occupied_beds_pre_or = NumOccupied("pre_or", self)

        # Power status: 1 = on, 0 = off
        self.power_status = 1

        # Capacities (for example)
        self.CAPACITY_ER = 10  # Max # of ER beds
        self.CAPACITY_PRE_OR = 25  # Max # of Pre-op beds
        self.CAPACITY_OR = 50
        self.CAPACITY_GENERAL = 40  # Max # of general beds
        self.CAPACITY_LAB = 3  # Max # of lab beds
        self.CAPACITY_ICU = 10  # Max # of icu beds
        self.CAPACITY_CCU = 5  # Max # of ccu beds
        self.CAPACITY_AMBULANCE = 10  # Max # of AMBULANCE beds


class NumOccupied:
    def __init__(self, name: str, state: SystemState):
        """
        Represents the number of occupied beds for a ward/section.
        :param name: The name of the ward/section.
        """
        self._value = 0
        self.name = name
        self.state = state

    def _trigger_hook(self):
        """Call the hook with the current value."""
        task = {"task": "section", "section": self.name, "time": self.state.current_time, "number": self._value}
        task_queue.append(task)

    def __iadd__(self, other: int):
        """Handle `+=` operator."""
        self._value += other
        self._trigger_hook()
        return self

    def __isub__(self, other: int):
        """Handle `-=` operator."""
        self._value -= other
        self._trigger_hook()
        return self

    def __int__(self):
        """Return the integer value."""
        return self._value

    def __repr__(self):
        """String representation for debugging."""
        return f"{self._value}"

    def __eq__(self, other: int):
        return self._value == other

    def __ne__(self, other: int):
        return self._value != other

    def __lt__(self, other: int):
        return self._value < other

    def __le__(self, other: int):
        return self._value <= other

    def __gt__(self, other: int):
        return self._value > other

    def __ge__(self, other: int):
        return self._value >= other
