from typing import Protocol, Union

from events.base.types import EventTypes
from utils.counters import Counters


class SimulationEngine(Protocol):
    counter: Counters

    def schedule_event(self, event_type: EventTypes, event_time: Union[int, float], **kwargs) -> bool:
        pass
