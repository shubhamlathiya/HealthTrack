from .userModel import *
from .staffModel import *
from .patientModel import *
from .departmentModel import *
from .LaboratoryTestReport import *
from .prescriptionModel import *
from .appointmentModel import *


# Explicitly list all models to ensure they're loaded
__all__ = [
    'User',
    'Staff',
    'Patient',
    'Department',
    'LaboratoryTestReport',
    'Prescription',
    'Appointment'
]