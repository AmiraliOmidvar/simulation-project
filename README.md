
---

## 1. High-Level Flow

1. **Initialization**  
   - A `SimulationEngine` instance is created, which will manage a priority queue (`event_queue`) of simulation events.
   - A `SystemState` instance holds the state of the hospital at any point in time (e.g., bed capacities, queues for patients, power status).
   - An `AnalyticsData` instance tracks various metrics, such as queue lengths, bed occupancies, and patient records.

2. **Scheduling Initial Events**  
   - Typically, the first **patient arrival** events (both ordinary and urgent) are scheduled.
   - A **power outage** event may also be scheduled if power disruptions are part of the scenario.

3. **Running the Simulation**  
   - The `SimulationEngine` runs by repeatedly popping the **earliest** event from the `event_queue`.
   - Upon popping an event, the simulation clock (`system_state.current_time`) is advanced to that event’s time, and the event’s `execute()` method is called.

4. **Event Execution**  
   - Each event updates the `SystemState` and potentially schedules new events. For example:
     - **PatientArrivalEvent** creates a new patient and adds them to a queue or bed if available.
     - **OperationComplete** moves a patient to ICU, CCU, or general ward, or schedules another surgery if needed.
     - **PowerOut** reduces capacities and removes overflow patients. It also schedules a **PowerBack** event and the next **PowerOut**.
     - **PowerBack** restores capacities and power status.
   - Right after each event’s `execute()` method finishes, **analytics** are updated.

5. **Analytics Updates**  
   - During event execution, tasks are often appended to a global **`task_queue`** (e.g., changes in queue size, bed occupancy).
   - After each event finishes, the `AnalyticsData.update()` method dequeues and processes these tasks, storing relevant metrics (queue lengths, bed occupancy over time, etc.).

6. **Completing the Simulation**  
   - The simulation may end after a certain time limit, a fixed number of events, or another termination condition (e.g., no more events in the `event_queue`).
   - `AnalyticsData.end_update()` can finalize any metrics (e.g., remove partial records of patients who never exited).

7. **Post-Simulation Analysis**  
   - Once a simulation run completes, `AnalyticsData` contains a record of queue lengths, bed occupancies, and patient info over time.
   - Often, you run multiple replications with different random seeds. Each run produces one `AnalyticsData` object. These objects can be collected into a **dataset**.

8. **Frame-Based Data and Plotting**  
   - The **`Analyst`** class processes the collected dataset. It:
     1. Converts time-series data to **frame-based** chunks (e.g., each frame = 480 minutes).
     2. Computes **frame-wise averages** across replications for each metric (queue length, bed occupancy, etc.).
     3. Calculates overall **ensemble** statistics (mean, confidence intervals).
     4. Generates **plots** (e.g., line charts) for each metric and saves them to disk.
   - The `run_analytics()` method outputs results in a structured JSON file (like `analysis.json`) and produces plots in a specified directory (e.g., `plots/`).

---

## 2. Key Components

1. **SimulationEngine**  
   - Holds a **priority queue** (`event_queue`) of future events, sorted by event time.
   - A **`run()`** method pops events in chronological order and updates the simulation clock.

2. **SystemState**  
   - Stores real-time info on bed counts, queue contents, power status, etc.
   - Is updated by event logic (e.g., incrementing occupied beds, changing power status).

3. **Events**  
   - Subclasses of a **`BaseEvent`**:
     - **PatientArrivalOrdinaryEvent** / **PatientArrivalUrgentEvent**  
       Schedules new arrivals, determines surgery type, assigns bed or queue.
     - **MoveToOr**, **OperationComplete**, **OrCleanComplete**  
       Manage the flow of patients into OR, their surgeries, and cleanup steps.
     - **PowerOut** / **PowerBack**  
       Simulate power disruptions and restorations.

4. **task_queue**  
   - A small **deque** that events append tasks to (e.g., queue size changes, bed occupancy changes).
   - **`AnalyticsData.update()`** reads from this `task_queue` to record metrics.

5. **AnalyticsData**  
   - Maintains time-based dictionaries of queue lengths, bed occupancy, boolean flags (emergency full), etc.
   - Records each **Patient**’s arrival/exit times.  
   - Finalizes incomplete records in **`end_update()`** if the simulation ends while some patients are still in the system.

6. **Analyst**  
   - Processes multiple `AnalyticsData` instances (one per simulation run).
   - Converts raw data to **frame-broken** data (grouping by frames, e.g., every 480 minutes).
   - Computes ensemble averages, confidence intervals.
   - Creates **plots** for metrics (e.g., queue length vs. time, bed occupancy vs. time).
   - Saves a JSON summary and PNG plots.

---

## 3. Running the Simulation

1. **Multiple Seeds** (Optional)  
   - You can run multiple replications by resetting the random generator seed. For each seed:
     ```python
     for seed in SEED_LIST:
         Generator.reset(seed)
         data = run_simulation()  # returns an AnalyticsData object
         dataset.append(data)
     ```

2. **Analyzing Results**  
   - Create an **`Analyst`** with `[AnalyticsData, AnalyticsData, ...]`.
   - Call `analyst.run_analytics()` to produce:
     - A JSON file (e.g., `analysis.json`) summarizing metrics, confidence intervals, etc.
     - A series of plots (e.g., in a `plots/` directory).

---

## 4. Notes / Tips

- **Queue vs. Beds**  
  - The system differentiates between queue structures (e.g., `lab_queue`, `emergency_queue`) and integer counters for bed occupancy.  
  - In events, you typically check if a bed is available (`num_occupied_beds_* < CAPACITY_*`). If not, you push the patient to a queue.

- **Power Events**  
  - **PowerOut** reduces capacities by 20% and removes overflow patients.  
  - **PowerBack** sets `power_status = 1` and divides the capacities by 0.8 to restore them.

- **Frame Length**  
  - By default, each frame might represent 480 minutes (8 hours), but you can change it in the code to group time-based data differently.

- **Final Data**  
  - `AnalyticsData` includes:
    - **Queue length histories** (lab, emergency, or, etc.)
    - **Section occupancy** (lab_occupied, icu_occupied, etc.)
    - **Boolean metrics** (e.g., `emergency_is_full`)  
  - The **Analyst** uses these dictionaries to compute frame-based averages and plots them.

- **Extend / Modify**  
  - Add new event types (lab operation, specialized wards).
  - Adjust bed capacity logic or power disruption logic for more complex scenarios.
  - Refine analytics or integrate real-time dashboards.

---

## 5. Basic Steps to Run

1. **Set Up**  
   - Ensure you have Python 3.10+ and install any dependencies (e.g., `numpy`, `matplotlib`). 
   - you can run `pip install -r requirements.txt`

2. **Run**  
   - Call main function (e.g., `run_simulation()`) in `simulation.py` that initializes, runs the simulation, and returns an `AnalyticsData` object.

3. **Analyze**  
   - Possibly repeat with multiple seeds to get multiple `AnalyticsData` objects.
   - Pass the list of analytics data to an **`Analyst`** instance and run `analyst.run_analytics()`.

4. **View Outputs**  
   - Check JSON outputs or visual plots in the specified output folder.
