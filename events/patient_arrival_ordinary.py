from activties import ADMIN_WORK_ORDINARY, ORDINARY_INTERARRIVAL
from entities.patient import Patient, PatientSurgery, PatientType
from events.base.base import BaseEvent
from events.base.types import EventTypes
from utils.number_generator import Generator

generator = Generator()


class PatientArrivalOrdinaryEvent(BaseEvent):
    """
    Handles the arrival of one (or multiple) patients.
    Assumes we already have a patient_id counter somewhere,
    or you pass it in the event. We'll do a simple approach here.
    """

    def __init__(self, event_time, system_state, sim_engine, analytics, **kwargs):
        super().__init__(event_time, system_state, sim_engine, analytics)

    def execute(self):
        surgery_type = self._get_surgery_type()
        has_heart_problem = self._get_has_heart_problems()
        self.patient = self._make_patient(PatientType.ORDINARY, surgery_type, has_heart_problem)
        self._add_ordinary_patient(self.patient)
        self._schedule_next_patient()

    @staticmethod
    def _get_surgery_type():
        r = generator.uniform(0, 1)
        if r <= 0.5:
            return PatientSurgery.SIMPLE
        elif 0.5 < r <= 0.95:
            return PatientSurgery.MEDIUM
        else:
            return PatientSurgery.COMPLEX

    @staticmethod
    def _get_has_heart_problems():
        r = generator.uniform(0, 1)
        if r < 0.75:
            return False
        else:
            return True

    def _add_ordinary_patient(self, patient):
        if self.system_state.num_occupied_beds_pre_or >= self.system_state.CAPACITY_PRE_OR:
            # reject patients
            return False
        else:
            self.system_state.num_occupied_beds_pre_or += 1
            self._schedule_ordinary_patient_events(patient)

    def _schedule_next_patient(self):
        self.sim_engine.schedule_event(
            event_type=EventTypes.PATIENT_ARRIVAL_ORDINARY, event_time=ORDINARY_INTERARRIVAL()
        )

    def _schedule_ordinary_patient_events(self, patient: Patient):
        self.sim_engine.schedule_event(
            event_type=EventTypes.ADMIN_WORK_COMPLETED,
            event_time=ADMIN_WORK_ORDINARY(),
            patient=patient
        )

    def _make_patient(self, patient_type, surgery_type, has_heart_problem):
        patient_id = self.sim_engine.counter.get_current_patient_id()
        patient = Patient(
            patient_id=patient_id, enter_time=self.system_state.current_time, patient_type=patient_type,
            patient_surgery=surgery_type, has_heart_problem=has_heart_problem
        )
        self.analytics.patients[patient.patient_id] = patient
        return patient
