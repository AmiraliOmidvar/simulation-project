from typing import List

from entities.patient import Patient, PatientPriorityQueue
from task_manager import task_queue
from utils.queue import Queue


class SystemState:
    """
    Represents the global state of the simulation at any given time `t`.

    This class maintains all relevant information about the system, including queues for different
    wards/sections, the number of occupied beds, power status, and maximum capacities for each
    section. It serves as a central repository for the simulation's current state, allowing
    different components of the simulation to access and modify the state as events are processed.

    Attributes:
        current_time (float): The current time in the simulation clock.

        lab_queue (PatientPriorityQueue): Priority queue for the lab section, managing patients awaiting lab services.
        emergency_queue (PatientPriorityQueue): Priority queue for the emergency room, managing incoming patients.
        or_queue (PatientPriorityQueue): Priority queue for the operating room (OR), managing patients scheduled for surgery.

        ccu_queue (Queue): Queue for the Coronary Care Unit (CCU), managing patients awaiting CCU beds.
        icu_queue (Queue): Queue for the Intensive Care Unit (ICU), managing patients awaiting ICU beds.
        general_queue (Queue): Queue for the General Ward, managing patients awaiting general beds.

        ccu_patients (List[Patient]): List of patients currently occupying CCU beds.
        icu_patients (List[Patient]): List of patients currently occupying ICU beds.

        num_occupied_beds_general (NumOccupied): Tracker for the number of occupied general ward beds.
        num_occupied_beds_or (NumOccupied): Tracker for the number of occupied OR beds.
        num_occupied_beds_emergency (NumOccupied): Tracker for the number of occupied emergency beds.
        num_occupied_beds_lab (NumOccupied): Tracker for the number of occupied lab beds.
        num_occupied_beds_icu (NumOccupied): Tracker for the number of occupied ICU beds.
        num_occupied_beds_ccu (NumOccupied): Tracker for the number of occupied CCU beds.
        num_occupied_beds_pre_or (NumOccupied): Tracker for the number of occupied pre-operation beds.

        power_status (int): Indicates the power status of the system (1 = power on, 0 = power off).

        CAPACITY_ER (int): Maximum number of beds available in the Emergency Room.
        CAPACITY_PRE_OR (int): Maximum number of beds available in the Pre-operation area.
        CAPACITY_OR (int): Maximum number of beds available in the Operating Room.
        CAPACITY_GENERAL (int): Maximum number of beds available in the General Ward.
        CAPACITY_LAB (int): Maximum number of beds available in the Lab section.
        CAPACITY_ICU (int): Maximum number of beds available in the Intensive Care Unit.
        CAPACITY_CCU (int): Maximum number of beds available in the Coronary Care Unit.
        CAPACITY_AMBULANCE (int): Maximum number of beds available in the Ambulance section.
    """

    def __init__(self):
        """
        Initializes the SystemState with default values and empty queues.

        Sets up all queues for different sections, initializes patient lists for CCU and ICU,
        and sets the initial power status to on. It also defines the maximum capacities for each
        ward/section in the simulation.
        """
        self.current_time = 0.0  # Simulation clock starts at time 0

        # Initialize priority queues for sections where patient priority matters
        self.lab_queue: PatientPriorityQueue = PatientPriorityQueue("lab", self)  # Queue for lab services
        self.emergency_queue: PatientPriorityQueue = PatientPriorityQueue("emergency", self)  # Emergency room queue
        self.or_queue: PatientPriorityQueue = PatientPriorityQueue("or", self)  # Operating room queue

        # Initialize standard queues for sections where order of arrival is sufficient
        self.ccu_queue: Queue = Queue("ccu", self)  # Coronary Care Unit queue
        self.icu_queue: Queue = Queue("icu", self)  # Intensive Care Unit queue
        self.general_queue: Queue = Queue("general", self)  # General Ward queue

        # Lists to keep track of patients currently occupying CCU and ICU beds
        self.ccu_patients: List[Patient] = []  # Patients in CCU
        self.icu_patients: List[Patient] = []  # Patients in ICU

        # Initialize trackers for occupied beds in each section
        self.num_occupied_beds_general = NumOccupied("general", self)  # General Ward beds
        self.num_occupied_beds_or = NumOccupied("or", self)  # Operating Room beds
        self.num_occupied_beds_emergency = NumOccupied("emergency", self)  # Emergency Room beds
        self.num_occupied_beds_lab = NumOccupied("lab", self)  # Lab beds
        self.num_occupied_beds_icu = NumOccupied("icu", self)  # ICU beds
        self.num_occupied_beds_ccu = NumOccupied("ccu", self)  # CCU beds
        self.num_occupied_beds_pre_or = NumOccupied("pre_or", self)  # Pre-operation beds

        # Power status: 1 = power on, 0 = power off
        self.power_status = 1

        # Define maximum capacities for each section
        self.CAPACITY_ER = 10  # Maximum ER beds
        self.CAPACITY_PRE_OR = 25  # Maximum Pre-operation beds
        self.CAPACITY_OR = 50  # Maximum Operating Room beds
        self.CAPACITY_GENERAL = 40  # Maximum General Ward beds
        self.CAPACITY_LAB = 3  # Maximum Lab beds
        self.CAPACITY_ICU = 10  # Maximum ICU beds
        self.CAPACITY_CCU = 5  # Maximum CCU beds
        self.CAPACITY_AMBULANCE = 10  # Maximum Ambulance beds


