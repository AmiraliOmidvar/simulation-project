from activties import LAB
from events.base.base import BaseEvent
from events.base.types import EventTypes


class AdminWorkComplete(BaseEvent):
    """
    Handles the arrival of one (or multiple) patients.
    Assumes we already have a patient_id counter somewhere,
    or you pass it in the event. We'll do a simple approach here.
    """

    def __init__(self, event_time, system_state, sim_engine, analytics, **kwargs):
        super().__init__(event_time, system_state, sim_engine, analytics)
        self.patient = kwargs.get("patient")

    def execute(self):
        if self.system_state.num_occupied_beds_lab >= self.system_state.CAPACITY_LAB:
            self.system_state.lab_queue.push(patient=self.patient)
        else:
            self.system_state.num_occupied_beds_lab += 1
            self.sim_engine.schedule_event(
                event_type=EventTypes.LAB_WORK_COMPLETE, event_time=LAB(), patient=self.patient
            )
