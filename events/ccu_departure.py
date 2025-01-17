from activties import CCU_STAY, GENERAL_STAY
from entities.patient import Patient
from events.base.base import ExitEvent
from events.base.types import EventTypes


class CCUDeparture(ExitEvent):
    def __init__(self, event_time, system_state, sim_engine, analytics, **kwargs):
        super().__init__(event_time, system_state, sim_engine, analytics)
        self.patient: Patient = kwargs.get("patient")

    def execute(self):
        if self.patient in self.system_state.ccu_patients:
            self.system_state.ccu_patients.remove(self.patient)
            self.system_state.num_occupied_beds_ccu -= 1

        if not self.system_state.ccu_queue.is_empty():
            next_patient = self.system_state.ccu_queue.pop()
            self.system_state.ccu_patients.append(next_patient)
            self.system_state.num_occupied_beds_ccu += 1
            self.system_state.num_occupied_beds_or -= 1
            self.sim_engine.schedule_event(
                event_type=EventTypes.CCU_DEPARTURE, event_time=CCU_STAY(), patient=next_patient
            )
