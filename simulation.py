import heapq
import time

from dotenv import load_dotenv

load_dotenv("improved_2.env")

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
    SimulationEngine processes events in chronological order and manages the simulation lifecycle.

    Attributes:
        generator (Generator): Generates random numbers for simulation events.
        system_state (SystemState): Represents the current state of the system being simulated.
        analytics (AnalyticsData): Collects and stores data for post-simulation analysis.
        end_time (int): The time at which the simulation will terminate.
        event_queue (list): Priority queue (heap) that stores scheduled events.
        counter (Counters): Keeps track of various counters during the simulation.
        logger (SimulationLogger): Handles logging of simulation events and states.
    """

    def __init__(self, end_time=20000):
        """
        Initializes the SimulationEngine with default or specified end time.

        Args:
            end_time (int, optional): The simulation will stop after this time. Defaults to 20000.
        """
        self.generator = Generator()
        self.system_state = SystemState()
        self.analytics = AnalyticsData()
        self.end_time = end_time
        self.event_queue = []
        self.counter = Counters()
        # self.logger = SimulationLogger()

    def initialize(self):
        """
        Sets up the initial state of the simulation by scheduling the first set of events.

        - Schedules the first urgent patient arrival.
        - Schedules the first ordinary patient arrival.
        - Schedules the first power outage at a random time within the first day (1440 minutes).
        """
        print("Initializing simulation...")

        # Schedule the first urgent patient arrival event
        urgent_interarrival_time = URGENT_INTERARRIVAL()
        self.schedule_event(
            event_type=EventTypes.PATIENT_ARRIVAL_URGENT,
            event_time=urgent_interarrival_time
        )

        # Schedule the first ordinary patient arrival event
        ordinary_interarrival_time = ORDINARY_INTERARRIVAL()
        self.schedule_event(
            event_type=EventTypes.PATIENT_ARRIVAL_ORDINARY,
            event_time=ordinary_interarrival_time
        )

        # Schedule the first power outage event at a random time within the first day
        first_outage_time = self.generator.uniform(0, 1440)
        self.schedule_event(
            event_type=EventTypes.POWER_OUT,
            event_time=first_outage_time
        )

    def schedule_event(self, event_type: EventTypes, event_time, **kwargs):
        """
        Schedules a new event by adding it to the event queue (priority queue).

        Args:
            event_type (EventTypes): The type of the event to be scheduled.
            event_time (float): The time at which the event should occur, relative to current time.
            **kwargs: Additional keyword arguments required to instantiate the event.
        """
        # Retrieve the event class from the registry based on event type
        event_class = registry[event_type]

        # Calculate the absolute event time by adding relative time to current simulation time
        absolute_event_time = self.system_state.current_time + event_time

        # Instantiate the event with necessary parameters
        event = event_class(
            event_time=absolute_event_time,
            system_state=self.system_state,
            sim_engine=self,
            analytics=self.analytics,
            **kwargs
        )

        # Push the event onto the priority queue
        heapq.heappush(self.event_queue, (event.time, event))

    def run(self):
        """
        Executes the simulation by processing events in chronological order until the event queue is empty
        or the simulation reaches the specified end time.
        """
        print("Starting simulation...")

        # Continue processing until there are no more events or end_time is reached
        while self.event_queue:
            # Check if the current simulation time has exceeded the end time
            if self.system_state.current_time > self.end_time:
                print(f"Reached end time: {self.end_time}. Stopping simulation.")
                break

            # Pop the earliest event from the priority queue
            event_tuple: BaseEvent = heapq.heappop(self.event_queue)
            event_time, current_event = event_tuple[0], event_tuple[1]

            # Advance the simulation clock to the time of the current event
            self.system_state.current_time = current_event.time

            # Execute the event's specific behavior
            current_event.execute()

            # Update analytics data based on the new system state
            self.analytics.update(self.system_state)

            # Log the event and current state using the SimulationLogger
            # self.logger.trace(
            #     event_name=current_event.name,
            #     event_time=current_event.time,
            #     patient=current_event.patient_id,
            #     patient_type=current_event.patient_type,
            #     patient_surgery=current_event.patient_surgery,
            #     system_state=self.system_state,
            #     event_details=None  # Additional details can be added if necessary
            # )

        # Perform any final updates to analytics after simulation ends
        self.analytics.end_update(self.system_state)
        print("Simulation has finished.")
        print(f"Final system state: {self.system_state}")


def run_simulation():
    """
    Sets up and runs a single instance of the simulation.

    Returns:
        AnalyticsData: The analytics data collected during the simulation.
    """
    # Instantiate the simulation engine with the configured simulation time
    sim = SimulationEngine(end_time=SIMULATION_TIME)

    # Initialize the simulation by scheduling initial events
    sim.initialize()

    # Run the simulation
    sim.run()

    # Return the collected analytics data for further analysis
    return sim.analytics


def run_simulation_for_seed(seed=6543434):
    """
    Helper function to reset the Generator with a given seed and run the simulation.
    Returns the collected simulation data.
    """
    print(f"Running simulation with seed {seed}...")
    Generator.reset(seed)
    data = run_simulation()
    return data


if __name__ == "__main__":
    st = time.time()
    from multiprocessing import Pool

    """
    Entry point for running the simulation in parallel.
    Executes the simulation for each seed in SEED_LIST using multiple processes,
    collects analytics data, and performs analysis across all simulation runs.
    """

    # Use a process pool to run simulations for each seed in parallel
    with Pool(processes=3) as pool:
        dataset = pool.map(run_simulation_for_seed, SEED_LIST)

    # Create an Analyst instance with the collected dataset
    analyst = Analyst(dataset)

    # Perform and print the analytics results
    print("Running analytics on simulation data...")
    analytics_results = analyst.run_analytics()
    print(analytics_results)
    print(time.time() - st)
