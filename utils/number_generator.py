import math


class Generator:
    """
    A Singleton class for generating random numbers using Combined Linear Congruential Generators (LCGs).

    This class implements a combined LCG approach to produce uniform random numbers, which are then
    used to generate various probability distributions such as uniform, normal, exponential, Poisson,
    integer, and triangular distributions. The Singleton pattern ensures that only one instance
    of the Generator exists throughout the simulation, maintaining consistent random number sequences.

    Attributes:
        _instance (Generator): The singleton instance of the Generator class.
        a1 (int): Multiplier for the first LCG.
        m1 (int): Modulus for the first LCG.
        a2 (int): Multiplier for the second LCG.
        m2 (int): Modulus for the second LCG.
        seed1 (int): Current seed/state for the first LCG.
        seed2 (int): Current seed/state for the second LCG.
        _seed (int): Initial seed provided during instantiation.
    """

    _instance = None  # Class-level variable to hold the singleton instance

    def __new__(cls, seed=1234):
        """
        Controls the creation of a new instance to ensure the Singleton pattern.

        If an instance of Generator does not exist, it creates one and initializes it.
        Otherwise, it returns the existing instance.

        Args:
            seed (int, optional): The initial seed for the random number generators. Defaults to 1234.

        Returns:
            Generator: The singleton instance of the Generator class.
        """
        if cls._instance is None:
            # Create the instance and initialize it with the seed
            cls._instance = super(Generator, cls).__new__(cls)
            cls._instance._initialize(seed)
            cls._instance._seed = seed
        return cls._instance

    def _initialize(self, seed):
        """
        Initializes the parameters and seeds for the combined LCGs.

        Sets up two separate LCGs with distinct multipliers and moduli. The seeds are derived
        from the provided seed to ensure variability between the two generators.

        Args:
            seed (int): The initial seed for the random number generators.
        """
        # Parameters for the two LCGs
        self.a1, self.m1 = 40014, 2147483563
        self.a2, self.m2 = 40692, 2147483399

        # Initialize seeds for both LCGs derived from the single seed
        self.seed1 = (seed % (self.m1 - 1)) + 1  # Ensure seed1 is in [1, m1-1]
        self.seed2 = ((seed // (self.m1 - 1)) % (self.m2 - 1)) + 1  # Ensure seed2 is in [1, m2-1]

    def combined_lcg(self):
        """
        Generates a combined uniform random number using two LCGs.

        This method updates both LCGs and combines their outputs to produce a more uniformly
        distributed random number, reducing the correlation inherent in a single LCG.

        Returns:
            float: A uniform random number in the range [0, 1).
        """
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
        """
        Generates a uniform random number within a specified range.

        Args:
            low (float, optional): The lower bound of the range. Defaults to 0.0.
            high (float, optional): The upper bound of the range. Defaults to 1.0.

        Returns:
            float: A uniform random number between low and high.
        """
        return low + (high - low) * self.combined_lcg()

    def normal(self, mean=0.0, stddev=1.0):
        """
        Generates a normally distributed random number using the Box-Muller transform.

        The Box-Muller transform converts two uniformly distributed random numbers into two
        independent standard normally distributed random numbers.

        Args:
            mean (float, optional): The mean of the normal distribution. Defaults to 0.0.
            stddev (float, optional): The standard deviation of the normal distribution. Defaults to 1.0.

        Returns:
            float: A normally distributed random number.
        """
        u1 = self.combined_lcg()
        u2 = self.combined_lcg()
        z0 = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        return mean + z0 * stddev

    def exponential(self, rate=1.0):
        """
        Generates an exponentially distributed random number.

        The exponential distribution is often used to model the time between independent events
        that happen at a constant average rate.

        Args:
            rate (float, optional): The rate parameter (λ) of the exponential distribution. Defaults to 1.0.

        Returns:
            float: An exponentially distributed random number.
        """
        u = self.combined_lcg()
        return -math.log(1 - u) / rate

    def poisson(self, lam):
        """
        Generates a Poisson-distributed random number using the acceptance-rejection method.

        The Poisson distribution models the number of events occurring within a fixed interval of time
        or space, given the average number of times the event occurs over that interval.

        Args:
            lam (float): The λ (lambda) parameter of the Poisson distribution, representing the average rate.

        Returns:
            int: A Poisson-distributed random number.
        """
        L = math.exp(-lam)
        k = 0
        p = 1.0
        while p > L:
            k += 1
            p *= self.combined_lcg()
        return k - 1

    def randint(self, a, b):
        """
        Generates a random integer within a specified inclusive range.

        Args:
            a (int): The lower bound of the range.
            b (int): The upper bound of the range.

        Raises:
            ValueError: If the lower bound 'a' is greater than the upper bound 'b'.

        Returns:
            int: A random integer N such that a <= N <= b.
        """
        if a > b:
            raise ValueError("Lower bound 'a' must be less than or equal to upper bound 'b'.")
        # Generate a uniform random number in [0, 1)
        u = self.combined_lcg()
        # Scale and shift to the range [a, b]
        return a + int(u * (b - a + 1))

    def triangular(self, low=0.0, high=1.0, mode=0.5):
        """
        Generates a random number from a triangular distribution.

        The triangular distribution is defined by a lower limit, an upper limit, and a mode (peak).

        Args:
            low (float, optional): The lower limit of the distribution. Defaults to 0.0.
            high (float, optional): The upper limit of the distribution. Defaults to 1.0.
            mode (float, optional): The mode (peak) of the distribution. Defaults to 0.5.

        Raises:
            ValueError: If the mode is not between low and high.

        Returns:
            float: A random number from the triangular distribution.
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
        """
        Resets the Generator instance with a new seed.

        This method clears the existing singleton instance and creates a new one with the provided seed,
        ensuring that the random number sequence starts anew.

        Args:
            seed (int): The new seed for the random number generators.

        Returns:
            Generator: The new singleton instance of the Generator class.
        """
        cls._instance = None  # Clear the current instance
        return cls(seed)  # Create a new instance with the given seed


# Example usage:
if __name__ == '__main__':
    seed = 73426789
    rng = Generator(seed)
    print(rng.uniform(0, 10))       # Uniform random number between 0 and 10
    print(rng.normal(0, 1))         # Standard normal random number
    print(rng.exponential(1))       # Exponential random number with rate 1
    print(rng.poisson(3))           # Poisson random number with lambda 3
    print(rng.randint(1, 100))      # Random integer between 1 and 100
    print(rng.triangular(0, 10, 5)) # Triangular random number between 0 and 10 with mode at 5

    # Demonstrating singleton behavior
    rng2 = Generator()
    print(rng is rng2)  # True, both rng and rng2 are the same instance
