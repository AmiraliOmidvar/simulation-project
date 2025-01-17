from activties import CCU_STAY, GENERAL_STAY
from entities.patient import Patient
from events.base.base import ExitEvent
from events.base.types import EventTypes


class CCUDeparture(ExitEvent):
    """
    Represents the departure event of a patient from the Critical Care Unit (CCU).

    This event is triggered when a patient completes their stay in the CCU. It handles the removal
    of the patient from the CCU occupancy, checks the CCU queue for waiting patients, and assigns
    the next patient in line to an available CCU bed if available. Additionally, it schedules the
    next departure event for the patient who is assigned to the CCU.
    """

    def __init__(self, event_time, system_state, sim_engine, analytics, **kwargs):
        """
        Initializes the CCUDeparture event with the given parameters.

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
        Executes the CCUDeparture event.

        This method performs the following actions:
            1. Removes the patient from the list of occupied CCU beds.
            2. Decrements the count of occupied CCU beds.
            3. Checks if there are patients waiting in the CCU queue.
            4. If the queue is not empty, assigns the next patient to a CCU bed.
            5. Schedules a new CCU_DEPARTURE event for the patient assigned to the CCU.
        """
        # Check if the patient is currently occupying a CCU bed
        if self.patient in self.system_state.ccu_patients:
            self.system_state.ccu_patients.remove(self.patient)  # Remove patient from CCU occupancy
            self.system_state.num_occupied_beds_ccu -= 1  # Decrement occupied CCU beds count

        # Check if there are patients waiting in the CCU queue
        if not self.system_state.ccu_queue.is_empty():
            next_patient = self.system_state.ccu_queue.pop()  # Retrieve the next patient from the queue
            self.system_state.ccu_patients.append(next_patient)  # Assign patient to CCU
            self.system_state.num_occupied_beds_ccu += 1  # Increment occupied CCU beds count
            self.system_state.num_occupied_beds_or -= 1  # Decrement occupied OR beds count (if applicable)

            # Schedule the next departure event for the patient assigned to the CCU
            self.sim_engine.schedule_event(
                event_type=EventTypes.CCU_DEPARTURE,  # Type of the event to schedule
                event_time=CCU_STAY(),  # Generate the time for the next departure using CCU_STAY activity
                patient=next_patient  # Associate the event with the patient
            )
