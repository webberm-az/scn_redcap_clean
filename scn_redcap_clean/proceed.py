# local imports
from . import config, console
from .step import Step
from .step_manager import StepManager
from .overrides import Overrides
from .review import Review
from .standardize import Standardize

class Proceed:

    def __init__(self, override = 'if_exists'):
        self.step_manager = StepManager()
        self.overrides = Overrides()
        self.review = Review()
        self.override = override


    def translated(self, action = 'override', override = 'default'):
        '''
        Proceeds with clean from translated override.
        Only inputs translations if 'translations_manual_override.csv' is in the overrides folder

        If action = None or action = 'skip' no translations will be input from the overrides folder. 
        '''
        if action in (None, 'skip'):
            df = self.step_manager.get_last_step_df(Step.translated.config_name)
        else:
            df = self.overrides.run(Step.translated)

        if override == 'default':
            override = self.override
        
        self._review_duplicates(df, override)



    def duplicates(self, action = 'override', override  = 'default'):
        '''
        Requires Ollama (local AI): 
        Download and install from: https://ollama.com/download

        Proceeds with clean from duplicates override.
        If duplicates_manual_override is not in overrides folder, removes all but the last submission. (Duplicate based on 'config.filter_columns' with default birthdate) 
        Only inputs manual overrides if 'duplicates_manual_override.csv' is in the overrides folder (keep flag_shared column empty unless a 'config.filter_columns' is shared by 2 different individuals, only flag the shared 'config.filter_columns' individual with the smaller 'participant_id' number)

        If action = 'keep' all duplicates will remain unchanged (no override occurs). 


        Continues to prepare medications and genomics for review using Ollama (local AI)

        Expect this step to take a few minutes...
        '''
        if action == 'keep':
            df = self.step_manager.get_last_step_df(Step.duplicates.config_name)
        else:
            df = self.overrides.run(Step.duplicates)

        if override == 'default':
            override = self.override
        
        self._review_clinical(df, override)
        
        

    def clinical(self, action = 'override'):
        '''
        The included 'config.meds_dict' csv should be updated based on the 'add_to_ref' column in 'medications_manual_override.csv' before running this step.

        'medications_manual_override.csv' and 'genomics_manual_override.csv' must be in the overrides folder

        Medications/supplements are input as dummy variables by individual med/sup and by their 'functional_class'.

        Splits protein variants (see configs), and maps regions based on UniProt regions
        
        Computes age based on each modules 'submission_date' and the 'birthdate'
        '''
        if action == 'skip':
            df = self.step_manager.get_last_step_df(Step.clinical.config_name)
        else:
            df = self.overrides.run(Step.clinical)
        
        self._input_age(df)
        


    def review_translations(self, df, lang_cols, override = 'default'):
        if override == 'default':
            override = self.override

        if self._is_input_override(Step.translated, override):
            self.translated(override = override)
            return

        review_translations = self.review.translations(df, lang_cols)

        if review_translations is not None:
            console.move_to_overrides('cleaner.proceed.translated()')
            return

        self._review_duplicates(df, override)


    
    def _review_duplicates(self, df, override = 'default'):
        if override == 'default':
            override = self.override

        if self._is_input_override(Step.duplicates, override):
            self.duplicates(override = override)
            return

        review_duplicates = self.review.duplicates(df)
        if review_duplicates is not None:
            console.move_to_overrides('cleaner.proceed.duplicates()')
            return
        
        self._review_clinical(df, override)


    
    def _review_clinical(self, df, override = 'default'):
        if override == 'default':
            override = self.override
            
        if self._is_input_override(
            Step.medications, override) and self.overrides.exists(Step.genomics):
            
            self.clinical()
            return

        review_clinical = self.review.clinical(df)
        
        if review_clinical is not None:
            console.move_to_overrides('cleaner.proceed.clinical()')
            return

        self._input_age(df)



    def _input_age(self, df):
        df = Standardize(df).try_get_age(config.age_units)

        self.overrides.create_csvs(df)


    def _is_input_override(self, step_enum, override):
        if override == 'if_exists' and self.overrides.exists(step_enum):
            return True
        
        return False
        