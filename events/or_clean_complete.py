from entities.patient import Patient
from events.base.base import BaseEvent
from events.base.types import EventTypes
from utils.number_generator import Generator

generator = Generator()


class OrCleanComplete(BaseEvent):
    def __init__(self, event_time, system_state, sim_engine, analytics, **kwargs):
        super().__init__(event_time, system_state, sim_engine, analytics)

    def execute(self):
        self.system_state.num_occupied_beds_or -= 1
        if not self.system_state.or_queue.is_empty():
            next_patient = self.system_state.or_queue.pop()
            self.sim_engine.schedule_event(
                event_type=EventTypes.MOVE_TO_OR, event_time=0, patient=next_patient
            )
