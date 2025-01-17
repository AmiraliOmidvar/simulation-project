from utils.number_generator import Generator

generator = Generator()

ADMIN_WORK_URGENT = lambda: 10  # S1
ADMIN_WORK_ORDINARY = lambda: 10  # S2
LAB = lambda: generator.uniform(28, 32)  # S3
CCU_STAY = lambda: generator.exponential(1 / (60 * 25))  # S4
ICU_STAY = lambda: generator.exponential(1 / (60 * 25))  # S5
GENERAL_STAY = lambda: generator.exponential(1 / (60 * 50))  # S6
PRE_OR_ORDINARY = lambda: 2880  # S7
LAB_RESULT = lambda: generator.triangular(5, 100, 75)  # S8
OR_COMPLEX = lambda: generator.normal(mean=242.03, stddev=63.27)  # S9
OR_MEDIUM = lambda: generator.normal(mean=74.54, stddev=9.95)  # S10
OR_SIMPLE = lambda: generator.normal(mean=30.22, stddev=4.95)  # S11
OR_CLEAN_UP = lambda: 10  # S12
ORDINARY_INTERARRIVAL = lambda: generator.exponential(rate=1 / 60)  # S13
URGENT_INTERARRIVAL = lambda: generator.exponential(rate=4 / 60)  # S14
