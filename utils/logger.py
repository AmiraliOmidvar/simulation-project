import atexit
import csv
import json
import os
import threading

import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)  # Initialize colorama


class SimulationLogger:
    MAX_BUFFER_SIZE = 50  # Maximum number of logs before auto-flushing

    def __init__(
            self,
            log_file="simulation_logs.json",
            state_file="state_logs.json",
            trace_file="trace_logs.csv"
            ):

        self.log_file = log_file
        self.state_file = state_file
        self.trace_file = trace_file

        self.event_buffer = []
        self.state_buffer = []
        self.trace_buffer = []

        self.lock = threading.Lock()  # For thread safety

        # Remove existing logs (JSON & CSV) on init to start fresh
        for file_path in [self.log_file, self.state_file, self.trace_file]:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Removed existing log file: {file_path}")

        # Prepare CSV with headers
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
        with open(self.trace_file, "w", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=self.trace_fieldnames)
            writer.writeheader()

        # Register the flush method to be called on program exit
        atexit.register(self.flush)

    def log_event(self, event_name, time, patient, patient_type, patient_surgery, details):
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

            print(
                Fore.GREEN + "Event Logged: " +
                Fore.CYAN + f"[Event Name: {Fore.YELLOW}{event['event_name']}" +
                Fore.CYAN + f", Time: {Fore.YELLOW}{event['time']}" +
                Fore.CYAN + f", Patient: {Fore.YELLOW}{event['patient']}" +
                Fore.CYAN + f", Details: {Fore.YELLOW}{event['details']}" +
                Fore.CYAN + "]" + Style.RESET_ALL
            )

            if buffer_size >= self.MAX_BUFFER_SIZE:
                self.flush()

    def log_state(self, system_state, time):
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
                "general": system_state.num_occupied_beds_general,
                "or": system_state.num_occupied_beds_or,
                "emergency": system_state.num_occupied_beds_emergency,
                "lab": system_state.num_occupied_beds_lab,
                "icu": system_state.num_occupied_beds_icu,
                "ccu": system_state.num_occupied_beds_ccu,
                "pre_or": system_state.num_occupied_beds_pre_or,
            },
            "power_status": system_state.power_status
        }

        with self.lock:
            self.state_buffer.append(state)

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
        This method creates a single row combining event data + system state data
        and stores it into a CSV row.
        """
        # Combine the event info and state info into one dictionary
        trace_row = {
            "event_name": event_name,
            "event_time": event_time,
            "patient": patient,
            "patient_type": patient_type,
            "patient_surgery": patient_surgery,
            "event_details": event_details,
            "system_time": system_state.current_time,  # from system_state
            "lab_queue": len(system_state.lab_queue),
            "emergency_queue": len(system_state.emergency_queue),
            "or_queue": len(system_state.or_queue),
            "ccu_queue": len(system_state.ccu_queue),
            "icu_queue": len(system_state.icu_queue),
            "general_queue": len(system_state.general_queue),
            "occupied_beds_general": system_state.num_occupied_beds_general,
            "occupied_beds_or": system_state.num_occupied_beds_or,
            "occupied_beds_emergency": system_state.num_occupied_beds_emergency,
            "occupied_beds_lab": system_state.num_occupied_beds_lab,
            "occupied_beds_icu": system_state.num_occupied_beds_icu,
            "occupied_beds_ccu": system_state.num_occupied_beds_ccu,
            "occupied_beds_pre_or": system_state.num_occupied_beds_pre_or,
            "power_status": system_state.power_status,
        }

        with self.lock:
            self.trace_buffer.append(trace_row)
            if len(self.trace_buffer) >= self.MAX_BUFFER_SIZE:
                self.flush()

    def flush(self):
        """Flush event, state, and trace buffers."""
        # Flush event buffer
        if self.event_buffer:
            try:
                with open(self.log_file, "a") as file:  # append mode
                    for event in self.event_buffer:
                        file.write(json.dumps(event) + "\n")  # Each event on a new line
                print(
                    Fore.YELLOW + f"Flushed {len(self.event_buffer)} events"
                    + Style.RESET_ALL
                )
                self.event_buffer.clear()
            except Exception as e:
                print(Fore.RED + f"Error flushing events: {e}" + Style.RESET_ALL)

        # Flush state buffer
        if self.state_buffer:
            try:
                with open(self.state_file, "a") as file:  # append mode
                    for state in self.state_buffer:
                        file.write(json.dumps(state) + "\n")  # Each state on a new line
                print(
                    Fore.YELLOW + f"Flushed {len(self.state_buffer)} states"
                    + Style.RESET_ALL
                )
                self.state_buffer.clear()
            except Exception as e:
                print(Fore.RED + f"Error flushing states: {e}" + Style.RESET_ALL)

        # Flush trace buffer to CSV
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
        Example method to read back JSON logs (not CSV).
        This assumes all event logs are in JSON lines.
        """
        try:
            with open(self.log_file, "r") as file:
                # Because we wrote each event as a new line of JSON,
                # we need to read line by line:
                lines = file.readlines()
                logs = [json.loads(line) for line in lines]

                # If log_type is specified, filter or process accordingly
                if log_type:
                    # e.g., return only logs with a certain event_name
                    return [log for log in logs if log.get("event_name") == log_type]
                return logs
        except FileNotFoundError:
            print(Fore.RED + f"No log file found at {self.log_file}" + Style.RESET_ALL)
            return []
        except json.JSONDecodeError as e:
            print(Fore.RED + f"Error decoding JSON logs: {e}" + Style.RESET_ALL)
            return []

    def __del__(self):
        # Ensure that logs are flushed when the instance is destroyed
        self.flush()
