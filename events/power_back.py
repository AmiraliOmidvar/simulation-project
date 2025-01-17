"""
Power Restoration Event Module

This module defines the PowerBack event, which handles the restoration of power within the simulation.
When power is restored, it updates the system state to reflect that power is back and adjusts the
capacities of critical care units such as the Critical Care Unit (CCU) and Intensive Care Unit (ICU).
"""

from events.base.base import BaseEvent


class PowerBack(BaseEvent):
    """
    Represents the event that occurs when power is restored to the system.

    This event is responsible for updating the system state to indicate that power is back and
    adjusting the capacities of the Critical Care Unit (CCU) and Intensive Care Unit (ICU) accordingly.
    Typically, this event would follow a PowerOutage event, restoring full operational capacity.
    """

    def __init__(self, event_time, system_state, sim_engine, analytics, **kwargs):
        """
        Initializes the PowerBack event with the given parameters.

        Args:
            event_time (float): The simulation time at which power is restored.
            system_state (SystemState): The current state of the simulation system.
            sim_engine (SimulationEngine): The simulation engine responsible for managing events.
            analytics (AnalyticsData): The analytics component for recording event outcomes.
            **kwargs: Additional keyword arguments. Not used in this event.
        """
        super().__init__(event_time, system_state, sim_engine, analytics)

    def execute(self):
        """
        Executes the PowerBack event.

        This method performs the following actions:
            1. Updates the system state to indicate that power is restored.
            2. Restores the capacities of the CCU and ICU to their original values by dividing the
               current capacities by 0.8 (assuming they were reduced to 80% during a power outage).
        """
        # Update the power status to indicate that power is restored
        self.system_state.power_status = 1  # 1 signifies power is on

        # Restore the capacities of CCU and ICU to their original values
        # Assuming that during a power outage, capacities were reduced to 80%
        self.system_state.CAPACITY_CCU = int(self.system_state.CAPACITY_CCU / 0.8)
        self.system_state.CAPACITY_ICU = int(self.system_state.CAPACITY_ICU / 0.8)
