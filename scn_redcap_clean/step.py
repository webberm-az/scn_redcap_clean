from enum import Enum

from . import config
from .clinical import Clinical
from .genomics import Genomics
from .duplicates import Duplicates
from .meds import Medications
from .translation import Translation

class Step(Enum):
    ''' Handles all cleaning steps. '''
    translated = (Translation.process_name, Translation, config.step_name_translated)
    duplicates = (Duplicates.process_name, Duplicates, config.step_name_duplicates)
    clinical = (Clinical.process_name, Clinical, config.step_name_clinical)
    medications = (Medications.process_name, Medications, None)
    genomics = (Genomics.process_name, Genomics, None)
    
    
    def __init__(self, process_name, class_name, config_name):
        self.process_name = process_name
        self.class_name = class_name
        self.config_name = config_name
