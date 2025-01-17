from activties import ADMIN_WORK_URGENT
from entities.patient import Patient
from events.base.base import BaseEvent
from events.base.types import EventTypes


class EmergencyDeparture(BaseEvent):
    """
    Handles the departure of a patient from the Emergency Department (ED).

    This event is triggered when a patient completes their stay in the Emergency Department.
    It updates the count of occupied beds in the ED and checks if there are patients waiting
    in the emergency queue. If there are waiting patients, it assigns the next patient to
    an available ED bed and schedules an `ADMIN_WORK_COMPLETED` event for that patient.

    Attributes:
        patient (Patient): The patient associated with this departure event.
    """

    def __init__(self, event_time, system_state, sim_engine, analytics, **kwargs):
        """
        Initializes the EmergencyDeparture event with the given parameters.

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
        Executes the EmergencyDeparture event.

        This method performs the following actions:
            1. Decrements the count of occupied beds in the Emergency Department.
            2. Checks if there are patients waiting in the emergency queue.
            3. If the queue is not empty, assigns the next patient to an available ED bed.
            4. Schedules an `ADMIN_WORK_COMPLETED` event for the patient assigned to the ED.
        """
        # Decrement the number of occupied beds in the Emergency Department
        self.system_state.num_occupied_beds_emergency -= 1

        # Check if there are patients waiting in the emergency queue
        if not self.system_state.emergency_queue.is_empty():
            # Increment the number of occupied ED beds as a bed becomes available
            self.system_state.num_occupied_beds_emergency += 1

            # Remove the next patient from the emergency queue
            next_patient = self.system_state.emergency_queue.pop()

            # Schedule an ADMIN_WORK_COMPLETED event for the next patient
            self.sim_engine.schedule_event(
                event_type=EventTypes.ADMIN_WORK_COMPLETED,  # Type of event to schedule
                event_time=ADMIN_WORK_URGENT(),  # Time at which the event should occur
                patient=next_patient  # Patient associated with the event
            )
