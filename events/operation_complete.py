from activties import CCU_STAY, GENERAL_STAY, ICU_STAY, OR_CLEAN_UP
from entities.patient import Patient, PatientSurgery
from events.base.base import BaseEvent
from events.base.types import EventTypes
from utils.number_generator import Generator

# Initialize the random number generator instance
generator = Generator()


class OperationComplete(BaseEvent):
    """
    Handles the completion of an operation for a patient.

    This event is triggered when a patient's surgical procedure is completed. Depending on the
    type and complexity of the surgery, it may schedule subsequent events such as resurgeries,
    emergency departures, or moving the patient to different wards like CCU or ICU. It also
    manages the cleanup process after the operation.

    Attributes:
        patient (Patient): The patient associated with this operation completion event.
    """

    def __init__(self, event_time, system_state, sim_engine, analytics, **kwargs):
        """
        Initializes the OperationComplete event with the given parameters.

        Args:
            event_time (float): The simulation time at which the operation is completed.
            system_state (SystemState): The current state of the simulation system.
            sim_engine (SimulationEngine): The simulation engine responsible for managing events.
            analytics (AnalyticsData): The analytics component for recording event outcomes.
            **kwargs: Additional keyword arguments. Expected to include 'patient'.
        """
        super().__init__(event_time, system_state, sim_engine, analytics)
        self.patient: Patient = kwargs.get("patient")  # Retrieve the patient from keyword arguments

    def execute(self):
        """
        Executes the OperationComplete event.

        This method determines the type of surgery the patient underwent and handles the
        post-operation process accordingly. It may schedule events for resurgeries, record
        patient exits due to death, or move the patient to the CCU or ICU based on their health
        conditions.
        """
        # Determine the type of surgery and handle accordingly
        if self.patient.patient_surgery == PatientSurgery.COMPLEX:
            self._handle_complex()

        if self.patient.patient_surgery == PatientSurgery.MEDIUM:
            self._handle_medium()

        if self.patient.patient_surgery == PatientSurgery.SIMPLE:
            self._handle_simple()

    def _schedule_cleanup_complete_event(self):
        """
        Schedules the cleanup completion event after an operation.

        This event signifies that the cleaning process in the Operating Room (OR) has been completed.
        """
        self.sim_engine.schedule_event(
            event_type=EventTypes.OR_CLEAN_UP_COMPLETE,
            event_time=OR_CLEAN_UP(),
            patient=self.patient
        )

    def _handle_complex(self):
        """
        Handles post-operation procedures for complex surgeries.

        This method manages the possibility of a resurgery and records patient mortality.
        It also moves the patient to the CCU or ICU based on their health conditions.
        """
        # Determine if the patient requires a resurgery
        r = generator.uniform(0, 1)
        if r < 0.01:
            # Schedule a resurgery event and mark the patient as having undergone resurgery
            self.sim_engine.schedule_event(
                event_type=EventTypes.MOVE_TO_OR,
                event_time=OR_CLEAN_UP(),
                patient=self.patient,
                is_resurgery=True
            )
            self.analytics.resurgery[self.patient.patient_id] = True
            return
        else:
            # Mark the patient as not having undergone resurgery if not already recorded
            if self.patient.patient_id not in self.analytics.resurgery:
                self.analytics.resurgery[self.patient.patient_id] = False

        # Determine if the patient dies post-operation
        r = generator.uniform(0, 1)
        if r < 0.1:
            # Record the patient's exit time due to death and schedule cleanup
            self.analytics.patients[self.patient.patient_id].exit_time = self.system_state.current_time
            self._schedule_cleanup_complete_event()
            return

        # Move the patient to CCU or ICU based on heart problems
        if self.patient.has_heart_problem:
            if self.system_state.num_occupied_beds_ccu >= self.system_state.CAPACITY_CCU:
                # If CCU is full, add the patient to the CCU queue
                self.system_state.ccu_queue.push(self.patient)
            else:
                # If CCU has available beds, assign the patient to CCU
                self._add_to_ccu()
        else:
            if self.system_state.num_occupied_beds_icu >= self.system_state.CAPACITY_ICU:
                # If ICU is full, add the patient to the ICU queue
                self.system_state.icu_queue.push(self.patient)
            else:
                # If ICU has available beds, assign the patient to ICU
                self._add_to_icu()

    def _handle_medium(self):
        """
        Handles post-operation procedures for medium complexity surgeries.

        This method randomly determines the next steps for the patient, which may include
        moving to the General Ward, ICU, or CCU based on predefined probabilities and bed availability.
        """
        # Determine the next step based on a random probability
        r = generator.uniform(0, 1)
        if r < 0.7:
            if self.system_state.num_occupied_beds_general >= self.system_state.CAPACITY_GENERAL:
                # If General Ward is full, add the patient to the general queue
                self.system_state.general_queue.push(self.patient)
            else:
                # If General Ward has available beds, assign the patient to General Ward
                self._add_to_general()
        elif 0.7 < r < 0.8:
            if self.system_state.num_occupied_beds_icu >= self.system_state.CAPACITY_ICU:
                # If ICU is full, add the patient to the ICU queue
                self.system_state.icu_queue.push(self.patient)
            else:
                # If ICU has available beds, assign the patient to ICU
                self._add_to_icu()
        else:
            if self.system_state.num_occupied_beds_ccu >= self.system_state.CAPACITY_CCU:
                # If CCU is full, add the patient to the CCU queue
                self.system_state.ccu_queue.push(self.patient)
            else:
                # If CCU has available beds, assign the patient to CCU
                self._add_to_ccu()

    def _handle_simple(self):
        """
        Handles post-operation procedures for simple surgeries.

        This method assigns the patient to the General Ward or queues them if the ward is at full capacity.
        """
        if self.system_state.num_occupied_beds_general >= self.system_state.CAPACITY_GENERAL:
            # If General Ward is full, add the patient to the general queue
            self.system_state.general_queue.push(self.patient)
        else:
            # If General Ward has available beds, assign the patient to General Ward
            self._add_to_general()

    def _add_to_ccu(self):
        """
        Assigns the patient to the Critical Care Unit (CCU) and schedules their departure.

        This method updates the system state to reflect the new occupancy in CCU and schedules
        a CCU departure event based on the CCU stay duration.
        """
        self.system_state.num_occupied_beds_ccu += 1  # Increment occupied CCU beds count
        self.system_state.ccu_patients.append(self.patient)  # Add patient to CCU patients list
        self.sim_engine.schedule_event(
            event_type=EventTypes.CCU_DEPARTURE,
            event_time=CCU_STAY(),
            patient=self.patient
        )
        self._schedule_cleanup_complete_event()  # Schedule cleanup after CCU assignment

    def _add_to_icu(self):
        """
        Assigns the patient to the Intensive Care Unit (ICU) and schedules their departure.

        This method updates the system state to reflect the new occupancy in ICU and schedules
        an ICU departure event based on the ICU stay duration.
        """
        self.system_state.num_occupied_beds_icu += 1  # Increment occupied ICU beds count
        self.system_state.icu_patients.append(self.patient)  # Add patient to ICU patients list
        self.sim_engine.schedule_event(
            event_type=EventTypes.ICU_DEPARTURE,
            event_time=ICU_STAY(),
            patient=self.patient
        )
        self._schedule_cleanup_complete_event()  # Schedule cleanup after ICU assignment

    def _add_to_general(self):
        """
        Assigns the patient to the General Ward and schedules their departure.

        This method updates the system state to reflect the new occupancy in the General Ward and schedules
        a General Ward departure event based on the General Ward stay duration.
        """
        self.system_state.num_occupied_beds_general += 1  # Increment occupied General Ward beds count
        self.sim_engine.schedule_event(
            event_type=EventTypes.GENERAL_DEPARTURE,
            event_time=GENERAL_STAY(),
            patient=self.patient
        )
        self._schedule_cleanup_complete_event()  # Schedule cleanup after General Ward assignment
