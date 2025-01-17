"""
Power Outage Event Module

This module defines the PowerOut event, which handles power outage scenarios within the simulation.
When a power outage occurs, it updates the system state to reflect the loss of power, reduces the
capacities of critical care units (CCU and ICU), removes any patients exceeding the new capacities,
and schedules subsequent power outage and restoration events.
"""

from events.base.base import BaseEvent
from events.base.types import EventTypes
from utils.number_generator import Generator

# Initialize the random number generator instance
generator = Generator()


class PowerOut(BaseEvent):
    """
    Represents the event that occurs when a power outage happens in the system.

    This event is responsible for updating the system state to indicate that power is lost,
    reducing the capacities of the Critical Care Unit (CCU) and Intensive Care Unit (ICU) by 20%,
    removing any patients that exceed the new capacities, and scheduling the next power outage
    and the restoration of power.
    """

    def __init__(self, event_time, system_state, sim_engine, analytics, **kwargs):
        """
        Initializes the PowerOut event with the given parameters.

        Args:
            event_time (float): The simulation time at which the power outage occurs.
            system_state (SystemState): The current state of the simulation system.
            sim_engine (SimulationEngine): The simulation engine responsible for managing events.
            analytics (AnalyticsData): The analytics component for recording event outcomes.
            **kwargs: Additional keyword arguments. Not used in this event.
        """
        super().__init__(event_time, system_state, sim_engine, analytics)

    def execute(self):
        """
        Executes the PowerOut event.

        This method performs the following actions:
            1. Updates the system state to indicate that power is lost.
            2. Reduces the capacities of the CCU and ICU by 20%.
            3. Removes any patients from the CCU and ICU that exceed the new capacities.
            4. Schedules the next power outage event.
            5. Schedules the power restoration (PowerBack) event.
        """
        # Indicate that power is now off
        self.system_state.power_status = 0

        # Reduce the capacities of CCU and ICU by 20%
        self.system_state.CAPACITY_CCU = int(self.system_state.CAPACITY_CCU * 0.8)
        self.system_state.CAPACITY_ICU = int(self.system_state.CAPACITY_ICU * 0.8)

        # Remove patients exceeding the new capacities in CCU and ICU
        self._remove_overflow_patients()

        # Schedule the next power outage event
        self._schedule_next_power_out()

        # Schedule the power restoration (PowerBack) event
        self._schedule_power_back()

    def _remove_overflow_patients(self):
        """
        Removes patients from the CCU and ICU if the number of occupied beds exceeds the new capacities.

        This method ensures that the number of patients in each unit does not exceed the reduced capacities
        by removing excess patients from the CCU and ICU patient lists.
        """
        # Remove excess patients from the CCU
        while self.system_state.num_occupied_beds_ccu >= self.system_state.CAPACITY_CCU:
            self.system_state.num_occupied_beds_ccu -= 1
            removed_patient = self.system_state.ccu_patients.pop()
            # Optionally, handle the removed patient (e.g., transfer to another unit or discharge)

        # Remove excess patients from the ICU
        while self.system_state.num_occupied_beds_icu >= self.system_state.CAPACITY_ICU:
            self.system_state.num_occupied_beds_icu -= 1
            removed_patient = self.system_state.icu_patients.pop()
            # Optionally, handle the removed patient (e.g., transfer to another unit or discharge)

    def _schedule_next_power_out(self):
        """
        Schedules the next power outage event.

        This method calculates the time for the next power outage based on a monthly cycle and schedules
        a new PowerOut event using a uniform distribution within the next month's timeframe.
        """
        # Define the length of a month in simulation time units (e.g., minutes)
        month_length = 43200  # Example: 30 days * 24 hours/day * 60 minutes/hour

        # Calculate the simulation time corresponding to the start of the next month
        next_month = self.system_state.current_time - self.system_state.current_time % month_length + month_length

        # Determine the inter-outage time using a uniform distribution between next_month and the end of the next month
        inter_outage = generator.uniform(next_month, next_month + month_length)

        # Schedule the next PowerOut event
        self.sim_engine.schedule_event(
            event_type=EventTypes.POWER_OUT,
            event_time=inter_outage
        )

    def _schedule_power_back(self):
        """
        Schedules the power restoration (PowerBack) event.

        This method schedules a PowerBack event to occur after a fixed duration (e.g., 1440 simulation time units).
        """
        # Define the duration until power is restored (e.g., 1 day * 1440 minutes/day)
        restoration_delay = 1440  # Example: 1 day

        # Schedule the PowerBack event
        self.sim_engine.schedule_event(
            event_type=EventTypes.POWER_BACK,
            event_time=restoration_delay
        )
