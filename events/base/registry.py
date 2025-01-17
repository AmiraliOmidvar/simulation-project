from typing import Dict, Type

from events.admin_work_complete import AdminWorkComplete
from events.base.base import BaseEvent
from events.base.types import EventTypes
from events.ccu_departure import CCUDeparture
from events.emergency_departure import EmergencyDeparture
from events.general_departure import GeneralDeparture
from events.icu_departure import ICUDeparture
from events.lab_work_complete import LabWorkComplete
from events.move_to_or import MoveToOr
from events.or_clean_complete import OrCleanComplete
from events.operation_complete import OperationComplete
from events.patient_arrival_ordinary import PatientArrivalOrdinaryEvent
from events.patient_arrival_urgent import PatientArrivalUrgentEvent
from events.power_back import PowerBack
from events.power_out import PowerOut

registry: Dict[EventTypes, Type[BaseEvent]] = {
    EventTypes.PATIENT_ARRIVAL_ORDINARY: PatientArrivalOrdinaryEvent,
    EventTypes.PATIENT_ARRIVAL_URGENT: PatientArrivalUrgentEvent,
    EventTypes.ADMIN_WORK_COMPLETED: AdminWorkComplete,
    EventTypes.LAB_WORK_COMPLETE: LabWorkComplete,
    EventTypes.MOVE_TO_OR: MoveToOr,
    EventTypes.OPERATION_COMPLETE: OperationComplete,
    EventTypes.OR_CLEAN_UP_COMPLETE: OrCleanComplete,
    EventTypes.ICU_DEPARTURE: ICUDeparture,
    EventTypes.CCU_DEPARTURE: CCUDeparture,
    EventTypes.GENERAL_DEPARTURE: GeneralDeparture,
    EventTypes.EMERGENCY_DEPARTURE: EmergencyDeparture,
    EventTypes.POWER_BACK: PowerBack,
    EventTypes.POWER_OUT: PowerOut,
}
