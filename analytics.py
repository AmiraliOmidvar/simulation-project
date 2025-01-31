import json
import math
import os
from collections import defaultdict
from typing import Callable, Dict, List

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import t

# NEW IMPORT:
from config import FRAME_LENGTH, SIMULATION_TIME

from entities.patient import Patient
from system_state import SystemState
from task_manager import task_queue


class AnalyticsData:
    """
    AnalyticsData is responsible for collecting and storing all simulation data
    for a single replication. It tracks:

    - Patients' data over the course of the simulation
    - Whether the emergency section is full at certain time steps
    - Whether a patient has required resurgery
    - Queue lengths in different sections
    - Occupancy data for various sections

    The data here is then used by the Analyst class to compute statistics.
    """

    def __init__(self):
        """
        Initializes the dictionaries that will store each relevant piece of data
        during a single simulation replication.
        """
        # Dictionary that maps patient ID -> Patient object
        self.patients: Dict[int, Patient] = {}

        # For every time step, tracks if the emergency is full (True/False)
        self.emergency_is_full: Dict[int, bool] = {}

        # For every time step, indicates if a resurgery event occurred
        self.resurgery: Dict[int, bool] = {}

        # Queue length tracking (time -> queue length)
        self.emergency_queue_length: Dict[int, int] = {}
        self.or_queue_length: Dict[int, int] = {}
        self.general_queue_length: Dict[int, int] = {}
        self.lab_queue_length: Dict[int, int] = {}
        self.ccu_queue_length: Dict[int, int] = {}
        self.icu_queue_length: Dict[int, int] = {}

        # Occupancy tracking (time -> number of occupied beds/machines)
        self.emergency_occupied: Dict[int, int] = {}
        self.or_occupied: Dict[int, int] = {}
        self.general_occupied: Dict[int, int] = {}
        self.lab_occupied: Dict[int, int] = {}
        self.ccu_occupied: Dict[int, int] = {}
        self.icu_occupied: Dict[int, int] = {}
        self.pre_or_occupied: Dict[int, int] = {}

        # Map of queue names to the corresponding dictionary for quick access
        self.queue_map = {
            "emergency": self.emergency_queue_length,
            "or": self.or_queue_length,
            "general": self.general_queue_length,
            "lab": self.lab_queue_length,
            "ccu": self.ccu_queue_length,
            "icu": self.icu_queue_length,
        }

        # Map of section names to their corresponding occupancy dictionary
        self.section_map = {
            "emergency": self.emergency_occupied,
            "or": self.or_occupied,
            "general": self.general_occupied,
            "lab": self.lab_occupied,
            "ccu": self.ccu_occupied,
            "icu": self.icu_occupied,
            "pre_or": self.pre_or_occupied
        }

    def end_update(self, system_state: SystemState):
        """
        Called at the end of the simulation or replication update cycle.
        Removes all patients who have not exited yet (i.e., whose exit_time is None),
        so that only completed patients remain in the record.
        """
        # Collect keys of patients to remove (those who haven't exited yet)
        patients_to_remove = [
            patient_id
            for patient_id, patient in self.patients.items()
            if patient.exit_time is None
        ]

        # Remove such patients from the dictionary
        for patient_id in patients_to_remove:
            del self.patients[patient_id]

    def update(self, system_state: SystemState):
        """
        Processes tasks from the global task_queue and updates queue lengths
        and section occupancies in the corresponding dictionaries.
        """
        # As long as there is a task in the queue, process it
        while task_queue:
            task = task_queue.popleft()
            # Update queue length data
            if task["task"] == "queue":
                self.queue_map[task["queue"]][task["time"]] = task["size"]

            # Update section occupancy data
            if task["task"] == "section":
                self.section_map[task["section"]][task["time"]] = task["number"]


