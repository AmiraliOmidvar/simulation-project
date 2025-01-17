"""
Patient Arrival Urgent Event Module

This module defines the PatientArrivalUrgentEvent class, which handles the arrival of urgent patients
in the simulation. It manages both individual urgent patient arrivals and rare mass casualty events,
creates patient instances with appropriate attributes, assigns them to emergency beds if available,
and schedules the necessary subsequent events such as administrative work completion and the arrival
of future urgent patients.
"""

from activties import ADMIN_WORK_URGENT, URGENT_INTERARRIVAL
from entities.patient import Patient, PatientSurgery, PatientType
from events.base.base import BaseEvent
from events.base.types import EventTypes
from utils.number_generator import Generator

# Initialize the random number generator instance
generator = Generator()


class PatientArrivalUrgentEvent(BaseEvent):
    """
    Handles the arrival of urgent patients to the simulation.

    This event is triggered when an urgent patient arrives at the simulation. It determines whether the
    arrival is a regular urgent patient or part of a mass casualty event. For each arriving patient,
    it determines the surgery type and whether the patient has heart problems, creates a Patient instance,
    assigns them to an emergency bed if available, and schedules the necessary subsequent events. It also
    schedules the arrival of the next urgent patient.

    Attributes:
        patient (Patient): The patient associated with this arrival event.
    """

    def __init__(self, event_time, system_state, sim_engine, analytics, **kwargs):
        """
        Initializes the PatientArrivalUrgentEvent with the given parameters.

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
        Executes the PatientArrivalUrgentEvent.

        This method performs the following actions:
            1. Checks if the arrival is part of a mass casualty event.
                - If yes, handles the arrival of a group of urgent patients.
            2. For each regular urgent patient:
                a. Determines the surgery type and whether the patient has heart problems.
                b. Creates a Patient instance with the determined attributes.
                c. Attempts to add the patient to an emergency bed.
            3. Schedules the arrival of the next urgent patient.
        """
        # Check if this is a mass casualty event with a 0.5% probability
        if self._is_mass_casualty_event():
            group_size = generator.randint(2, 5)  # Random group size between 2 and 5
            self._handle_mass_casualty_event(group_size)

        # Determine the type of surgery and whether the patient has heart problems
        surgery_type = self._get_surgery_type()
        has_heart_problem = self._get_has_heart_problems()

        # Create a new urgent Patient instance with the determined attributes
        self.patient = self._make_patient(PatientType.URGENT, surgery_type, has_heart_problem)
        # Attempt to add the urgent patient to an emergency bed
        self._add_urgent_patient(self.patient)
        # Schedule the arrival of the next urgent patient
        self._schedule_next_patient()

    def _handle_mass_casualty_event(self, group_size: int):
        """
        Handles the arrival of a group of urgent patients during a mass casualty event.

        Args:
            group_size (int): The number of patients arriving in the mass casualty event.
        """
        for i in range(group_size):
            # Determine the type of surgery for each patient
            surgery_type = self._get_surgery_type()
            # Assume mass casualty patients do not have heart problems
            patient = self._make_patient(PatientType.URGENT, surgery_type, False)
            # Attempt to add each patient to an emergency bed
            if not self._add_urgent_patient(patient):
                # If unable to add a patient, stop processing the remaining patients in the group
                break

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
        return r >= 0.75  # 25% chance the patient has heart problems

    @staticmethod
    def _is_mass_casualty_event():
        """
        Determines whether the current arrival is part of a mass casualty event.

        Returns:
            bool: True if it's a mass casualty event, False otherwise.
        """
        r = generator.uniform(0, 1)
        return r < 0.005  # 0.5% chance of a mass casualty event

    def _add_urgent_patient(self, patient):
        """
        Attempts to add an urgent patient to an emergency bed.

        If the emergency department (ER) is full, the patient is added to the emergency queue
        if there is available space. Otherwise, the patient is rejected. The method also updates
        analytics data to indicate whether the emergency department is full at the time of arrival.

        Args:
            patient (Patient): The patient to be added.

        Returns:
            bool: True if the patient was successfully added or queued, False if rejected.
        """
        if self.system_state.num_occupied_beds_emergency >= self.system_state.CAPACITY_ER:
            # Emergency department is full
            self.analytics.emergency_is_full[self.system_state.current_time] = True
            if len(self.system_state.emergency_queue) >= self.system_state.CAPACITY_AMBULANCE:
                # Emergency queue is also full; reject the patient
                return False
            else:
                # Add the patient to the emergency queue
                self.system_state.emergency_queue.push(patient)
                return True
        else:
            # Emergency department has available beds
            self.analytics.emergency_is_full[self.system_state.current_time] = False
            self.system_state.num_occupied_beds_emergency += 1
            # Schedule the administrative work completion event for the patient
            self._schedule_urgent_patient_events(patient)
            return True

    def _schedule_urgent_patient_events(self, patient: Patient):
        """
        Schedules the administrative work completion event for an urgent patient.

        Args:
            patient (Patient): The patient for whom to schedule the event.
        """
        self.sim_engine.schedule_event(
            event_type=EventTypes.ADMIN_WORK_COMPLETED,
            event_time=ADMIN_WORK_URGENT(),
            patient=patient
        )

    def _schedule_next_patient(self):
        """
        Schedules the arrival of the next urgent patient based on the interarrival time.
        """
        self.sim_engine.schedule_event(
            event_type=EventTypes.PATIENT_ARRIVAL_URGENT,
            event_time=URGENT_INTERARRIVAL()
        )

    def _make_patient(self, patient_type, surgery_type, has_heart_problem):
        """
        Creates a new Patient instance with the specified attributes.

        Args:
            patient_type (PatientType): The type of the patient (e.g., URGENT).
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
        # Record the patient in the analytics data for tracking
        self.analytics.patients[patient.patient_id] = patient
        return patient
