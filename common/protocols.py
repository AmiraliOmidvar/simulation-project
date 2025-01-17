from typing import Protocol

from events.base.types import EventTypes
from utils.counters import Counters


class SimulationEngine(Protocol):
    counter: Counters

    def schedule_event(self, event_type: EventTypes, event_time: int, **kwargs) -> bool:
        pass
