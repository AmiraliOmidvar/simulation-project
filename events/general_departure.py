from entities.patient import Patient
from events.base.base import ExitEvent
from events.base.types import EventTypes
from activties import GENERAL_STAY


class GeneralDeparture(ExitEvent):
    def __init__(self, event_time, system_state, sim_engine, analytics, **kwargs):
        super().__init__(event_time, system_state, sim_engine, analytics)
        self.patient: Patient = kwargs.get("patient")

    def execute(self):
        super().execute()
        self.system_state.num_occupied_beds_general -= 1
        if not self.system_state.general_queue.is_empty():
            self.system_state.num_occupied_beds_general += 1
            next_patient = self.system_state.general_queue.pop()
            self.system_state.num_occupied_beds_or -= 1
            self.sim_engine.schedule_event(
                event_type=EventTypes.GENERAL_DEPARTURE, event_time=GENERAL_STAY(), patient=next_patient
            )
