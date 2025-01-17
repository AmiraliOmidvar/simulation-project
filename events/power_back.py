from events.base.base import BaseEvent


class PowerBack(BaseEvent):
    def __init__(self, event_time, system_state, sim_engine, analytics, **kwargs):
        super().__init__(event_time, system_state, sim_engine, analytics)

    def execute(self):
        self.system_state.power_status = 1
        self.system_state.CAPACITY_CCU = int(self.system_state.CAPACITY_CCU / 0.8)
        self.system_state.CAPACITY_ICU = int(self.system_state.CAPACITY_ICU / 0.8)