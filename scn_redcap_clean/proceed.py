# local imports
from . import config, console
from .step import Step
from .step_manager import StepManager
from .overrides import Overrides
from .review import Review
from .standardize import Standardize

class Proceed:

    def __init__(self):
        self.step_manager = StepManager()
        self.overrides = Overrides()
        self.review = Review()
        self.use_existing_overrides = True


    def translated(self, skip_input = False):
        '''
        Proceeds with clean from translated override.
        Only inputs translations if 'translations_manual_override.csv' is in the overrides folder
        '''
        if skip_input:
            df = self.step_manager.get_last_step_df(Step.translated.config_name)
        else:
            df = self.overrides.run(Step.translated)
        
        self._review_duplicates(df)



    def duplicates(self, keep_all = False):
        '''
        Requires Ollama (local AI): 
        Download and install from: https://ollama.com/download

        Proceeds with clean from duplicates override.
        If duplicates_manual_override is not in overrides folder, removes all but the last submission. (Duplicate based on 'config.filter_columns' with default birthdate) 
        Only inputs manual overrides if 'duplicates_manual_override.csv' is in the overrides folder (keep flag_shared column empty unless a 'config.filter_columns' is shared by 2 different individuals, only flag the shared 'config.filter_columns' individual with the smaller 'participant_id' number)

        If 'keep_all = True' all duplicates will remain unchanged (no override occurs). 

        Continues to prepare medications and genomics for review using Ollama (local AI)
        Expect this step to take a few minutes...
        '''
        if keep_all:
            df = self.step_manager.get_last_step_df(Step.duplicates.config_name)
        else:
            df = self.overrides.run(Step.duplicates)

        self._review_clinical(df)
        
        

    def clinical(self, skip_input = False):
        '''
        The included 'config.meds_dict' csv should be updated based on the 'add_to_ref' column in 'medications_manual_override.csv' before running this step.

        'medications_manual_override.csv' and 'genomics_manual_override.csv' must be in the overrides folder

        Medications/supplements are input as dummy variables by individual med/sup and by their 'functional_class'.

        Splits protein variants (see configs), and maps regions based on UniProt regions
        
        Computes age based on each modules 'submission_date' and the 'birthdate'
        '''
        if skip_input:
            df = self.step_manager.get_last_step_df(Step.clinical.config_name)
        else:
            df = self.overrides.run(Step.clinical)
        
        self._input_age(df)
        


    def review_translations(self, df, lang_cols):
        if self._is_input_override(Step.translated):
            self.translated()
            return

        review_translations = self.review.translations(df, lang_cols)

        if review_translations is not None:
            console.move_to_overrides('cleaner.proceed.translated()')
            return

        self._review_duplicates(df)


    
    def _review_duplicates(self, df):
        if self._is_input_override(Step.duplicates):
            self.duplicates()
            return

        review_duplicates = self.review.duplicates(df)
        if review_duplicates is not None:
            console.move_to_overrides('cleaner.proceed.duplicates()')
            return
        
        self._review_clinical(df)


    
    def _review_clinical(self, df):
        if self._is_input_override(Step.medications) and self.overrides.exists(
            Step.genomics):
            
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



    def _is_input_override(self, step_enum):
        if self.use_existing_overrides and self.overrides.exists(step_enum):
            return True
        
        return False
        