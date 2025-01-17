import heapq

from activties import ORDINARY_INTERARRIVAL, URGENT_INTERARRIVAL
from analytics import Analyst, AnalyticsData
from config import SEED_LIST, SIMULATION_TIME
from events.base.base import BaseEvent
from events.base.registry import registry
from events.base.types import EventTypes
from system_state import SystemState
from utils.counters import Counters
from utils.logger import SimulationLogger
from utils.number_generator import Generator


class SimulationEngine:
    """
    Processes events in chronological order and provides an initialization step.
    """

    def __init__(self, end_time=20000):
        self.generator = Generator()
        self.system_state = SystemState()
        self.analytics = AnalyticsData()
        self.end_time = end_time
        self.event_queue = []
        self.counter = Counters()
        self.logger = SimulationLogger()

    def initialize(self):
        """
        Initialization phase to set up the simulation environment.
        Schedules initial events.
        """
        print("Initializing simulation...")

        # Schedule the first patient arrival at time=0

        self.schedule_event(event_type=EventTypes.PATIENT_ARRIVAL_URGENT, event_time=ORDINARY_INTERARRIVAL())
        self.schedule_event(event_type=EventTypes.PATIENT_ARRIVAL_ORDINARY, event_time=URGENT_INTERARRIVAL())

        # Schedule the first power outage at a random time
        first_outage_time = self.generator.uniform(0, 1440)
        self.schedule_event(event_type=EventTypes.POWER_OUT, event_time=first_outage_time)

    def schedule_event(self, event_type: EventTypes, event_time, **kwargs):
        """
        Insert event into the future event list (priority queue).
        """
        event_class = registry[event_type]
        event = event_class(
            event_time=self.system_state.current_time + event_time, system_state=self.system_state, sim_engine=self,
            analytics=self.analytics, **kwargs
        )
        heapq.heappush(self.event_queue, event)

    def run(self):
        """
        Repeatedly pop the earliest event and process it,
        until we have no events or we exceed end_time.
        """
        print("Starting simulation...")
        while self.event_queue:
            if self.system_state.current_time > self.end_time:
                break

            # Pop from the queue
            current_event: BaseEvent = heapq.heappop(self.event_queue)

            # Advance simulation clock
            self.system_state.current_time = current_event.time

            # Execute event
            current_event.execute()
            self.analytics.update(self.system_state)

            # Log
            # self.logger.log_event(
            #     event_name=current_event.name, time=current_event.time, patient=current_event.patient_id,
            #     patient_type=current_event.patient_type, patient_surgery=current_event.patient_surgery, details=None
            # )
            # self.logger.log_state(self.system_state, current_event.time)
            self.logger.trace(
                event_name=current_event.name, event_time=current_event.time, patient=current_event.patient_id,
                patient_type=current_event.patient_type, patient_surgery=current_event.patient_surgery,
                system_state=self.system_state, event_details=None
            )

        self.analytics.end_update(self.system_state)
        print("Simulation has finished.")
        print(f"Final: {self.system_state}")


def run_simulation():
    sim = SimulationEngine(end_time=SIMULATION_TIME)
    sim.initialize()
    sim.run()
    return sim.analytics


if __name__ == "__main__":
    dataset = []
    for i, seed in enumerate([6534534]):
        Generator.reset(seed)
        data = run_simulation()
        dataset.append(data)

    analyst = Analyst(dataset)
    print(analyst.run_analytics())
