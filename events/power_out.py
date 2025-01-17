from events.base.base import BaseEvent
from events.base.types import EventTypes
from utils.number_generator import Generator

generator = Generator()


class PowerOut(BaseEvent):
    def __init__(self, event_time, system_state, sim_engine, analytics, **kwargs):
        super().__init__(event_time, system_state, sim_engine, analytics)

    def execute(self):
        self.system_state.power_status = 0
        self.system_state.CAPACITY_CCU = int(self.system_state.CAPACITY_CCU * 0.8)
        self.system_state.CAPACITY_ICU = int(self.system_state.CAPACITY_ICU * 0.8)
        self._remove_overflow_patients()
        self._schedule_next_power_out()
        self._schedule_power_back()

    def _remove_overflow_patients(self):
        while self.system_state.num_occupied_beds_ccu >= self.system_state.CAPACITY_CCU:
            self.system_state.num_occupied_beds_ccu -= 1
            self.system_state.ccu_patients.pop()

        while self.system_state.num_occupied_beds_icu >= self.system_state.CAPACITY_ICU:
            self.system_state.num_occupied_beds_icu -= 1
            self.system_state.icu_patients.pop()

    def _schedule_next_power_out(self):
        month_length = 43200
        next_month = self.system_state.current_time - self.system_state.current_time % month_length + 43200
        inter_outage = generator.uniform(next_month, next_month + 43200)
        self.sim_engine.schedule_event(event_type=EventTypes.POWER_OUT, event_time=inter_outage)

    def _schedule_power_back(self):
        self.sim_engine.schedule_event(event_type=EventTypes.POWER_BACK, event_time=1440)