class Analyst:
    """
    Analyst handles multiple metrics (types of data) across multiple replications
    of a simulation. It is initialized with a dataset, which is a list of
    AnalyticsData objects (one per replication). It can then compute statistics,
    generate plots, and produce summary results (including confidence intervals).
    """

    def __init__(self, dataset: List["AnalyticsData"]):
        """
        :param dataset: A list of AnalyticsData objects, each containing the full
                        record of data for one simulation replication.
        """
        self.dataset = dataset

        # Map each metric name to a function that returns "frame-broken" data,
        # i.e., a list of dictionaries keyed by frame_index -> value.
        from functools import partial
        self.metrics: Dict[str, Callable] = {
            "patient_waits": self._frame_patient_waits,
            "emergency_is_full": partial(self._frame_bool, metric_name="emergency_is_full"),
            "resurgery": partial(self._frame_bool, metric_name="resurgery"),

            "general_queue": partial(self._frame_queue, queue_name="general"),
            "emergency_queue": partial(self._frame_queue, queue_name="emergency"),
            "or_queue": partial(self._frame_queue, queue_name="or"),
            "lab_queue": partial(self._frame_queue, queue_name="lab"),
            "ccu_queue": partial(self._frame_queue, queue_name="ccu"),
            "icu_queue": partial(self._frame_queue, queue_name="icu"),

            "general_occupied": partial(self._frame_section, section_name="general"),
            "emergency_occupied": partial(self._frame_section, section_name="emergency"),
            "or_occupied": partial(self._frame_section, section_name="or"),
            "lab_occupied": partial(self._frame_section, section_name="lab"),
            "ccu_occupied": partial(self._frame_section, section_name="ccu"),
            "icu_occupied": partial(self._frame_section, section_name="icu"),
            "pre_or_occupied": partial(self._frame_section, section_name="pre_or")
        }

        # For certain metrics, we may decide to ignore the first few frames (burn-in, etc.)
        # This dictionary holds the cutoff frame index for each metric.
        self.metrics_cutoff: Dict[str, int] = {
            "patient_waits": 0,
            "emergency_is_full": 0,
            "general_queue": 0,
            "emergency_queue": 0,
            "or_queue": 0,
            "lab_queue": 0,
            "ccu_queue": 0,
            "icu_queue": 0,
            "resurgery": 0,
            "general_occupied": 0,
            "emergency_occupied": 0,
            "or_occupied": 0,
            "lab_occupied": 0,
            "ccu_occupied": 0,
            "icu_occupied": 0,
            "pre_or_occupied": 0
        }

    # -------------------------------------------------------------------------
    # Helper function to fill frames from 0..(total_frames-1) by carrying forward
    # the last known value if a frame is missing.
    # -------------------------------------------------------------------------
    def _fill_missing_frames(self, frame_dict: Dict[int, float]) -> Dict[int, float]:
        total_frames = SIMULATION_TIME // FRAME_LENGTH
        filled_dict = {}
        last_value = 0.0
        for f in range(total_frames):
            value = frame_dict.get(f, last_value)
            filled_dict[f] = value
            last_value = value
        return filled_dict

    # -------------------------------------------------------------------------
    # 1. METRIC-SPECIFIC "FRAME-BROKEN" METHODS
    # -------------------------------------------------------------------------
    def _frame_patient_waits(self) -> List[Dict[int, float]]:
        """
        For each replication, compute the average wait time for each 480-minute frame.
        Returns a list of dicts, where each dict maps {frame_index -> average_wait_time}.
        """
        all_frame_averages = []

        # Loop over each replication's data
        for data in self.dataset:
            frames: Dict[int, List[float]] = defaultdict(list)

            # For each patient, collect wait times based on their enter and exit times
            for patient in data.patients.values():
                if patient.exit_time is None:
                    continue

                # Calculate the wait time for the patient
                wait_time = patient.exit_time - patient.enter_time

                # Determine which frame (of length FRAME_LENGTH) they belong to
                frame_index = patient.enter_time // FRAME_LENGTH
                frames[frame_index].append(wait_time)

            # Compute the mean wait time for each frame in this replication
            frame_averages: Dict[int, float] = {}
            for f_index, wait_times in frames.items():
                if wait_times:
                    frame_averages[f_index] = sum(wait_times) / len(wait_times)
                else:
                    frame_averages[f_index] = 0.0

            # Fill missing frames using the helper
            filled_frame_averages = self._fill_missing_frames(frame_averages)
            all_frame_averages.append(filled_frame_averages)

        return all_frame_averages

    def _frame_queue(self, queue_name: str) -> List[Dict[int, float]]:
        """
        For each replication, computes the average queue length (for a given queue)
        within each 480-minute frame. Returns a list of dicts mapping {frame_index -> average_length}.
        :param queue_name: Name of the queue to process (e.g., "emergency", "or", etc.).
        """
        all_frame_averages = []

        # Loop over each replication's data
        for data in self.dataset:
            frames: Dict[int, List[float]] = defaultdict(list)

            # For each time entry in the specified queue's dictionary
            for time, observation in data.queue_map[queue_name].items():
                frame_index = time // FRAME_LENGTH
                frames[frame_index].append(observation)

            # Compute average queue length for each frame
            frame_averages: Dict[int, float] = {}
            for f_index, observation in frames.items():
                if observation:
                    frame_averages[f_index] = sum(observation) / len(observation)
                else:
                    frame_averages[f_index] = 0.0

            # Fill missing frames using the helper
            filled_frame_averages = self._fill_missing_frames(frame_averages)
            all_frame_averages.append(filled_frame_averages)

        return all_frame_averages

    def _frame_section(self, section_name: str) -> List[Dict[int, float]]:
        """
        For each replication, computes the average occupancy for a given section
        (e.g., "emergency", "or", "ccu", etc.) within each 480-minute frame.
        Returns a list of dicts mapping {frame_index -> average_occupancy}.
        :param section_name: Name of the section to process.
        """
        all_frame_averages = []

        # Loop over each replication's data
        for data in self.dataset:
            frames: Dict[int, List[float]] = defaultdict(list)

            # For each time entry in the specified section's dictionary
            for time, observation in data.section_map[section_name].items():
                frame_index = time // FRAME_LENGTH
                frames[frame_index].append(observation)

            # Compute average occupancy for each frame
            frame_averages: Dict[int, float] = {}
            for f_index, observation in frames.items():
                if observation:
                    frame_averages[f_index] = sum(observation) / len(observation)
                else:
                    frame_averages[f_index] = 0.0

            # Fill missing frames using the helper
            filled_frame_averages = self._fill_missing_frames(frame_averages)
            all_frame_averages.append(filled_frame_averages)

        return all_frame_averages

    def _frame_bool(self, metric_name: str) -> List[Dict[int, float]]:
        """
        For each replication, computes the fraction of 'True' occurrences for a given boolean metric
        (e.g., 'emergency_is_full', 'resurgery') within each 480-minute frame.
        Returns a list of dicts mapping {frame_index -> fraction_true}.
        :param metric_name: Name of the boolean metric in AnalyticsData to process.
        """
        all_frame_averages = []

        # Loop over each replication's data
        for data in self.dataset:
            frames: Dict[int, List[bool]] = defaultdict(list)

            # For each time entry in the specified boolean metric's dictionary
            for time, observation in getattr(data, metric_name).items():
                frame_index = time // FRAME_LENGTH
                frames[frame_index].append(observation)

            # Compute fraction of True values for each frame
            frame_averages: Dict[int, float] = {}
            for f_index, observations in frames.items():
                if not len(observations) == 0:
                    frame_averages[f_index] = observations.count(True) / len(observations)
                else:
                    frame_averages[f_index] = 0

            # Fill missing frames using the helper
            filled_frame_averages = self._fill_missing_frames(frame_averages)
            all_frame_averages.append(filled_frame_averages)

        return all_frame_averages

    # -------------------------------------------------------------------------
    # 2. COMPUTE FRAME-WISE ENSEMBLE (NO FRAME-BY-FRAME CIs)
    # -------------------------------------------------------------------------
    @staticmethod
    def compute_frame_ensemble(
            frame_data: List[Dict[int, float]],
    ) -> Dict[int, float]:
        """
        Given a list of per-replication dictionaries mapping frame_index -> value,
        compute the ensemble average at each frame index (mean across replications).

        :param frame_data: A list of per-replication dicts (frame -> value).
        :return: A dict: {frame_index -> mean across replications}.
        """
        # 1) Collect all frames across all replications
        all_frames = set()
        for rep_dict in frame_data:
            all_frames.update(rep_dict.keys())
        sorted_frames = sorted(all_frames)

        # 2) For each frame, average across replications
        ensemble_data = {}
        for f in sorted_frames:
            values = []
            for rep_dict in frame_data:
                if f in rep_dict:
                    values.append(rep_dict[f])
            if len(values) > 0:
                ensemble_data[f] = sum(values) / len(values)
            else:
                ensemble_data[f] = 0.0
        return ensemble_data

    # -------------------------------------------------------------------------
    # 3. COMPUTE "OVERALL" POINT ESTIMATOR + CI (ACROSS FRAMES)
    # -------------------------------------------------------------------------
    @staticmethod
    def compute_overall_point_estimate_and_ci(
            ensemble_data: Dict[int, float],
            alpha: float = 0.05,
            cutoff: int = 0
    ) -> Dict[str, float]:
        """
        Treats each frame's ensemble average as one observation in a sample.

        The returned dictionary includes:
          - 'mean': The average across frames (after cutoff)
          - 'ci_lower': Lower bound of the t-based confidence interval
          - 'ci_upper': Upper bound of the t-based confidence interval

        :param ensemble_data: Dictionary {frame_index -> ensemble_average}.
        :param alpha: Significance level for the confidence interval (default 0.05).
        :param cutoff: How many initial frames to skip (e.g. burn-in).
        :return: A dict with keys "mean", "ci_lower", "ci_upper".
        """
        # If there's no frame data, return all zeros
        if not ensemble_data:
            return {"mean": 0.0, "ci_lower": 0.0, "ci_upper": 0.0}

        # Convert the values to a list and apply the cutoff
        values = list(ensemble_data.values())[cutoff:]
        n = len(values)

        # Calculate the overall mean
        overall_mean = np.mean(values)

        # If only one frame or fewer, margin is 0
        if n > 1:
            overall_std = np.std(values, ddof=1)
            dof = n - 1
            # t critical value for two-tailed alpha
            t_crit = t.ppf(1 - alpha / 2, dof)
            margin = t_crit * (overall_std / math.sqrt(n))
        else:
            margin = 0.0

        return {
            "mean": overall_mean,
            "ci_lower": overall_mean - margin,
            "ci_upper": overall_mean + margin,
        }

    # -------------------------------------------------------------------------
    # 4. PLOTTING (NO FRAME-BY-FRAME CI)
    # -------------------------------------------------------------------------
    @staticmethod
    def plot_frame_data(
            frame_data: List[Dict[int, float]],
            ensemble_data: Dict[int, float],
            metric_name: str,
            save_path: str
    ):
        """
        Generates a line plot showing:
          - Each replication's values in black with low opacity
          - The ensemble average as a thick black line
        Saves the plot to the given path and then closes the plot figure.

        :param frame_data: List of dicts, each dict is (frame_index -> value) for a replication.
        :param ensemble_data: A dict (frame_index -> ensemble mean) across replications.
        :param metric_name: The name of the metric being plotted (for labels).
        :param save_path: Path to save the resulting plot image.
        """
        # Ensure the directory for saving plots exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # Collect all frames from all replications
        all_frames = set()
        for rep_dict in frame_data:
            all_frames.update(rep_dict.keys())
        sorted_frames = sorted(all_frames)

        # Plot each replication's curve (thin, low opacity)
        for rep_dict in frame_data:
            y_values = [rep_dict.get(f, 0.0) for f in sorted_frames]
            plt.plot(sorted_frames, y_values, color="black", alpha=0.01)

        # Plot the ensemble average (thick black line)
        ensemble_y = [ensemble_data.get(f, 0.0) for f in sorted_frames]
        plt.plot(
            sorted_frames,
            ensemble_y,
            color="black",
            linewidth=2,
            label="Ensemble (frame-wise)"
        )

        # Labeling axes and title
        plt.xlabel("Frame Index (each = 480 minutes)")
        plt.ylabel(f"{metric_name} (units)")
        plt.title(f"{metric_name} by Frame")
        plt.legend()

        # Save and close the plot
        plt.savefig(save_path, bbox_inches="tight")
        plt.close()
        print(f"[INFO] Plot for '{metric_name}' saved to: {save_path}")

    # -------------------------------------------------------------------------
    # 5. MASTER RUN METHOD
    # -------------------------------------------------------------------------
    def run_analytics(
            self,
            alpha: float = 0.05,
            output_json: str = "analysis.json",
            output_plots_dir: str = "plots",
    ):
        """
        Orchestrates the analytics workflow for all metrics:
          1) For each metric, obtain "frame-broken" data across replications.
          2) Compute the frame-wise ensemble average.
          3) Compute a single overall point estimate + CI across frames.
          4) Plot each metric's replications + ensemble average.
          5) Save results to a JSON file, including summary statistics.

        :param alpha: Significance level (default=0.05) for confidence intervals.
        :param output_json: Path to save the summary JSON file (default="analysis.json").
        :param output_plots_dir: Directory where plots should be saved (default="plots").
        """
        results_for_all_metrics = {}

        # Iterate over all defined metrics
        for metric_name, frame_broken_func in self.metrics.items():
            # 1) Get the per-replication, per-frame data
            data = frame_broken_func()  # -> List[Dict[int, float]]

            # 2) Compute the ensemble across replications for each frame
            ensemble_data = self.compute_frame_ensemble(data)

            # 3) Compute overall point estimate and CI across frames
            summary_stats = self.compute_overall_point_estimate_and_ci(
                ensemble_data,
                alpha=alpha,
                cutoff=self.metrics_cutoff[metric_name]
            )

            # 4) Plot the data
            plot_path = os.path.join(output_plots_dir, f"{metric_name}.png")
            self.plot_frame_data(
                frame_data=data,
                ensemble_data=ensemble_data,
                metric_name=metric_name,
                save_path=plot_path
            )

            # 5) Prepare the dictionary to store in the final JSON
            metric_dict = {
                "estimation": summary_stats  # overall mean & CI
            }
            results_for_all_metrics[metric_name] = metric_dict

        # Write out the final results to a JSON file
        os.makedirs(os.path.dirname(output_json) or ".", exist_ok=True)
        with open(output_json, "w") as f:
            json.dump(results_for_all_metrics, f, indent=2)

        print(f"[INFO] Analysis results saved to '{output_json}'")
