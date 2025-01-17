import atexit
import csv
import json
import os
import threading

import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)  # Initialize colorama for colored terminal output


class SimulationLogger:
    """
    Handles logging of simulation events, system states, and trace information.

    This class provides mechanisms to log various aspects of the simulation, including events,
    system states, and detailed trace information. Logs are buffered and periodically flushed
    to their respective files to optimize performance. Additionally, the logger ensures that
    all logs are flushed upon program exit.

    Attributes:
        MAX_BUFFER_SIZE (int): The maximum number of log entries to buffer before flushing.
        log_file (str): Path to the JSON file where event logs are stored.
        state_file (str): Path to the JSON file where state logs are stored.
        trace_file (str): Path to the CSV file where trace logs are stored.
        event_buffer (list): Buffer to store event logs before flushing.
        state_buffer (list): Buffer to store state logs before flushing.
        trace_buffer (list): Buffer to store trace logs before flushing.
        lock (threading.Lock): A lock to ensure thread-safe operations on buffers.
        trace_fieldnames (list): CSV headers for the trace log file.
    """

    MAX_BUFFER_SIZE = 50  # Maximum number of logs before auto-flushing

    def __init__(
            self,
            log_file="simulation_logs.json",
            state_file="state_logs.json",
            trace_file="trace_logs.csv"
    ):
        """
        Initializes the SimulationLogger by setting up log files and buffers.

        Args:
            log_file (str, optional): Filename for event logs. Defaults to "simulation_logs.json".
            state_file (str, optional): Filename for state logs. Defaults to "state_logs.json".
            trace_file (str, optional): Filename for trace logs. Defaults to "trace_logs.csv".
        """
        self.log_file = log_file
        self.state_file = state_file
        self.trace_file = trace_file

        self.event_buffer = []
        self.state_buffer = []
        self.trace_buffer = []

        self.lock = threading.Lock()  # Ensures thread-safe access to buffers

        # Remove existing logs to start fresh
        for file_path in [self.log_file, self.state_file, self.trace_file]:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Removed existing log file: {file_path}")

        # Define CSV headers for trace logs
        self.trace_fieldnames = [
            "event_name",
            "event_time",
            "patient",
            "patient_type",
            "patient_surgery",
            "event_details",
            "system_time",
            "lab_queue",
            "emergency_queue",
            "or_queue",
            "ccu_queue",
            "icu_queue",
            "general_queue",
            "occupied_beds_general",
            "occupied_beds_or",
            "occupied_beds_emergency",
            "occupied_beds_lab",
            "occupied_beds_icu",
            "occupied_beds_ccu",
            "occupied_beds_pre_or",
            "power_status",
        ]
        # Initialize the CSV trace file with headers
        with open(self.trace_file, "w", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=self.trace_fieldnames)
            writer.writeheader()

        # Ensure that buffers are flushed when the program exits
        atexit.register(self.flush)

    def log_event(self, event_name, time, patient, patient_type, patient_surgery, details):
        """
        Logs an event by adding it to the event buffer.

        Args:
            event_name (str): Name of the event.
            time (float): Simulation time when the event occurred.
            patient (int): Identifier for the patient involved in the event.
            patient_type (str): Type/category of the patient.
            patient_surgery (str): Surgery details related to the patient, if any.
            details (Any): Additional details about the event.
        """
        event = {
            "event_name": event_name,
            "time": time,
            "patient": patient,
            "patient_type": patient_type,
            "patient_surgery": patient_surgery,
            "details": details
        }

        with self.lock:
            self.event_buffer.append(event)
            buffer_size = len(self.event_buffer)

            # Print a colored log message to the console for real-time monitoring
            print(
                Fore.GREEN + "Event Logged: " +
                Fore.CYAN + f"[Event Name: {Fore.YELLOW}{event['event_name']}" +
                Fore.CYAN + f", Time: {Fore.YELLOW}{event['time']}" +
                Fore.CYAN + f", Patient: {Fore.YELLOW}{event['patient']}" +
                Fore.CYAN + f", Details: {Fore.YELLOW}{event['details']}" +
                Fore.CYAN + "]" + Style.RESET_ALL
            )

            # Automatically flush buffers if the buffer size exceeds the threshold
            if buffer_size >= self.MAX_BUFFER_SIZE:
                self.flush()

    def log_state(self, system_state, time):
        """
        Logs the current system state by adding it to the state buffer.

        Args:
            system_state (SystemState): The current state of the system.
            time (float): Simulation time when the state is recorded.
        """
        state = {
            "timestamp": time,
            "current_time": system_state.current_time,
            "queues": {
                "lab_queue": len(system_state.lab_queue),
                "emergency_queue": len(system_state.emergency_queue),
                "or_queue": len(system_state.or_queue),
                "ccu_queue": len(system_state.ccu_queue),
                "icu_queue": len(system_state.icu_queue),
                "general_queue": len(system_state.general_queue),
            },
            "occupied_beds": {
                "general": int(system_state.num_occupied_beds_general),
                "or": int(system_state.num_occupied_beds_or),
                "emergency": int(system_state.num_occupied_beds_emergency),
                "lab": int(system_state.num_occupied_beds_lab),
                "icu": int(system_state.num_occupied_beds_icu),
                "ccu": int(system_state.num_occupied_beds_ccu),
                "pre_or": int(system_state.num_occupied_beds_pre_or),
            },
            "power_status": system_state.power_status
        }

        with self.lock:
            self.state_buffer.append(state)

            # Automatically flush buffers if the buffer size exceeds the threshold
            if len(self.state_buffer) >= self.MAX_BUFFER_SIZE:
                self.flush()

    def trace(
            self,
            event_name,
            event_time,
            patient,
            patient_type,
            patient_surgery,
            event_details,
            system_state
    ):
        """
        Logs a combined trace of an event and the current system state.

        This method creates a comprehensive log entry that includes both event-specific
        information and the overall system state at the time of the event.

        Args:
            event_name (str): Name of the event.
            event_time (float): Simulation time when the event occurred.
            patient (int): Identifier for the patient involved in the event.
            patient_type (str): Type/category of the patient.
            patient_surgery (str): Surgery details related to the patient, if any.
            event_details (Any): Additional details about the event.
            system_state (SystemState): The current state of the system.
        """
        # Combine the event information and system state into a single trace entry
        trace_row = {
            "event_name": event_name,
            "event_time": event_time,
            "patient": patient,
            "patient_type": patient_type,
            "patient_surgery": patient_surgery,
            "event_details": event_details,
            "system_time": system_state.current_time,  # Current simulation time
            "lab_queue": len(system_state.lab_queue),
            "emergency_queue": len(system_state.emergency_queue),
            "or_queue": len(system_state.or_queue),
            "ccu_queue": len(system_state.ccu_queue),
            "icu_queue": len(system_state.icu_queue),
            "general_queue": len(system_state.general_queue),
            "occupied_beds_general": int(system_state.num_occupied_beds_general),
            "occupied_beds_or": int(system_state.num_occupied_beds_or),
            "occupied_beds_emergency": int(system_state.num_occupied_beds_emergency),
            "occupied_beds_lab": int(system_state.num_occupied_beds_lab),
            "occupied_beds_icu": int(system_state.num_occupied_beds_icu),
            "occupied_beds_ccu": int(system_state.num_occupied_beds_ccu),
            "occupied_beds_pre_or": int(system_state.num_occupied_beds_pre_or),
            "power_status": system_state.power_status,
        }

        with self.lock:
            self.trace_buffer.append(trace_row)

            # Automatically flush buffers if the buffer size exceeds the threshold
            if len(self.trace_buffer) >= self.MAX_BUFFER_SIZE:
                self.flush()

    def flush(self):
        """
        Flushes the event, state, and trace buffers to their respective log files.

        This method writes all buffered log entries to disk, ensuring that no logs are lost
        in the event of a crash or unexpected termination. After flushing, the buffers are cleared.
        """
        # Flush event buffer to JSON log file
        if self.event_buffer:
            try:
                with open(self.log_file, "a") as file:  # Append mode
                    for event in self.event_buffer:
                        file.write(json.dumps(event) + "\n")  # Each event on a new line
                print(
                    Fore.YELLOW + f"Flushed {len(self.event_buffer)} events"
                    + Style.RESET_ALL
                )
                self.event_buffer.clear()
            except Exception as e:
                print(Fore.RED + f"Error flushing events: {e}" + Style.RESET_ALL)

        # Flush state buffer to JSON log file
        if self.state_buffer:
            try:
                with open(self.state_file, "a") as file:  # Append mode
                    for state in self.state_buffer:
                        file.write(json.dumps(state) + "\n")  # Each state on a new line
                print(
                    Fore.YELLOW + f"Flushed {len(self.state_buffer)} states"
                    + Style.RESET_ALL
                )
                self.state_buffer.clear()
            except Exception as e:
                print(Fore.RED + f"Error flushing states: {e}" + Style.RESET_ALL)

        # Flush trace buffer to CSV trace log file
        if self.trace_buffer:
            try:
                with open(self.trace_file, "a", newline="") as csv_file:
                    writer = csv.DictWriter(csv_file, fieldnames=self.trace_fieldnames)
                    for row in self.trace_buffer:
                        writer.writerow(row)
                print(
                    Fore.YELLOW + f"Flushed {len(self.trace_buffer)} trace rows"
                    + Style.RESET_ALL
                )
                self.trace_buffer.clear()
            except Exception as e:
                print(Fore.RED + f"Error flushing trace: {e}" + Style.RESET_ALL)

    def read_logs(self, log_type=None):
        """
        Reads and returns logs from the event log file.

        This method allows retrieval of logged events, optionally filtering by event type.

        Args:
            log_type (str, optional): Specific event name to filter logs. If None, returns all logs.

        Returns:
            list: A list of log dictionaries matching the filter criteria.
        """
        try:
            with open(self.log_file, "r") as file:
                # Each line in the log file is a separate JSON object
                lines = file.readlines()
                logs = [json.loads(line) for line in lines]

                # If a specific log_type is provided, filter the logs accordingly
                if log_type:
                    return [log for log in logs if log.get("event_name") == log_type]
                return logs
        except FileNotFoundError:
            print(Fore.RED + f"No log file found at {self.log_file}" + Style.RESET_ALL)
            return []
        except json.JSONDecodeError as e:
            print(Fore.RED + f"Error decoding JSON logs: {e}" + Style.RESET_ALL)
            return []

    def __del__(self):
        """
        Ensures that all logs are flushed when the SimulationLogger instance is destroyed.
        """
        self.flush()
