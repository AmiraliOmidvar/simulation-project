class Counters:
    """
    Manages various counters used throughout the simulation.

    This class is responsible for generating unique identifiers for patients and can be extended
    to include other counters as needed. It ensures that each patient receives a distinct ID,
    which is crucial for tracking and managing patient-related events within the simulation.

    Attributes:
        CURRENT_PATIENT_ID (int): A class-level counter that keeps track of the latest patient ID assigned.
            It starts at 0 and increments by 1 each time a new patient ID is requested.
    """

    CURRENT_PATIENT_ID = 0  # Class variable to track the current patient ID

    def get_current_patient_id(self):
        """
        Generates and returns a new unique patient ID.

        This method increments the `CURRENT_PATIENT_ID` counter by 1 and returns the updated value.
        It ensures that each patient is assigned a unique identifier, which is essential for
        distinguishing between different patients in the simulation.

        Returns:
            int: The newly assigned unique patient ID.
        """
        self.CURRENT_PATIENT_ID += 1  # Increment the patient ID counter
        return self.CURRENT_PATIENT_ID  # Return the new patient ID
