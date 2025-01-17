import json
import math
import os
from collections import defaultdict
from typing import Callable, Dict, List

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import t

from config import FRAME_LENGTH
from entities.patient import Patient
from system_state import SystemState
from task_manager import task_queue


class AnalyticsData:
    def __init__(self):
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
        # Collect keys of patients to remove
        patients_to_remove = [
            patient_id
            for patient_id, patient in self.patients.items()
            if patient.exit_time is None
        ]

        # Remove patients from the dictionary
        for patient_id in patients_to_remove:
            del self.patients[patient_id]

    def update(self, system_state: SystemState):
        while task_queue:
            task = task_queue.popleft()
            if task["task"] == "queue":
                self.queue_map[task["queue"]][task["time"]] = task["size"]

            if task["task"] == "section":
                self.section_map[task["section"]][task["time"]] = task["number"]


class Analyst:
    """
    Analyst handles multiple "metrics" or types of data.
    Each metric is associated with a function returning "frame-broken" data:
        List[Dict[frame_index, value]]    # one dict per replication

    Example:
        "patient_waits" -> self._frame_patient_waits()
    """

    def __init__(self, dataset: List["AnalyticsData"]):
        """
        :param dataset: A list of AnalyticsData objects, one per replication.
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

        # Map: metric name -> cutoff point
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
        For each replication, compute the average wait time for each 480-minute frame.
        Returns a list of dicts: [ {frame_index -> average_wait_time}, ... ].
        """
        all_frame_averages = []

        for data in self.dataset:
            frames: Dict[int, List[float]] = defaultdict(list)

            for patient in data.patients.values():
                if patient.exit_time is None:
                    continue

                wait_time = patient.exit_time - patient.enter_time
                frame_index = patient.enter_time // FRAME_LENGTH
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

    def _frame_queue(self, queue_name):
        all_frame_averages = []

        for data in self.dataset:
            frames: Dict[int, List[float]] = defaultdict(list)

            for time, observation in data.queue_map[queue_name].items():
                frame_index = time // FRAME_LENGTH
                frames[frame_index].append(observation)

            # Compute mean wait time for each frame
            frame_averages: Dict[int, float] = {}
            for f_index, observation in frames.items():
                if observation:
                    frame_averages[f_index] = sum(observation) / len(observation)
                else:
                    frame_averages[f_index] = 0.0

            all_frame_averages.append(frame_averages)

        return all_frame_averages

    def _frame_section(self, section_name):
        all_frame_averages = []

        for data in self.dataset:
            frames: Dict[int, List[float]] = defaultdict(list)

            for time, observation in data.section_map[section_name].items():
                frame_index = time // FRAME_LENGTH
                frames[frame_index].append(observation)

            # Compute mean wait time for each frame
            frame_averages: Dict[int, float] = {}
            for f_index, observation in frames.items():
                if observation:
                    frame_averages[f_index] = sum(observation) / len(observation)
                else:
                    frame_averages[f_index] = 0.0

            all_frame_averages.append(frame_averages)

        return all_frame_averages

    def _frame_bool(self, metric_name) -> List[Dict[int, float]]:
        all_frame_averages = []

        for data in self.dataset:
            frames: Dict[int, List[bool]] = defaultdict(list)

            for time, observation in getattr(data, metric_name).items():
                frame_index = time // FRAME_LENGTH
                frames[frame_index].append(observation)

            frame_averages: Dict[int, float] = {}
            for f_index, observations in frames.items():
                if not len(observations) == 0:
                    frame_averages[f_index] = observations.count(True) / len(observations)
                else:
                    frame_averages[f_index] = 0

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
        :param frame_data: A list of per-replication dicts (frame -> value).
        :return: A dict: { frame_index -> mean across replications }
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
            alpha: float = 0.05, cutoff: int = 0
    ) -> Dict[str, float]:
        """
        We treat each frame's ensemble average as one observation in a sample.
        Then:
          - overall_mean = average across frames
          - stdev across frames
          - t-based margin of error (if #frames > 1)

        Returns a dict: { "mean": X, "ci_lower": Y, "ci_upper": Z }
        """
        # If there's no frame data, return all zeros
        if not ensemble_data:
            return {"mean": 0.0, "ci_lower": 0.0, "ci_upper": 0.0}

        values = list(ensemble_data.values())[cutoff:]
        n = len(values)

        overall_mean = np.mean(values)
        if n > 1:
            overall_std = np.std(values, ddof=1)
            dof = n - 1
            # t critical value for two-tailed alpha
            t_crit = t.ppf(1 - alpha / 2, dof)
            margin = t_crit * (overall_std / math.sqrt(n))
        else:
            # Only one frame => no variation
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
        Plots:
          - Each replication in black with low alpha.
          - The ensemble average (thick black line).
          - No confidence intervals per frame.
        """
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # Collect all frames
        all_frames = set()
        for rep_dict in frame_data:
            all_frames.update(rep_dict.keys())
        sorted_frames = sorted(all_frames)

        # Plot each replication's curve
        for rep_dict in frame_data:
            y_values = [rep_dict.get(f, 0.0) for f in sorted_frames]
            plt.plot(sorted_frames, y_values, color="black", alpha=0.01)

        # Plot the ensemble average
        ensemble_y = [ensemble_data.get(f, 0.0) for f in sorted_frames]
        plt.plot(
            sorted_frames,
            ensemble_y,
            color="black",
            linewidth=2,
            label="Ensemble (frame-wise)"
        )

        plt.xlabel("Frame Index (each = 480 minutes)")
        plt.ylabel(f"{metric_name} (units)")
        plt.title(f"{metric_name} by Frame")
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
        Workflow:
          1) For each metric, get "frame-broken" data across replications.
          2) Compute frame-wise ensemble average (dict: frame->value).
          3) Compute a single overall point estimate + CI (across frames).
          4) Plot (replications + ensemble).
          5) Save to JSON:
             {
               metric_name: {
                 "frames": { frame: ensemble_value, ... },
                 "summary": { "mean": X, "ci_lower": Y, "ci_upper": Z }
               },
               ...
             }
        """
        results_for_all_metrics = {}

        for metric_name, frame_broken_func in self.metrics.items():
            # 1) Get per-replication, per-frame data
            data = frame_broken_func()  # -> List[Dict[int, float]]

            # 2) Compute ensemble across replications for each frame
            ensemble_data = self.compute_frame_ensemble(data)

            # 3) Compute overall point estimate and CI across frames
            summary_stats = self.compute_overall_point_estimate_and_ci(
                ensemble_data,
                alpha=alpha,
                cutoff=self.metrics_cutoff[metric_name]
            )

            # 4) Plot
            plot_path = os.path.join(output_plots_dir, f"{metric_name}.png")
            self.plot_frame_data(
                frame_data=data,
                ensemble_data=ensemble_data,
                metric_name=metric_name,
                save_path=plot_path
            )

            # 5) Prepare JSON output
            metric_dict = {
                "estimation": summary_stats  # overall mean & CI
            }
            results_for_all_metrics[metric_name] = metric_dict

        # Finally, dump to JSON
        os.makedirs(os.path.dirname(output_json) or ".", exist_ok=True)
        with open(output_json, "w") as f:
            json.dump(results_for_all_metrics, f, indent=2)

        print(f"[INFO] Analysis results saved to '{output_json}'")
