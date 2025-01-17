from activties import ADMIN_WORK_URGENT, URGENT_INTERARRIVAL
from entities.patient import Patient, PatientSurgery, PatientType
from events.base.base import BaseEvent
from events.base.types import EventTypes
from utils.number_generator import Generator

generator = Generator()


class PatientArrivalUrgentEvent(BaseEvent):
    """
    Handles the arrival of one (or multiple) patients.
    Assumes we already have a patient_id counter somewhere,
    or you pass it in the event. We'll do a simple approach here.
    """

    def __init__(self, event_time, system_state, sim_engine, analytics, **kwargs):
        super().__init__(event_time, system_state, sim_engine, analytics)

    def execute(self):
        if self._is_mass_casualty_event():
            group_size = generator.randint(2, 5)
            self._handle_mass_casualty_event(group_size)

        surgery_type = self._get_surgery_type()
        has_heart_problem = self._get_has_heart_problems()

        self.patient = self._make_patient(PatientType.URGENT, surgery_type, has_heart_problem)
        self._add_urgent_patient(self.patient)
        self._schedule_next_patient()

    def _handle_mass_casualty_event(self, group_size: int):
        for i in range(group_size):
            surgery_type = self._get_surgery_type()
            # we assume mass casualty patients doesnt have heart problems
            patient = self._make_patient(PatientType.URGENT, surgery_type, False)
            if not self._add_urgent_patient(patient):
                # don't accept the rest
                break

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

    @staticmethod
    def _is_mass_casualty_event():
        r = generator.uniform(0, 1)
        return r < 0.005

    def _add_urgent_patient(self, patient):
        if self.system_state.num_occupied_beds_emergency >= self.system_state.CAPACITY_ER:
            self.analytics.emergency_is_full[self.system_state.current_time] = True
            if len(self.system_state.emergency_queue) >= self.system_state.CAPACITY_AMBULANCE:
                # reject patients
                return False

            else:
                self.system_state.emergency_queue.push(patient)
        else:
            self.analytics.emergency_is_full[self.system_state.current_time] = False
            self.system_state.num_occupied_beds_emergency += 1
            self._schedule_urgent_patient_events(patient)

    def _schedule_urgent_patient_events(self, patient: Patient):
        self.sim_engine.schedule_event(
            event_type=EventTypes.ADMIN_WORK_COMPLETED,
            event_time=ADMIN_WORK_URGENT(),
            patient=patient
        )

    def _schedule_next_patient(self):
        self.sim_engine.schedule_event(
            event_type=EventTypes.PATIENT_ARRIVAL_URGENT,
            event_time=URGENT_INTERARRIVAL(),
        )

    def _make_patient(self, patient_type, surgery_type, has_heart_problem):
        patient_id = self.sim_engine.counter.get_current_patient_id()
        patient = Patient(
            patient_id=patient_id, enter_time=self.system_state.current_time, patient_type=patient_type,
            patient_surgery=surgery_type, has_heart_problem=has_heart_problem
        )
        self.analytics.patients[patient.patient_id] = patient
        return patient
