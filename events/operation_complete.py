from activties import CCU_STAY, GENERAL_STAY, ICU_STAY, OR_CLEAN_UP
from entities.patient import Patient, PatientSurgery
from events.base.base import BaseEvent
from events.base.types import EventTypes
from utils.number_generator import Generator

generator = Generator()


class OperationComplete(BaseEvent):
    """
    Handles the arrival of one (or multiple) patients.
    Assumes we already have a patient_id counter somewhere,
    or you pass it in the event. We'll do a simple approach here.
    """

    def __init__(self, event_time, system_state, sim_engine, analytics, **kwargs):
        super().__init__(event_time, system_state, sim_engine, analytics)
        self.patient: Patient = kwargs.get("patient")

    def execute(self):
        if self.patient.patient_surgery == PatientSurgery.COMPLEX:
            self._handle_complex()

        if self.patient.patient_surgery == PatientSurgery.MEDIUM:
            self._handle_medium()

        if self.patient.patient_surgery == PatientSurgery.SIMPLE:
            self._handle_simple()

    def _schedule_cleanup_complete_event(self):
        self.sim_engine.schedule_event(
            event_type=EventTypes.OR_CLEAN_UP_COMPLETE, event_time=OR_CLEAN_UP()
        )

    def _handle_complex(self):
        # resurgery
        r = generator.uniform(0, 1)
        if r < 0.01:
            # 10 is for cleanup
            self.sim_engine.schedule_event(
                event_type=EventTypes.MOVE_TO_OR, event_time=OR_CLEAN_UP(), patient=self.patient,
                is_resurgery=True
            )
            self.analytics.resurgery[self.patient.patient_id] = True
            return
        else:
            if self.patient.patient_id not in self.analytics.resurgery:
                self.analytics.resurgery[self.patient.patient_id] = False

        # death
        r = generator.uniform(0, 1)
        if r < 0.1:
            self.analytics.patients[self.patient.patient_id].exit_time = self.system_state.current_time
            self._schedule_cleanup_complete_event()
            return

        if self.patient.has_heart_problem:
            if self.system_state.num_occupied_beds_ccu >= self.system_state.CAPACITY_CCU:
                self.system_state.ccu_queue.push(self.patient)
            else:
                # schedule ccu departure
                self._add_to_ccu()

        else:
            if self.system_state.num_occupied_beds_icu >= self.system_state.CAPACITY_ICU:
                self.system_state.icu_queue.push(self.patient)
            else:
                # schedule icu departure
                self._add_to_icu()

    def _handle_medium(self):
        r = generator.uniform(0, 1)
        if r < 0.7:
            if self.system_state.num_occupied_beds_general >= self.system_state.CAPACITY_GENERAL:
                self.system_state.general_queue.push(self.patient)
            else:
                self._add_to_general()

        elif 0.7 < r < 0.8:
            if self.system_state.num_occupied_beds_icu >= self.system_state.CAPACITY_ICU:
                self.system_state.icu_queue.push(self.patient)
            else:
                self._add_to_icu()

        else:
            if self.system_state.num_occupied_beds_ccu >= self.system_state.CAPACITY_CCU:
                self.system_state.ccu_queue.push(self.patient)
            else:
                self._add_to_ccu()

    def _handle_simple(self):
        if self.system_state.num_occupied_beds_general >= self.system_state.CAPACITY_GENERAL:
            self.system_state.general_queue.push(self.patient)
        else:
            self._add_to_general()

    def _add_to_ccu(self):
        self.system_state.num_occupied_beds_ccu += 1
        self.system_state.ccu_patients.append(self.patient)
        self.sim_engine.schedule_event(
            event_type=EventTypes.CCU_DEPARTURE, event_time=CCU_STAY(),
            patient=self.patient
        )
        self._schedule_cleanup_complete_event()

    def _add_to_icu(self):
        self.system_state.num_occupied_beds_icu += 1
        self.system_state.icu_patients.append(self.patient)
        self.sim_engine.schedule_event(
            event_type=EventTypes.ICU_DEPARTURE, event_time=ICU_STAY(),
            patient=self.patient
        )
        self._schedule_cleanup_complete_event()

    def _add_to_general(self):
        self.system_state.num_occupied_beds_general += 1
        self.sim_engine.schedule_event(
            event_type=EventTypes.GENERAL_DEPARTURE, event_time=GENERAL_STAY(),
            patient=self.patient
        )
        self._schedule_cleanup_complete_event()
