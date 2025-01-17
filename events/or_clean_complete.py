"""
Operating Room Cleanup Completion Event Module

This module defines the OrCleanComplete event, which handles the completion of the cleaning process
in the Operating Room (OR) after a patient's surgery. It ensures that the OR bed is freed up and
assigns the next patient in the OR queue to an available bed by scheduling a MOVE_TO_OR event for them.
"""

from events.base.base import BaseEvent
from events.base.types import EventTypes


class OrCleanComplete(BaseEvent):
    """
    Represents the event that occurs when the Operating Room (OR) cleaning is completed.

    This event is responsible for freeing up an occupied OR bed after a patient's surgery and
    assigning the next patient in the OR queue to the available bed by scheduling a MOVE_TO_OR event.
    """

    def __init__(self, event_time, system_state, sim_engine, analytics, **kwargs):
        """
        Initializes the OrCleanComplete event with the given parameters.

        Args:
            event_time (float): The simulation time at which the OR cleaning is completed.
            system_state (SystemState): The current state of the simulation system.
            sim_engine (SimulationEngine): The simulation engine responsible for managing events.
            analytics (AnalyticsData): The analytics component for recording event outcomes.
            **kwargs: Additional keyword arguments. Not used in this event.
        """
        super().__init__(event_time, system_state, sim_engine, analytics)

    def execute(self):
        """
        Executes the OrCleanComplete event.

        This method performs the following actions:
            1. Decrements the count of occupied OR beds, freeing up a bed after cleanup.
            2. Checks if there are patients waiting in the OR queue.
            3. If the OR queue is not empty, pops the next patient and schedules a MOVE_TO_OR event
               for them with an immediate event time.
        """
        # Decrement the number of occupied OR beds as cleanup is complete
        self.system_state.num_occupied_beds_or -= 1

        # Check if there are patients waiting in the OR queue
        if not self.system_state.or_queue.is_empty():
            # Retrieve the next patient from the OR queue
            next_patient = self.system_state.or_queue.pop()
            # Schedule a MOVE_TO_OR event for the next patient with an immediate event time
            self.sim_engine.schedule_event(
                event_type=EventTypes.MOVE_TO_OR,
                event_time=0,  # Immediate event
                patient=next_patient
            )
