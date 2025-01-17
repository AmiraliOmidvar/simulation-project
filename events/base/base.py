from common.protocols import SimulationEngine
from system_state import SystemState
from analytics import AnalyticsData


class BaseEvent:
    """
    Base class for all events in the simulation.

    This class serves as the foundational blueprint for all specific events that occur
    within the simulation system. It ensures that events are processed in chronological
    order by leveraging Python's priority queue mechanisms. Subclasses must implement the
    `execute` method to define the event-specific behavior.

    Attributes:
        time (float): The scheduled time at which the event should occur.
        sim_engine (SimulationEngine): Reference to the simulation engine managing the event queue.
        system_state (SystemState): Reference to the current state of the system being simulated.
        analytics (AnalyticsData): Reference to the analytics data collector for recording event outcomes.
        patient (Patient, optional): Reference to the patient involved in the event, if applicable.
    """

    def __init__(
            self,
            event_time: float,
            system_state: SystemState,
            sim_engine: SimulationEngine,
            analytics: AnalyticsData,
            **kwargs
    ):
        """
        Initializes the BaseEvent with essential references and scheduling information.

        Args:
            event_time (float): The simulation time at which the event is scheduled to occur.
            system_state (SystemState): The current state of the system.
            sim_engine (SimulationEngine): The simulation engine managing the event queue.
            analytics (AnalyticsData): The analytics component for recording event data.
            **kwargs: Additional keyword arguments for extended functionality in subclasses.
        """
        self.time = event_time
        self.sim_engine: SimulationEngine = sim_engine
        self.system_state: SystemState = system_state
        self.analytics = analytics
        self.patient = None  # To be assigned in subclasses if the event is patient-related

    def __lt__(self, other: 'BaseEvent') -> bool:
        """
        Defines the less-than comparison based on event time for priority queue ordering.

        This method allows the priority queue to sort events chronologically.

        Args:
            other (BaseEvent): Another event to compare against.

        Returns:
            bool: True if this event's time is earlier than the other event's time, False otherwise.
        """
        return self.time < other.time

    def execute(self):
        """
        Executes the event's specific actions.

        This method is called by the simulation engine when the simulation clock reaches
        the event's scheduled time. Subclasses must override this method to define
        the event's behavior.
        """
        raise NotImplementedError("Execute method must be implemented by subclasses.")

    def __repr__(self) -> str:
        """
        Provides a string representation of the event for debugging and logging.

        Returns:
            str: A string detailing the event's class name, scheduled time, and associated patient ID if applicable.
        """
        if self.patient is not None:
            return f"{self.__class__.__name__} at time={self.time} patient id: {self.patient.patient_id}"
        else:
            return f"{self.__class__.__name__} at time={self.time}"

    @property
    def name(self) -> str:
        """
        Retrieves the name of the event based on its class.

        Returns:
            str: The class name of the event.
        """
        return self.__class__.__name__

    @property
    def patient_id(self) -> int:
        """
        Retrieves the patient ID associated with the event, if any.

        Returns:
            int or None: The patient ID if the event is patient-related; otherwise, None.
        """
        if self.patient is not None:
            return self.patient.patient_id
        return None

    @property
    def patient_type(self) -> str:
        """
        Retrieves the type of the patient involved in the event, if any.

        Returns:
            str or None: The patient type if applicable; otherwise, None.
        """
        if self.patient is not None:
            return self.patient.patient_type.value
        return None

    @property
    def patient_surgery(self) -> str:
        """
        Retrieves the surgery details of the patient involved in the event, if any.

        Returns:
            str or None: The surgery details if applicable; otherwise, None.
        """
        if self.patient is not None:
            return self.patient.patient_surgery.value
        return None


class ExitEvent(BaseEvent):
    """
    Event representing a patient exiting the system.

    This event is triggered when a patient completes their stay in the system and exits.
    It updates the analytics data to record the patient's exit time.
    """

    def execute(self):
        """
        Executes the ExitEvent by recording the patient's exit time.

        Updates the `exit_time` attribute of the patient in the analytics data to the current simulation time.
        This signifies that the patient has left the system.
        """
        if self.patient and self.patient.patient_id in self.analytics.patients:
            self.analytics.patients[self.patient.patient_id].exit_time = self.system_state.current_time
