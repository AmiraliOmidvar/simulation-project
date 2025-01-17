from common.protocols import SimulationEngine
from system_state import SystemState
from analytics import AnalyticsData


class BaseEvent:
    """
    Base class for events. Must implement 'execute'.
    Provides ordering by event time for priority queue usage.
    """

    def __init__(
            self, event_time, system_state: SystemState, sim_engine: SimulationEngine, analytics: AnalyticsData, **kwargs
    ):
        self.time = event_time
        self.sim_engine: SimulationEngine = sim_engine
        self.system_state: SystemState = system_state
        self.analytics = analytics
        self.patient = None

    def __lt__(self, other):
        return self.time < other.time

    def execute(self):
        """
        Called when the simulation clock == self.time.
        Must be implemented by subclasses.
        """
        pass

    def __repr__(self):
        if self.patient is not None:
            return f"{self.__class__.__name__} at time={self.time} patient id : {self.patient.patient_id}"
        else:
            return f"{self.__class__.__name__} at time={self.time}"

    @property
    def name(self):
        return self.__class__.__name__

    @property
    def patient_id(self):
        if self.patient is not None:
            return self.patient.patient_id
        else:
            return None

    @property
    def patient_type(self):
        if self.patient is not None:
            return self.patient.patient_type.value
        else:
            return None

    @property
    def patient_surgery(self):
        if self.patient is not None:
            return self.patient.patient_surgery.value
        else:
            return None


class ExitEvent(BaseEvent):

    def execute(self):
        self.analytics.patients[self.patient.patient_id].exit_time = self.system_state.current_time