class NumOccupied:
    """
    Tracks the number of occupied beds in a specific ward or section.

    This class encapsulates the logic for incrementing and decrementing the number of occupied
    beds, ensuring that any change in occupancy triggers appropriate hooks for further processing
    or logging.

    Attributes:
        _value (int): The current number of occupied beds.
        name (str): The name of the ward or section being tracked.
        state (SystemState): Reference to the global system state.
    """

    def __init__(self, name: str, state: SystemState):
        """
        Initializes the NumOccupied instance for a specific ward/section.

        Args:
            name (str): The name of the ward or section (e.g., "general", "icu").
            state (SystemState): Reference to the current system state to access simulation time.
        """
        self._value = 0  # Start with zero occupied beds
        self.name = name
        self.state = state

    def _trigger_hook(self):
        """
        Triggers a hook whenever the number of occupied beds changes.

        This method appends a task to the global `task_queue`, indicating that a change has
        occurred in the specified section at the current simulation time. This can be used
        for logging, monitoring, or triggering other actions in the simulation.
        """
        task = {
            "task": "section",
            "section": self.name,
            "time": self.state.current_time,
            "number": self._value
        }
        task_queue.append(task)

    def __iadd__(self, other: int):
        """
        Handles the in-place addition (+=) operation to increment the number of occupied beds.

        Args:
            other (int): The number to add to the current count of occupied beds.

        Returns:
            NumOccupied: The updated instance with the incremented value.
        """
        self._value += other
        self._trigger_hook()  # Notify about the change
        return self

    def __isub__(self, other: int):
        """
        Handles the in-place subtraction (-=) operation to decrement the number of occupied beds.

        Args:
            other (int): The number to subtract from the current count of occupied beds.

        Returns:
            NumOccupied: The updated instance with the decremented value.
        """
        self._value -= other
        self._trigger_hook()  # Notify about the change
        return self

    def __int__(self):
        """
        Allows the instance to be converted to an integer representing the number of occupied beds.

        Returns:
            int: The current number of occupied beds.
        """
        return self._value

    def __repr__(self):
        """
        Provides a string representation of the NumOccupied instance for debugging purposes.

        Returns:
            str: The string representation showing the current number of occupied beds.
        """
        return f"{self._value}"

    def __eq__(self, other: int):
        """
        Checks if the number of occupied beds is equal to a given value.

        Args:
            other (int): The value to compare against.

        Returns:
            bool: True if equal, False otherwise.
        """
        return self._value == other

    def __ne__(self, other: int):
        """
        Checks if the number of occupied beds is not equal to a given value.

        Args:
            other (int): The value to compare against.

        Returns:
            bool: True if not equal, False otherwise.
        """
        return self._value != other

    def __lt__(self, other: int):
        """
        Checks if the number of occupied beds is less than a given value.

        Args:
            other (int): The value to compare against.

        Returns:
            bool: True if less than, False otherwise.
        """
        return self._value < other

    def __le__(self, other: int):
        """
        Checks if the number of occupied beds is less than or equal to a given value.

        Args:
            other (int): The value to compare against.

        Returns:
            bool: True if less than or equal to, False otherwise.
        """
        return self._value <= other

    def __gt__(self, other: int):
        """
        Checks if the number of occupied beds is greater than a given value.

        Args:
            other (int): The value to compare against.

        Returns:
            bool: True if greater than, False otherwise.
        """
        return self._value > other

    def __ge__(self, other: int):
        """
        Checks if the number of occupied beds is greater than or equal to a given value.

        Args:
            other (int): The value to compare against.

        Returns:
            bool: True if greater than or equal to, False otherwise.
        """
        return self._value >= other
