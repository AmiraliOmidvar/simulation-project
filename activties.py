"""
Simulation Activity Durations and Interarrival Time Generators.

This module defines various lambda functions representing the durations of different activities
and interarrival times within the simulation. These functions utilize a random number generator
to introduce variability and realism into the simulation scenarios. The activities include
administrative work, laboratory processes, patient stays in different wards, and interarrival
times for both ordinary and urgent patients.
"""

from utils.number_generator import Generator

# Initialize the random number generator instance
generator = Generator()

# Administrative work duration for urgent patients (constant time of 10 units)
ADMIN_WORK_URGENT = lambda: 10  # S1

# Admduration for ordinary patients (constant time of 10 units)
ADMIN_WORK_ORDINARY = lambda: 10  # S2

# Laboratory processing time (uniform distribution between 28 and 32 units)
LAB = lambda: generator.uniform(28, 32)  # S3

# Stay duration in the Critical Care Unit (CCU) (exponential distribution with rate 1/(60*25))
CCU_STAY = lambda: generator.exponential(1 / (60 * 25))  # S4

# Stay duration in the Intensive Care Unit (ICU) (exponential distribution with rate 1/(60*25))
ICU_STAY = lambda: generator.exponential(1 / (60 * 25))  # S5

# Stay duration in the General Ward (exponential distribution with rate 1/(60*50))
GENERAL_STAY = lambda: generator.exponential(1 / (60 * 50))  # S6

# Pre-operating room preparation time for ordinary patients (constant time of 2880 units)
PRE_OR_ORDINARY = lambda: 2880  # S7

# Time to receive lab results (triangular distribution with low=5, mode=75, high=100 units)
LAB_RESULT = lambda: generator.triangular(5, 100, 75)  # S8

# Operating Room (OR) complex procedure duration (normal distribution with mean=242.03, stddev=63.27)
OR_COMPLEX = lambda: generator.normal(mean=242.03, stddev=63.27)  # S9

# Operating Room (OR) medium complexity procedure duration (normal distribution with mean=74.54, stddev=9.95)
OR_MEDIUM = lambda: generator.normal(mean=74.54, stddev=9.95)  # S10

# Operating Room (OR) simple procedure duration (normal distribution with mean=30.22, stddev=4.95)
OR_SIMPLE = lambda: generator.normal(mean=30.22, stddev=4.95)  # S11

# Operating Room (OR) clean-up time (constant time of 10 units)
OR_CLEAN_UP = lambda: 10  # S12

# Interarrival time for ordinary patients (exponential distribution with rate=1/60)
ORDINARY_INTERARRIVAL = lambda: generator.exponential(rate=1 / 60)  # S13

# Interarrival time for urgent patients (exponential distribution with rate=4/60)
URGENT_INTERARRIVAL = lambda: generator.exponential(rate=4 / 60)  # S14
