from activties import OR_COMPLEX, OR_MEDIUM, OR_SIMPLE
from entities.patient import Patient, PatientSurgery, PatientType
from events.base.base import BaseEvent
from events.base.types import EventTypes


class MoveToOr(BaseEvent):
    """
    Handles the arrival of one (or multiple) patients.
    Assumes we already have a patient_id counter somewhere,
    or you pass it in the event. We'll do a simple approach here.
    """

    def __init__(self, event_time, system_state, sim_engine, analytics, **kwargs):
        super().__init__(event_time, system_state, sim_engine, analytics)
        self.patient: Patient = kwargs.get("patient")
        self.is_resurgery = kwargs.get("is_resurgery", False)

    def execute(self):
        if self.is_resurgery:
            self._handle_operation()

        else:
            if self.system_state.num_occupied_beds_or >= self.system_state.CAPACITY_OR:
                self.system_state.or_queue.push(self.patient)
                return

            if self.patient.patient_type == PatientType.ORDINARY:
                self.system_state.num_occupied_beds_pre_or -= 1
            if self.patient.patient_type == PatientType.URGENT:
                self._schedule_emergency_departure()
            self._handle_operation()

    def _handle_operation(self):
        if self.patient.patient_surgery == PatientSurgery.COMPLEX:
            self.system_state.num_occupied_beds_or += 1
            self.sim_engine.schedule_event(
                event_type=EventTypes.OPERATION_COMPLETE, event_time=OR_COMPLEX(), patient=self.patient
            )

        if self.patient.patient_surgery == PatientSurgery.MEDIUM:
            self.system_state.num_occupied_beds_or += 1
            self.sim_engine.schedule_event(
                event_type=EventTypes.OPERATION_COMPLETE, event_time=OR_MEDIUM(), patient=self.patient
            )

        if self.patient.patient_surgery == PatientSurgery.SIMPLE:
            self.system_state.num_occupied_beds_or += 1
            self.sim_engine.schedule_event(
                event_type=EventTypes.OPERATION_COMPLETE, event_time=OR_SIMPLE(), patient=self.patient
            )

    def _schedule_emergency_departure(self):
        self.sim_engine.schedule_event(
            event_type=EventTypes.EMERGENCY_DEPARTURE, event_time=0, patient=self.patient
        )
