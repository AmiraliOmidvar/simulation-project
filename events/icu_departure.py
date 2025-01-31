from activties import GENERAL_STAY, ICU_STAY, OR_CLEAN_UP
from entities.patient import Patient
from events.base.base import ExitEvent
from events.base.types import EventTypes


class ICUDeparture(ExitEvent):
    """
    Handles the departure of a patient from the Intensive Care Unit (ICU).

    This event is triggered when a patient completes their stay in the ICU. It updates the count
    of occupied ICU beds, checks the ICU queue for waiting patients, and assigns the next patient
    in line to an available ICU bed if possible. Additionally, it schedules the next departure
    event for the patient who is assigned to the ICU.

    Attributes:
        patient (Patient): The patient associated with this departure event.
    """

    def __init__(self, event_time, system_state, sim_engine, analytics, **kwargs):
        """
        Initializes the ICUDeparture event with the given parameters.

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
        Executes the ICUDeparture event.

        This method performs the following actions:
            1. Checks if the patient is currently occupying an ICU bed.
            2. If the patient is in the ICU, removes them from the list of occupied ICU beds
               and decrements the count of occupied ICU beds.
            3. Checks if there are patients waiting in the ICU queue.
            4. If the queue is not empty, assigns the next patient to an available ICU bed.
            5. Decrements the count of occupied OR beds if applicable.
            6. Schedules a new ICU_DEPARTURE event for the patient assigned to the ICU.
        """
        # Check if the patient is currently occupying an ICU bed
        if self.patient in self.system_state.icu_patients:
            self.system_state.icu_patients.remove(self.patient)  # Remove patient from ICU occupancy
            self.system_state.num_occupied_beds_icu -= 1  # Decrement occupied ICU beds count

        # Check if there are patients waiting in the ICU queue
        if not self.system_state.icu_queue.is_empty():
            # Assign a bed to the next patient in the queue
            next_patient = self.system_state.icu_queue.pop()  # Retrieve the next patient from the queue
            self.system_state.icu_patients.append(next_patient)  # Assign patient to ICU
            self.system_state.num_occupied_beds_icu += 1  # Increment occupied ICU beds count
            self._schedule_cleanup_complete_event()

            # Schedule the next departure event for the patient assigned to the ICU
            self.sim_engine.schedule_event(
                event_type=EventTypes.ICU_DEPARTURE,  # Type of event to schedule
                event_time=ICU_STAY(),  # Time at which the event should occur
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