import os
from utils.number_generator import Generator

# Retrieve configuration parameters from environment variables with 'CFG_' prefix
CFG_ADMIN_WORK_URGENT = int(os.getenv('ADMIN_WORK_URGENT'))  # S1
CFG_ADMIN_WORK_ORDINARY = int(os.getenv('ADMIN_WORK_ORDINARY'))  # S2

CFG_LAB_MIN = float(os.getenv('LAB_MIN'))  # S3
CFG_LAB_MAX = float(os.getenv('LAB_MAX'))  # S3

CFG_CCU_STAY_RATE = float(os.getenv('CCU_STAY_RATE'))  # S4
CFG_ICU_STAY_RATE = float(os.getenv('ICU_STAY_RATE'))  # S5
CFG_GENERAL_STAY_RATE = float(os.getenv('GENERAL_STAY_RATE'))  # S6

CFG_PRE_OR_ORDINARY = float(os.getenv('PRE_OR_ORDINARY'))  # S7

CFG_LAB_RESULT_LOW = float(os.getenv('LAB_RESULT_LOW'))  # S8
CFG_LAB_RESULT_MODE = float(os.getenv('LAB_RESULT_MODE'))  # S8
CFG_LAB_RESULT_HIGH = float(os.getenv('LAB_RESULT_HIGH'))  # S8

CFG_OR_COMPLEX_MEAN = float(os.getenv('OR_COMPLEX_MEAN'))  # S9
CFG_OR_COMPLEX_STDDEV = float(os.getenv('OR_COMPLEX_STDDEV'))  # S9

CFG_OR_MEDIUM_MEAN = float(os.getenv('OR_MEDIUM_MEAN'))  # S10
CFG_OR_MEDIUM_STDDEV = float(os.getenv('OR_MEDIUM_STDDEV'))  # S10

CFG_OR_SIMPLE_MEAN = float(os.getenv('OR_SIMPLE_MEAN'))  # S11
CFG_OR_SIMPLE_STDDEV = float(os.getenv('OR_SIMPLE_STDDEV'))  # S11

CFG_OR_CLEAN_UP = int(os.getenv('OR_CLEAN_UP'))  # S12

CFG_ORDINARY_INTERARRIVAL_RATE = float(os.getenv('ORDINARY_INTERARRIVAL_RATE'))  # S13
CFG_URGENT_INTERARRIVAL_RATE = float(os.getenv('URGENT_INTERARRIVAL_RATE'))  # S14

# Initialize the random number generator instance
generator = Generator()

# Define lambda functions using the loaded configuration parameters

ADMIN_WORK_URGENT = lambda: CFG_ADMIN_WORK_URGENT  # S1
ADMIN_WORK_ORDINARY = lambda: CFG_ADMIN_WORK_ORDINARY  # S2
LAB = lambda: generator.uniform(CFG_LAB_MIN, CFG_LAB_MAX)  # S3
CCU_STAY = lambda: generator.exponential(CFG_CCU_STAY_RATE)  # S4
ICU_STAY = lambda: generator.exponential(CFG_ICU_STAY_RATE)  # S5
GENERAL_STAY = lambda: generator.exponential(CFG_GENERAL_STAY_RATE)  # S6
PRE_OR_ORDINARY = lambda: CFG_PRE_OR_ORDINARY  # S7
LAB_RESULT = lambda: generator.triangular(CFG_LAB_RESULT_LOW, CFG_LAB_RESULT_HIGH, CFG_LAB_RESULT_MODE)  # S8
OR_COMPLEX = lambda: generator.normal(mean=CFG_OR_COMPLEX_MEAN, stddev=CFG_OR_COMPLEX_STDDEV)  # S9
OR_MEDIUM = lambda: generator.normal(mean=CFG_OR_MEDIUM_MEAN, stddev=CFG_OR_MEDIUM_STDDEV)  # S10
OR_SIMPLE = lambda: generator.normal(mean=CFG_OR_SIMPLE_MEAN, stddev=CFG_OR_SIMPLE_STDDEV)  # S11
OR_CLEAN_UP = lambda: CFG_OR_CLEAN_UP  # S12
ORDINARY_INTERARRIVAL = lambda: generator.exponential(rate=CFG_ORDINARY_INTERARRIVAL_RATE)  # S13
URGENT_INTERARRIVAL = lambda: generator.exponential(rate=CFG_URGENT_INTERARRIVAL_RATE)  # S14
