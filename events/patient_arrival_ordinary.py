"""
Patient Arrival Ordinary Event Module

This module defines the PatientArrivalOrdinaryEvent class, which handles the arrival of ordinary patients
in the simulation. It manages the creation of patient instances, assigns them to pre-operating room (pre-OR)
beds if available, and schedules the necessary subsequent events such as administrative work completion
and the arrival of the next patient.
"""

from activties import ADMIN_WORK_ORDINARY, ORDINARY_INTERARRIVAL
from entities.patient import Patient, PatientSurgery, PatientType
from events.base.base import BaseEvent
from events.base.types import EventTypes
from utils.number_generator import Generator

# Initialize the random number generator instance
generator = Generator()


class PatientArrivalOrdinaryEvent(BaseEvent):
    """
    Handles the arrival of ordinary patients to the simulation.

    This event is triggered when an ordinary patient arrives at the simulation. It determines the
    patient's surgery type and whether they have heart problems, creates a Patient instance, assigns
    them to a pre-OR bed if available, and schedules the necessary subsequent events. It also schedules
    the arrival of the next ordinary patient.

    Attributes:
        patient (Patient): The patient associated with this arrival event.
    """

    def __init__(self, event_time, system_state, sim_engine, analytics, **kwargs):
        """
        Initializes the PatientArrivalOrdinaryEvent with the given parameters.

        Args:
            event_time (float): The simulation time at which the patient arrives.
            system_state (SystemState): The current state of the simulation system.
            sim_engine (SimulationEngine): The simulation engine responsible for managing events.
            analytics (AnalyticsData): The analytics component for recording event outcomes.
            **kwargs: Additional keyword arguments. Not used in this event.
        """
        super().__init__(event_time, system_state, sim_engine, analytics)

    def execute(self):
        """
        Executes the PatientArrivalOrdinaryEvent.

        This method performs the following actions:
            1. Determines the surgery type and whether the patient has heart problems.
            2. Creates a Patient instance with the determined attributes.
            3. Attempts to add the patient to a pre-OR bed.
            4. Schedules the arrival of the next ordinary patient.
        """
        # Determine the type of surgery the patient will undergo
        surgery_type = self._get_surgery_type()
        # Determine if the patient has heart problems
        has_heart_problem = self._get_has_heart_problems()
        # Create a new Patient instance with the determined attributes
        self.patient = self._make_patient(PatientType.ORDINARY, surgery_type, has_heart_problem)
        # Attempt to add the patient to a pre-OR bed
        self._add_ordinary_patient(self.patient)
        # Schedule the arrival of the next ordinary patient
        self._schedule_next_patient()

    @staticmethod
    def _get_surgery_type():
        """
        Determines the type of surgery for the arriving patient based on predefined probabilities.

        Returns:
            PatientSurgery: The type of surgery assigned to the patient.
        """
        r = generator.uniform(0, 1)
        if r <= 0.5:
            return PatientSurgery.SIMPLE  # 50% chance for simple surgery
        elif 0.5 < r <= 0.95:
            return PatientSurgery.MEDIUM  # 45% chance for medium surgery
        else:
            return PatientSurgery.COMPLEX  # 5% chance for complex surgery

    @staticmethod
    def _get_has_heart_problems():
        """
        Determines whether the arriving patient has heart problems based on predefined probability.

        Returns:
            bool: True if the patient has heart problems, False otherwise.
        """
        r = generator.uniform(0, 1)
        if r < 0.75:
            return False  # 75% chance the patient does not have heart problems
        else:
            return True  # 25% chance the patient has heart problems

    def _add_ordinary_patient(self, patient):
        """
        Attempts to add an ordinary patient to a pre-OR bed.

        If the pre-OR beds are full, the patient is rejected. Otherwise, the patient is assigned to a
        pre-OR bed, and the necessary subsequent events are scheduled.

        Args:
            patient (Patient): The patient to be added.

        Returns:
            bool: True if the patient was successfully added, False otherwise.
        """
        if self.system_state.num_occupied_beds_pre_or >= self.system_state.CAPACITY_PRE_OR:
            # Pre-OR beds are full; reject the patient
            return False
        else:
            # Assign the patient to a pre-OR bed
            self.system_state.num_occupied_beds_pre_or += 1
            # Schedule the administrative work completion event for the patient
            self._schedule_ordinary_patient_events(patient)
            return True

    def _schedule_next_patient(self):
        """
        Schedules the arrival of the next ordinary patient based on the interarrival time.
        """
        self.sim_engine.schedule_event(
            event_type=EventTypes.PATIENT_ARRIVAL_ORDINARY,
            event_time=ORDINARY_INTERARRIVAL()
        )

    def _schedule_ordinary_patient_events(self, patient: Patient):
        """
        Schedules the administrative work completion event for an ordinary patient.

        Args:
            patient (Patient): The patient for whom to schedule the event.
        """
        self.sim_engine.schedule_event(
            event_type=EventTypes.ADMIN_WORK_COMPLETED,
            event_time=ADMIN_WORK_ORDINARY(),
            patient=patient
        )

    def _make_patient(self, patient_type, surgery_type, has_heart_problem):
        """
        Creates a new Patient instance with the specified attributes.

        Args:
            patient_type (PatientType): The type of the patient (e.g., ORDINARY).
            surgery_type (PatientSurgery): The type of surgery the patient will undergo.
            has_heart_problem (bool): Indicates whether the patient has heart problems.

        Returns:
            Patient: The newly created patient instance.
        """
        # Retrieve a unique patient ID from the simulation engine's counter
        patient_id = self.sim_engine.counter.get_current_patient_id()
        # Create a new Patient instance with the provided attributes
        patient = Patient(
            patient_id=patient_id,
            enter_time=self.system_state.current_time,
            patient_type=patient_type,
            patient_surgery=surgery_type,
            has_heart_problem=has_heart_problem
        )
        # Record the patient in the analytics data
        self.analytics.patients[patient.patient_id] = patient
        return patient
