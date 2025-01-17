import json
import math
import os
from collections import defaultdict, deque
from typing import Callable, Dict, List

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import t

from config import FRAME_LENGTH
from entities.patient import Patient
from system_state import SystemState
from task_manager import task_queue


class AnalyticsData:
    """
    Collects and organizes data throughout the simulation for post-simulation analysis.

    This class stores various metrics related to patients and system states at different
    points in time. It aggregates data from the simulation's event processing to provide
    a comprehensive dataset for analysis.

    Attributes:
        patients (Dict[int, Patient]): Maps patient IDs to their respective Patient objects.
        emergency_is_full (Dict[int, bool]): Tracks whether the emergency room was full at specific times.
        resurgery (Dict[int, bool]): Tracks whether a resurgery event occurred for patients.

        emergency_queue_length (Dict[int, int]): Records the length of the emergency queue over time.
        or_queue_length (Dict[int, int]): Records the length of the operating room queue over time.
        general_queue_length (Dict[int, int]): Records the length of the general ward queue over time.
        lab_queue_length (Dict[int, int]): Records the length of the lab queue over time.
        ccu_queue_length (Dict[int, int]): Records the length of the CCU queue over time.
        icu_queue_length (Dict[int, int]): Records the length of the ICU queue over time.

        emergency_occupied (Dict[int, int]): Tracks the number of occupied emergency beds over time.
        or_occupied (Dict[int, int]): Tracks the number of occupied OR beds over time.
        general_occupied (Dict[int, int]): Tracks the number of occupied general beds over time.
        lab_occupied (Dict[int, int]): Tracks the number of occupied lab beds over time.
        ccu_occupied (Dict[int, int]): Tracks the number of occupied CCU beds over time.
        icu_occupied (Dict[int, int]): Tracks the number of occupied ICU beds over time.
        pre_or_occupied (Dict[int, int]): Tracks the number of occupied pre-operation beds over time.

        queue_map (Dict[str, Dict[int, int]]): Maps queue names to their respective queue length dictionaries.
        section_map (Dict[str, Dict[int, int]]): Maps section names to their respective occupied bed dictionaries.
    """

    def __init__(self):
        """
        Initializes the AnalyticsData with empty dictionaries for tracking various metrics.

        This setup prepares all necessary data structures to record metrics during the simulation.
        """
        self.patients: Dict[int, Patient] = {}
        self.emergency_is_full: Dict[int, bool] = {}
        self.resurgery: Dict[int, bool] = {}

        self.emergency_queue_length: Dict[int, int] = {}
        self.or_queue_length: Dict[int, int] = {}
        self.general_queue_length: Dict[int, int] = {}
        self.lab_queue_length: Dict[int, int] = {}
        self.ccu_queue_length: Dict[int, int] = {}
        self.icu_queue_length: Dict[int, int] = {}

        self.emergency_occupied: Dict[int, int] = {}
        self.or_occupied: Dict[int, int] = {}
        self.general_occupied: Dict[int, int] = {}
        self.lab_occupied: Dict[int, int] = {}
        self.ccu_occupied: Dict[int, int] = {}
        self.icu_occupied: Dict[int, int] = {}
        self.pre_or_occupied: Dict[int, int] = {}

        self.queue_map = {
            "emergency": self.emergency_queue_length,
            "or": self.or_queue_length,
            "general": self.general_queue_length,
            "lab": self.lab_queue_length,
            "ccu": self.ccu_queue_length,
            "icu": self.icu_queue_length,
        }

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
        Cleans up patient records at the end of the simulation.

        Removes patients who have not exited the system by the end of the simulation.

        Args:
            system_state (SystemState): The final state of the system at simulation end.
        """
        # Identify patients who have not exited the system
        patients_to_remove = [
            patient_id
            for patient_id, patient in self.patients.items()
            if patient.exit_time is None
        ]

        # Remove these patients from the records
        for patient_id in patients_to_remove:
            del self.patients[patient_id]

    def update(self, system_state: SystemState):
        """
        Processes and records tasks from the task queue.

        Updates queue lengths and bed occupancies based on tasks generated during event execution.

        Args:
            system_state (SystemState): The current state of the system.
        """
        while task_queue:
            task = task_queue.popleft()
            if task["task"] == "queue":
                queue_name = task.get("queue")
                if queue_name in self.queue_map:
                    self.queue_map[queue_name][task["time"]] = task["size"]
                else:
                    print(f"[WARNING] Unknown queue name: {queue_name}")

            elif task["task"] == "section":
                section_name = task.get("section")
                if section_name in self.section_map:
                    self.section_map[section_name][task["time"]] = task["number"]
                else:
                    print(f"[WARNING] Unknown section name: {section_name}")


class Analyst:
    """
    Performs analysis on collected simulation data to generate metrics and visualizations.

    This class handles multiple types of metrics, processes frame-based data, computes ensemble
    averages, calculates confidence intervals, and generates plots for visualization.

    Attributes:
        dataset (List[AnalyticsData]): A list of AnalyticsData objects from multiple simulation runs.
        metrics (Dict[str, Callable]): Maps metric names to their corresponding processing functions.
        metrics_cutoff (Dict[str, int]): Defines cutoff points for each metric to exclude initial frames if necessary.
    """

    def __init__(self, dataset: List["AnalyticsData"]):
        """
        Initializes the Analyst with a dataset containing multiple simulation replications.

        Args:
            dataset (List[AnalyticsData]): A list of AnalyticsData objects, each representing a simulation run.
        """
        self.dataset = dataset

        # Map: metric name -> function that returns frame-broken data
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

        # Map: metric name -> cutoff point (frames to exclude from analysis)
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
    # 1. METRIC-SPECIFIC "FRAME-BROKEN" METHODS
    # -------------------------------------------------------------------------
    def _frame_patient_waits(self) -> List[Dict[int, float]]:
        """
        Calculates the average wait time for patients within each frame across all replications.

        A frame represents a specific time interval (e.g., 480 minutes). This method aggregates
        wait times of patients who entered during each frame and computes the average wait time.

        Returns:
            List[Dict[int, float]]: A list where each element corresponds to a replication and maps
                                     frame indices to average wait times.
        """
        all_frame_averages = []

        for data in self.dataset:
            frames: Dict[int, List[float]] = defaultdict(list)

            for patient in data.patients.values():
                if patient.exit_time is None:
                    continue  # Skip patients who haven't exited

                wait_time = patient.exit_time - patient.enter_time
                frame_index = int(patient.enter_time // FRAME_LENGTH)
                frames[frame_index].append(wait_time)

            # Compute mean wait time for each frame
            frame_averages: Dict[int, float] = {}
            for f_index, wait_times in frames.items():
                if wait_times:
                    frame_averages[f_index] = sum(wait_times) / len(wait_times)
                else:
                    frame_averages[f_index] = 0.0

            all_frame_averages.append(frame_averages)

        return all_frame_averages

    def _frame_queue(self, queue_name: str) -> List[Dict[int, float]]:
        """
        Calculates the average queue length for a specific queue within each frame across all replications.

        Args:
            queue_name (str): The name of the queue to analyze (e.g., "general", "emergency").

        Returns:
            List[Dict[int, float]]: A list where each element corresponds to a replication and maps
                                     frame indices to average queue lengths.
        """
        all_frame_averages = []

        for data in self.dataset:
            frames: Dict[int, List[float]] = defaultdict(list)

            for time, observation in data.queue_map[queue_name].items():
                frame_index = int(time // FRAME_LENGTH)
                frames[frame_index].append(observation)

            # Compute mean queue length for each frame
            frame_averages: Dict[int, float] = {}
            for f_index, observations in frames.items():
                if observations:
                    frame_averages[f_index] = sum(observations) / len(observations)
                else:
                    frame_averages[f_index] = 0.0

            all_frame_averages.append(frame_averages)

        return all_frame_averages

    def _frame_section(self, section_name: str) -> List[Dict[int, float]]:
        """
        Calculates the average number of occupied beds for a specific section within each frame across all replications.

        Args:
            section_name (str): The name of the section to analyze (e.g., "general", "icu").

        Returns:
            List[Dict[int, float]]: A list where each element corresponds to a replication and maps
                                     frame indices to average occupied bed counts.
        """
        all_frame_averages = []

        for data in self.dataset:
            frames: Dict[int, List[float]] = defaultdict(list)

            for time, observation in data.section_map[section_name].items():
                frame_index = int(time // FRAME_LENGTH)
                frames[frame_index].append(observation)

            # Compute mean occupied beds for each frame
            frame_averages: Dict[int, float] = {}
            for f_index, observations in frames.items():
                if observations:
                    frame_averages[f_index] = sum(observations) / len(observations)
                else:
                    frame_averages[f_index] = 0.0

            all_frame_averages.append(frame_averages)

        return all_frame_averages

    def _frame_bool(self, metric_name: str) -> List[Dict[int, float]]:
        """
        Calculates the proportion of True occurrences for a boolean metric within each frame across all replications.

        Args:
            metric_name (str): The name of the boolean metric to analyze (e.g., "emergency_is_full").

        Returns:
            List[Dict[int, float]]: A list where each element corresponds to a replication and maps
                                     frame indices to the proportion of True occurrences.
        """
        all_frame_averages = []

        for data in self.dataset:
            frames: Dict[int, List[bool]] = defaultdict(list)

            # Retrieve the appropriate metric dictionary
            metric_dict = getattr(data, metric_name, {})
            for time, observation in metric_dict.items():
                frame_index = int(time // FRAME_LENGTH)
                frames[frame_index].append(observation)

            # Compute the proportion of True for each frame
            frame_averages: Dict[int, float] = {}
            for f_index, observations in frames.items():
                if observations:
                    true_count = observations.count(True)
                    frame_averages[f_index] = true_count / len(observations)
                else:
                    frame_averages[f_index] = 0.0

            all_frame_averages.append(frame_averages)

        return all_frame_averages

    # -------------------------------------------------------------------------
    # 2. COMPUTE FRAME-WISE ENSEMBLE (NO FRAME-BY-FRAME CIs)
    # -------------------------------------------------------------------------
    @staticmethod
    def compute_frame_ensemble(
            frame_data: List[Dict[int, float]],
    ) -> Dict[int, float]:
        """
        Aggregates frame-based data across all replications to compute ensemble averages for each frame.

        Args:
            frame_data (List[Dict[int, float]]): A list where each element is a dictionary mapping
                                                frame indices to values for a single replication.

        Returns:
            Dict[int, float]: A dictionary mapping each frame index to its ensemble average across replications.
        """
        # Collect all unique frame indices across all replications
        all_frames = set()
        for rep_dict in frame_data:
            all_frames.update(rep_dict.keys())
        sorted_frames = sorted(all_frames)

        # Compute the average value for each frame across all replications
        ensemble_data = {}
        for f in sorted_frames:
            values = [rep_dict[f] for rep_dict in frame_data if f in rep_dict]
            if values:
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
        Calculates the overall mean and confidence interval across all frames for a given metric.

        Treats each frame's ensemble average as an independent observation and computes the mean
        and confidence interval using the t-distribution.

        Args:
            ensemble_data (Dict[int, float]): A dictionary mapping frame indices to ensemble averages.
            alpha (float, optional): Significance level for the confidence interval. Defaults to 0.05.
            cutoff (int, optional): Number of initial frames to exclude from the analysis. Defaults to 0.

        Returns:
            Dict[str, float]: A dictionary containing the overall mean, lower CI, and upper CI.
        """
        # Exclude initial frames based on the cutoff
        values = list(ensemble_data.values())[cutoff:]
        n = len(values)

        # If no data is available after cutoff, return zeros
        if n == 0:
            return {"mean": 0.0, "ci_lower": 0.0, "ci_upper": 0.0}

        overall_mean = np.mean(values)

        if n > 1:
            overall_std = np.std(values, ddof=1)
            dof = n - 1
            # Calculate the t critical value for a two-tailed test
            t_crit = t.ppf(1 - alpha / 2, dof)
            margin = t_crit * (overall_std / math.sqrt(n))
        else:
            # If only one observation, margin of error is zero
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
        Generates and saves a plot for a specific metric showing individual replications and the ensemble average.

        The plot includes:
            - Each replication's data as a thin black line with low opacity.
            - The ensemble average across all replications as a thick black line.

        Args:
            frame_data (List[Dict[int, float]]): A list where each element is a dictionary mapping
                                                frame indices to metric values for a single replication.
            ensemble_data (Dict[int, float]): A dictionary mapping frame indices to ensemble averages.
            metric_name (str): The name of the metric being plotted.
            save_path (str): The file path where the plot image will be saved.
        """
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)

        # Collect all frame indices
        all_frames = set()
        for rep_dict in frame_data:
            all_frames.update(rep_dict.keys())
        sorted_frames = sorted(all_frames)

        # Plot each replication's data
        for rep_dict in frame_data:
            y_values = [rep_dict.get(f, 0.0) for f in sorted_frames]
            plt.plot(sorted_frames, y_values, color="black", alpha=0.1)

        # Plot the ensemble average
        ensemble_y = [ensemble_data.get(f, 0.0) for f in sorted_frames]
        plt.plot(
            sorted_frames,
            ensemble_y,
            color="red",
            linewidth=2,
            label="Ensemble Average"
        )

        plt.xlabel("Frame Index (Each Frame = {} minutes)".format(FRAME_LENGTH))
        plt.ylabel(f"{metric_name} (Units)")
        plt.title(f"{metric_name} Over Time")
        plt.legend()

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
        Executes the full analytics workflow, processing all metrics, generating plots, and saving results.

        The workflow includes:
            1. Processing frame-based data for each metric across all replications.
            2. Computing ensemble averages for each frame.
            3. Calculating overall mean and confidence intervals across frames.
            4. Generating and saving plots for each metric.
            5. Compiling and saving all results to a JSON file.

        Args:
            alpha (float, optional): Significance level for confidence intervals. Defaults to 0.05.
            output_json (str, optional): Path to save the analysis results in JSON format. Defaults to "analysis.json".
            output_plots_dir (str, optional): Directory to save the generated plots. Defaults to "plots".
        """
        results_for_all_metrics = {}

        for metric_name, frame_broken_func in self.metrics.items():
            print(f"[INFO] Processing metric: {metric_name}")

            # 1. Retrieve frame-based data for the metric across all replications
            data = frame_broken_func()  # List[Dict[int, float]]

            # 2. Compute the ensemble average for each frame
            ensemble_data = self.compute_frame_ensemble(data)

            # 3. Compute overall mean and confidence interval across frames
            summary_stats = self.compute_overall_point_estimate_and_ci(
                ensemble_data,
                alpha=alpha,
                cutoff=self.metrics_cutoff.get(metric_name, 0)
            )

            # 4. Generate and save the plot for the metric
            plot_path = os.path.join(output_plots_dir, f"{metric_name}.png")
            self.plot_frame_data(
                frame_data=data,
                ensemble_data=ensemble_data,
                metric_name=metric_name,
                save_path=plot_path
            )

            # 5. Compile the results for JSON output
            metric_dict = {
                "frames": ensemble_data,
                "summary": summary_stats
            }
            results_for_all_metrics[metric_name] = metric_dict

        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_json) or ".", exist_ok=True)

        # Save all analysis results to a JSON file
        with open(output_json, "w") as f:
            json.dump(results_for_all_metrics, f, indent=2)

        print(f"[INFO] Analysis results saved to '{output_json}'")
