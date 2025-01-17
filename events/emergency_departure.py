from activties import ADMIN_WORK_URGENT
from entities.patient import Patient
from events.base.base import BaseEvent
from events.base.types import EventTypes


class EmergencyDeparture(BaseEvent):
    def __init__(self, event_time, system_state, sim_engine, analytics, **kwargs):
        super().__init__(event_time, system_state, sim_engine, analytics)
        self.patient: Patient = kwargs.get("patient")

    def execute(self):
        self.system_state.num_occupied_beds_emergency -= 1

        if not self.system_state.emergency_queue.is_empty():
            self.system_state.num_occupied_beds_emergency += 1
            next_patient = self.system_state.emergency_queue.pop()

            self.sim_engine.schedule_event(
                event_type=EventTypes.ADMIN_WORK_COMPLETED,
                event_time=ADMIN_WORK_URGENT(),
                patient=next_patient
            )
