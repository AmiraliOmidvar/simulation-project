import math
import numpy as np
from numba import njit


@njit
def fast_combined_lcg(seed1, seed2, a1, m1, a2, m2):
    """
    Optimized Combined LCG using Numba for JIT compilation.
    """
    seed1 = (a1 * seed1) % m1
    seed2 = (a2 * seed2) % m2
    return max((seed1 - seed2) % m1, 1) / m1, seed1, seed2


@njit
def fast_normal(seed1, seed2, a1, m1, a2, m2, mean, stddev):
    """
    Optimized normal distribution using Box-Muller transform with JIT.
    """
    u1, seed1, seed2 = fast_combined_lcg(seed1, seed2, a1, m1, a2, m2)
    u2, seed1, seed2 = fast_combined_lcg(seed1, seed2, a1, m1, a2, m2)

    r = (-2.0 * math.log(u1)) ** 0.5
    theta = 6.28318530718 * u2  # 2π
    z0 = r * math.cos(theta)
    return mean + z0 * stddev, seed1, seed2


@njit
def fast_exponential(seed1, seed2, a1, m1, a2, m2, rate):
    """
    Optimized exponential distribution using inverse transform method.
    """
    u, seed1, seed2 = fast_combined_lcg(seed1, seed2, a1, m1, a2, m2)
    return -math.log(u) / rate, seed1, seed2


@njit
def fast_poisson(seed1, seed2, a1, m1, a2, m2, lam):
    """
    Optimized Poisson distribution using Knuth’s algorithm.
    """
    L = math.exp(-lam)
    k = 0
    p = 1.0
    while p > L:
        u, seed1, seed2 = fast_combined_lcg(seed1, seed2, a1, m1, a2, m2)
        p *= u
        k += 1
    return k - 1, seed1, seed2


class Generator:
    _instance = None

    def __new__(cls, seed=1234):
        if cls._instance is None:
            cls._instance = super(Generator, cls).__new__(cls)
            cls._instance._initialize(seed)
            cls._instance._seed = seed
        return cls._instance

    def _initialize(self, seed):
        """
        Initialize the LCG parameters and seeds.
        """
        self.a1, self.m1 = 40014, 2147483563
        self.a2, self.m2 = 40692, 2147483399
        self.seed1 = (seed % (self.m1 - 1)) + 1
        self.seed2 = ((seed // (self.m1 - 1)) % (self.m2 - 1)) + 1

    def combined_lcg(self):
        """
        Calls the optimized LCG function.
        """
        result, self.seed1, self.seed2 = fast_combined_lcg(
            self.seed1, self.seed2, self.a1, self.m1, self.a2, self.m2
        )
        return result

    def uniform(self, low=0.0, high=1.0):
        return low + (high - low) * self.combined_lcg()

    def normal(self, mean=0.0, stddev=1.0):
        """
        Optimized normal distribution.
        """
        result, self.seed1, self.seed2 = fast_normal(
            self.seed1, self.seed2, self.a1, self.m1, self.a2, self.m2, mean, stddev
        )
        return result

    def exponential(self, rate=1.0):
        """
        Optimized exponential distribution.
        """
        result, self.seed1, self.seed2 = fast_exponential(
            self.seed1, self.seed2, self.a1, self.m1, self.a2, self.m2, rate
        )
        return result

    def poisson(self, lam):
        """
        Optimized Poisson distribution.
        """
        result, self.seed1, self.seed2 = fast_poisson(
            self.seed1, self.seed2, self.a1, self.m1, self.a2, self.m2, lam
        )
        return result

    def randint(self, a, b):
        """
        Generates a fast random integer using LCG.
        """
        if a > b:
            raise ValueError("Lower bound 'a' must be <= upper bound 'b'.")
        u = self.combined_lcg()
        return a + int(u * (b - a + 1))

    def triangular(self, low=0.0, high=1.0, mode=0.5):
        """
        Optimized triangular distribution using inverse transform method.
        """
        if not (low <= mode <= high):
            raise ValueError("Mode must be between low and high.")

        u = self.combined_lcg()
        if u < (mode - low) / (high - low):
            return low + math.sqrt(u * (high - low) * (mode - low))
        else:
            return high - math.sqrt((1 - u) * (high - low) * (high - mode))

    @classmethod
    def reset(cls, seed):
        """
        Reset the singleton instance with a new seed.
        """
        cls._instance = None
        return cls(seed)

    def uniform_vectorized(self, low=0.0, high=1.0, size=1000):
        """
        Generates a bulk set of uniform random numbers.
        """
        return low + (high - low) * np.array([self.combined_lcg() for _ in range(size)])


# Example Usage
if __name__ == '__main__':
    seed = 73426789
    rng = Generator(seed)

    print(rng.uniform(0, 10))  # Uniform
    print(rng.normal(0, 1))  # Normal
    print(rng.exponential(1))  # Exponential
    print(rng.poisson(3))  # Poisson
    print(rng.randint(1, 100))  # Integer
    print(rng.triangular(0, 10, 5))  # Triangular
    print(rng.uniform_vectorized(0, 1, 5))  # Bulk random numbers

    # Check Singleton
    rng2 = Generator()
    print(rng is rng2)  # True
