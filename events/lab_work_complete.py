from activties import LAB, LAB_RESULT, PRE_OR_ORDINARY
from entities.patient import Patient, PatientType
from events.base.base import BaseEvent
from events.base.types import EventTypes


class LabWorkComplete(BaseEvent):
    """
    Handles the arrival of one (or multiple) patients.
    Assumes we already have a patient_id counter somewhere,
    or you pass it in the event. We'll do a simple approach here.
    """

    def __init__(self, event_time, system_state, sim_engine, analytics, **kwargs):
        super().__init__(event_time, system_state, sim_engine, analytics)
        self.patient: Patient = kwargs.get("patient")

    def execute(self):
        self.system_state.num_occupied_beds_lab -= 1
        if self.patient.patient_type == PatientType.URGENT:
            self.sim_engine.schedule_event(
                event_type=EventTypes.MOVE_TO_OR, event_time=LAB_RESULT(), patient=self.patient
            )
        if self.patient.patient_type == PatientType.ORDINARY:
            self.sim_engine.schedule_event(
                event_type=EventTypes.MOVE_TO_OR, event_time=PRE_OR_ORDINARY(), patient=self.patient
            )

        if not self.system_state.lab_queue.is_empty():
            self.system_state.num_occupied_beds_lab += 1
            next_patient = self.system_state.lab_queue.pop()
            self.sim_engine.schedule_event(
                event_type=EventTypes.LAB_WORK_COMPLETE, event_time=LAB(), patient=next_patient
            )
