from activties import GENERAL_STAY, OR_CLEAN_UP
from entities.patient import Patient
from events.base.base import ExitEvent
from events.base.types import EventTypes


class GeneralDeparture(ExitEvent):
    """
    Handles the departure of a patient from the General Ward.

    This event is triggered when a patient completes their stay in the General Ward.
    It updates the count of occupied beds, checks the General Ward queue for waiting patients,
    and assigns the next patient in line to an available bed if possible. Additionally,
    it schedules the next departure event for the patient who is assigned to the General Ward.

    Attributes:
        patient (Patient): The patient associated with this departure event.
    """

    def __init__(self, event_time, system_state, sim_engine, analytics, **kwargs):
        """
        Initializes the GeneralDeparture event with the given parameters.

        Args:
            event_time (float): The simulation time at which the departure occurs.
            system_state (SystemState): The current state of the simulation system.
            sim_engine (SimulationEngine): The simulation engine responsible for managing events.
            analytics (AnalyticsData): The analytics component for recording event outcomes.
            **kwargs: Additional keyword arguments. Expected to include 'patient'.
        """
        super().__init__(event_time, system_state, sim_engine, analytics)
        self.patient: Patient = kwargs.get("patient")  # Retrieve the patient from keyword arguments

    def execute(self):
        """
        Executes the GeneralDeparture event.

        This method performs the following actions:
            1. Calls the superclass's execute method to perform any base-level operations.
            2. Decrements the count of occupied beds in the General Ward.
            3. Checks if there are patients waiting in the General Ward queue.
            4. If the queue is not empty, assigns the next patient to an available General Ward bed.
            5. Decrements the count of occupied OR beds (if applicable).
            6. Schedules a new GENERAL_DEPARTURE event for the patient assigned to the General Ward.
        """
        super().execute()  # Perform any base-level execution steps defined in ExitEvent

        # Decrement the number of occupied beds in the General Ward as the patient departs
        self.system_state.num_occupied_beds_general -= 1

        # Check if there are patients waiting in the General Ward queue
        if not self.system_state.general_queue.is_empty():
            # Assign a bed to the next patient in the queue
            self.system_state.num_occupied_beds_general += 1
            next_patient = self.system_state.general_queue.pop()  # Remove the next patient from the queue

            self._schedule_cleanup_complete_event()

            # Schedule the next departure event for the patient assigned to the General Ward
            self.sim_engine.schedule_event(
                event_type=EventTypes.GENERAL_DEPARTURE,  # Type of the event to schedule
                event_time=GENERAL_STAY(),  # Time at which the event should occur
                patient=next_patient  # Patient associated with the event
            )

    def _schedule_cleanup_complete_event(self):
        """
        Schedules the cleanup completion event after an operation.

        This event signifies that the cleaning process in the Operating Room (OR) has been completed.
        """
        self.sim_engine.schedule_event(
            event_type=EventTypes.OR_CLEAN_UP_COMPLETE,
            event_time=OR_CLEAN_UP(),
            patient=self.patient
        )
