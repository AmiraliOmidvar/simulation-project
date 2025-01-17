class Counters:
    CURRENT_PATIENT_ID = 0

    def get_current_patient_id(self):
        self.CURRENT_PATIENT_ID += 1
        return self.CURRENT_PATIENT_ID
