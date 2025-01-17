import math


class Generator:
    _instance = None  # Class-level variable to hold the singleton instance

    def __new__(cls, seed=1234):
        if cls._instance is None:
            # Create the instance and initialize it with the seed
            cls._instance = super(Generator, cls).__new__(cls)
            cls._instance._initialize(seed)
            cls._instance._seed = seed
        return cls._instance

    def _initialize(self, seed):
        # Parameters for the two LCGs
        self.a1, self.m1 = 40014, 2147483563
        self.a2, self.m2 = 40692, 2147483399

        # Initialize seeds for both LCGs derived from the single seed
        self.seed1 = (seed % (self.m1 - 1)) + 1  # Ensure seed1 is in [1, m1-1]
        self.seed2 = ((seed // (self.m1 - 1)) % (self.m2 - 1)) + 1  # Ensure seed2 is in [1, m2-1]

    def combined_lcg(self):
        """Combined Linear Congruential Generator"""
        # Update each LCG
        self.seed1 = (self.a1 * self.seed1) % self.m1
        self.seed2 = (self.a2 * self.seed2) % self.m2

        # Combine the results
        z = (self.seed1 - self.seed2) % (self.m1 - 1)
        if z > 0:
            return z / self.m1
        else:
            return (self.m1 - 1) / self.m1

    def uniform(self, low=0.0, high=1.0):
        """Generate a uniform random number between low and high"""
        return low + (high - low) * self.combined_lcg()

    def normal(self, mean=0.0, stddev=1.0):
        """Generate a normal random number using the Box-Muller transform"""
        u1 = self.combined_lcg()
        u2 = self.combined_lcg()
        z0 = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        return mean + z0 * stddev

    def exponential(self, rate=1.0):
        """Generate an exponential random number"""
        u = self.combined_lcg()
        return -math.log(1 - u) / rate

    def poisson(self, lam):
        """Generate a Poisson random number using the acceptance-rejection method"""
        L = math.exp(-lam)
        k = 0
        p = 1.0
        while p > L:
            k += 1
            p *= self.combined_lcg()
        return k - 1

    def randint(self, a, b):
        """Generate a random integer N such that a <= N <= b"""
        if a > b:
            raise ValueError("Lower bound 'a' must be less than or equal to upper bound 'b'.")
        # Generate a uniform random number in [0, 1)
        u = self.combined_lcg()
        # Scale and shift to the range [a, b]
        return a + int(u * (b - a + 1))

    def triangular(self, low=0.0, high=1.0, mode=0.5):
        """
        Generate a random number from a triangular distribution.
        """
        if not (low <= mode <= high):
            raise ValueError("Mode must be between low and high.")

        u = self.combined_lcg()  # Generate a uniform random number in [0, 1)

        # Use the inverse transform method for triangular distribution
        if u < (mode - low) / (high - low):
            return low + math.sqrt(u * (high - low) * (mode - low))
        else:
            return high - math.sqrt((1 - u) * (high - low) * (high - mode))

    @classmethod
    def reset(cls, seed):
        """Reset the generator with a new seed."""
        cls._instance = None  # Clear the current instance
        return cls(seed)  # Create a new instance with the given seed


# Example usage:
if __name__ == '__main__':
    seed = 73426789
    rng = Generator(seed)
    print(rng.uniform(0, 10))  # Uniform random number between 0 and 10
    print(rng.normal(0, 1))  # Standard normal random number
    print(rng.exponential(1))  # Exponential random number with rate 1
    print(rng.poisson(3))  # Poisson random number with lambda 3

    # Demonstrating singleton behavior
    rng2 = Generator()
    print(rng is rng2)  # True, both rng and rng2 are the same instance
