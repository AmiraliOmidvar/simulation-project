from activties import OR_COMPLEX, OR_MEDIUM, OR_SIMPLE
from entities.patient import Patient, PatientSurgery, PatientType
from events.base.base import BaseEvent
from events.base.types import EventTypes


class MoveToOr(BaseEvent):
    """
    Handles the movement of a patient to the Operating Room (OR).

    This event is triggered when a patient is ready to be moved to the OR for their surgical procedure.
    It determines whether there are available beds in the OR. If the OR is at full capacity, the patient
    is added to the OR queue. Otherwise, the patient is assigned to an OR bed, and the appropriate
    operation completion event is scheduled based on the complexity of the patient's surgery.

    Attributes:
        patient (Patient): The patient associated with this movement event.
        is_resurgery (bool): Indicates whether the patient is undergoing a resurgery.
    """

    def __init__(self, event_time, system_state, sim_engine, analytics, **kwargs):
        """
        Initializes the MoveToOr event with the given parameters.

        Args:
            event_time (float): The simulation time at which the event is scheduled to occur.
            system_state (SystemState): The current state of the simulation system.
            sim_engine (SimulationEngine): The simulation engine responsible for managing events.
            analytics (AnalyticsData): The analytics component for recording event outcomes.
            **kwargs: Additional keyword arguments. Expected to include 'patient' and optionally 'is_resurgery'.
        """
        super().__init__(event_time, system_state, sim_engine, analytics)
        self.patient: Patient = kwargs.get("patient")  # Retrieve the patient from keyword arguments
        self.is_resurgery = kwargs.get("is_resurgery", False)  # Determine if the patient is undergoing a resurgery

    def execute(self):
        """
        Executes the MoveToOr event.

        This method performs the following actions:
            1. If the patient is undergoing a resurgery, handles the operation accordingly.
            2. If not a resurgery:
                a. Checks if the number of occupied OR beds has reached the OR's capacity.
                b. If the OR is full, adds the patient to the OR queue.
                c. If there is available space:
                    i. Decrements the number of pre-OR occupied beds if the patient is ordinary.
                    ii. Schedules an emergency departure event if the patient is urgent.
                    iii. Handles the operation based on the patient's surgery type.
        """
        if self.is_resurgery:
            # Handle the operation for a resurgery patient
            self._handle_operation()
        else:
            # Check if the Operating Room (OR) has reached its capacity
            if self.system_state.num_occupied_beds_or >= self.system_state.CAPACITY_OR:
                # OR is full; add the patient to the OR queue
                self.system_state.or_queue.push(self.patient)
                return  # Exit the method as the patient has been queued

            # If the patient is ordinary, decrement the count of pre-OR occupied beds
            if self.patient.patient_type == PatientType.ORDINARY:
                self.system_state.num_occupied_beds_pre_or -= 1

            # If the patient is urgent, schedule an emergency departure event
            if self.patient.patient_type == PatientType.URGENT:
                self._schedule_emergency_departure()

            # Handle the operation based on the patient's surgery type
            self._handle_operation()

    def _handle_operation(self):
        """
        Handles the assignment of the patient to an OR bed and schedules the operation completion event.

        This method determines the type of surgery the patient is undergoing and schedules the corresponding
        operation completion event with the appropriate duration.
        """
        # Assign a bed to the patient in the OR
        self.system_state.num_occupied_beds_or += 1

        # Schedule the operation completion event based on the surgery type
        if self.patient.patient_surgery == PatientSurgery.COMPLEX:
            self.sim_engine.schedule_event(
                event_type=EventTypes.OPERATION_COMPLETE,
                event_time=OR_COMPLEX(),  # Duration for a complex surgery
                patient=self.patient
            )
        elif self.patient.patient_surgery == PatientSurgery.MEDIUM:
            self.sim_engine.schedule_event(
                event_type=EventTypes.OPERATION_COMPLETE,
                event_time=OR_MEDIUM(),  # Duration for a medium complexity surgery
                patient=self.patient
            )
        elif self.patient.patient_surgery == PatientSurgery.SIMPLE:
            self.sim_engine.schedule_event(
                event_type=EventTypes.OPERATION_COMPLETE,
                event_time=OR_SIMPLE(),  # Duration for a simple surgery
                patient=self.patient
            )

    def _schedule_emergency_departure(self):
        """
        Schedules an Emergency Departure event for an urgent patient.

        This method is called when an urgent patient needs to depart the system urgently,
        bypassing regular procedures.
        """
        self.sim_engine.schedule_event(
            event_type=EventTypes.EMERGENCY_DEPARTURE,
            event_time=0,  # Immediate departure
            patient=self.patient
        )
