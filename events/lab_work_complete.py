from activties import LAB, LAB_RESULT, PRE_OR_ORDINARY
from entities.patient import Patient, PatientType
from events.base.base import BaseEvent
from events.base.types import EventTypes


class LabWorkComplete(BaseEvent):
    """
    Handles the completion of laboratory work for a patient.

    This event is triggered when a patient's laboratory work is completed. Depending on the
    patient's type (URGENT or ORDINARY), it schedules the next appropriate event to move the
    patient to the Operating Room (OR). Additionally, if there are patients waiting in the lab queue,
    it assigns the next patient to an available lab bed and schedules a subsequent LabWorkComplete event.

    Attributes:
        patient (Patient): The patient associated with this lab work completion event.
    """

    def __init__(self, event_time, system_state, sim_engine, analytics, **kwargs):
        """
        Initializes the LabWorkComplete event with the given parameters.

        Args:
            event_time (float): The simulation time at which the lab work is completed.
            system_state (SystemState): The current state of the simulation system.
            sim_engine (SimulationEngine): The simulation engine responsible for managing events.
            analytics (AnalyticsData): The analytics component for recording event outcomes.
            **kwargs: Additional keyword arguments. Expected to include 'patient'.
        """
        super().__init__(event_time, system_state, sim_engine, analytics)
        self.patient: Patient = kwargs.get("patient")  # Retrieve the patient from keyword arguments

    def execute(self):
        """
        Executes the LabWorkComplete event.

        This method performs the following actions:
            1. Decrements the count of occupied lab beds as the patient's lab work is completed.
            2. Checks the patient's type:
                - If URGENT, schedules a MOVE_TO_OR event with a LAB_RESULT time.
                - If ORDINARY, schedules a MOVE_TO_OR event with a PRE_OR_ORDINARY time.
            3. Checks if there are patients waiting in the lab queue:
                - If the queue is not empty, assigns the next patient to an available lab bed.
                - Increments the count of occupied lab beds.
                - Schedules a new LabWorkComplete event for the next patient.
        """
        # Decrement the number of occupied lab beds as the patient's lab work is complete
        self.system_state.num_occupied_beds_lab -= 1

        # Determine the next event based on the patient's type
        if self.patient.patient_type == PatientType.URGENT:
            # Schedule a MOVE_TO_OR event with a LAB_RESULT time for urgent patients
            self.sim_engine.schedule_event(
                event_type=EventTypes.MOVE_TO_OR,
                event_time=LAB_RESULT(),  # Generates the time for the next event
                patient=self.patient
            )
        if self.patient.patient_type == PatientType.ORDINARY:
            # Schedule a MOVE_TO_OR event with a PRE_OR_ORDINARY time for ordinary patients
            self.sim_engine.schedule_event(
                event_type=EventTypes.MOVE_TO_OR,
                event_time=PRE_OR_ORDINARY(),  # Generates the time for the next event
                patient=self.patient
            )

        # Check if there are patients waiting in the lab queue
        if not self.system_state.lab_queue.is_empty():
            # Assign a bed to the next patient in the lab queue
            self.system_state.num_occupied_beds_lab += 1  # Increment occupied lab beds count
            next_patient = self.system_state.lab_queue.pop()  # Retrieve the next patient from the queue

            # Schedule a new LabWorkComplete event for the next patient
            self.sim_engine.schedule_event(
                event_type=EventTypes.LAB_WORK_COMPLETE,
                event_time=LAB(),  # Generates the time for the next LabWorkComplete event
                patient=next_patient
            )
