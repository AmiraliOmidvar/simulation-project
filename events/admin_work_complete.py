from activties import LAB
from events.base.base import BaseEvent
from events.base.types import EventTypes


class AdminWorkComplete(BaseEvent):
    """
    Handles the completion of administrative work related to laboratory activities for a patient.

    This event is triggered when administrative tasks associated with laboratory processes are completed.
    It determines whether there are available beds in the lab. If the lab is at full capacity, the patient
    is added to the lab queue. Otherwise, the patient occupies a lab bed, and a subsequent `LAB_WORK_COMPLETE`
    event is scheduled to handle the next steps in the patient's laboratory-related workflow.

    Attributes:
        patient (Patient, optional): The patient associated with this administrative work completion event.
            This attribute is set during initialization if a patient is provided.
    """

    def __init__(self, event_time, system_state, sim_engine, analytics, **kwargs):
        """
        Initializes the AdminWorkComplete event with the given parameters.

        Args:
            event_time (float): The simulation time at which the event is scheduled to occur.
            system_state (SystemState): The current state of the simulation system.
            sim_engine (SimulationEngine): The simulation engine responsible for managing and executing events.
            analytics (AnalyticsData): The analytics component for recording event outcomes and system metrics.
            **kwargs: Additional keyword arguments. Expected to include 'patient' if the event is patient-related.
        """
        super().__init__(event_time, system_state, sim_engine, analytics)
        self.patient = kwargs.get("patient")  # Retrieve the patient from keyword arguments, if provided

    def execute(self):
        """
        Executes the AdminWorkComplete event.

        This method performs the following actions:
            1. Checks if the number of occupied lab beds has reached the lab's capacity.
            2. If the lab is full, adds the patient to the lab queue.
            3. If there is available space, assigns a lab bed to the patient and schedules a `LAB_WORK_COMPLETE`
               event to handle the next phase of the patient's laboratory process.

        Raises:
            KeyError: If `patient` is not set and is required for processing.
        """
        # Check if the lab has reached its maximum capacity
        if self.system_state.num_occupied_beds_lab >= self.system_state.CAPACITY_LAB:
            # Lab is full; add the patient to the lab queue
            self.system_state.lab_queue.push(patient=self.patient)
        else:
            # Lab has available beds; assign a bed to the patient
            self.system_state.num_occupied_beds_lab += 1
            # Schedule the next event indicating the completion of lab work for the patient
            self.sim_engine.schedule_event(
                event_type=EventTypes.LAB_WORK_COMPLETE,
                event_time=LAB(),  # Determine the time for the next lab work completion
                patient=self.patient
            )
