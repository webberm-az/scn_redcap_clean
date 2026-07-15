from enum import Enum

from . import config
from .clinical import Clinical
from .genomics import Genomics
from .duplicate_accounts import DuplicateAccounts
from .meds import Medications
from .translation import Translation

class Step(Enum):
    ''' Handles all cleaning steps. '''
    translated = (Translation.get_process_name(), Translation, config.step_name_translated)
    duplicates = (DuplicateAccounts.get_process_name(), DuplicateAccounts, config.step_name_duplicates)
    clinical = (Clinical.get_process_name(), Clinical, config.step_name_clinical)
    medications = (Medications.get_process_name(), Medications, None)
    genomics = (Genomics.get_process_name(), Genomics, None)
    
    
    def __init__(self, process_name, class_name, config_name):
        self.process_name = process_name
        self.class_name = class_name
        self.config_name = config_name
