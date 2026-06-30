import os
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()

# local imports
from . import config  # global configs
from .duplicates import Duplicates
from .genomics import Genomics
from .meds import Medications
from .merging import Merging
from .overrides import Overrides
from .paths import Paths
from .standardize import Standardize
from .translation import Translation


class Cleaner:
    '''
    Data cleaning steps to run in order. Each outputs a main step csv to the steps folder and steps 1-4 output a review csv for the next step to the review folder.
    Each step also copies csv outputs as read-only in archive folder for version history.
    '''
    def __init__(self):
        self.paths = Paths(raw_data_source = config.raw_data_dir)


    def step_01_merge_raw_and_review_translations(self, csv_list):
        ''' 
        Creates a 'base' file and merges csvs in csv_list (if csvs are in raw folder).
        'base.csv' is created based on 'config.module' and 'config.raw_module_csv' settings and used to filter only participant_id's with at least 1 response in the specified 'config.module' list. 'Data Dictionary' configs must be set.
        '''
        
        merging = Merging(self.paths)
        df = merging.try_run_step_01(csv_list)
                
                        #### track merging.language_columns in new cleaned data dict?
        Translation(df, self).create_translations_for_review(merging.language_columns)
        
        return
    


    def step_02_translated_and_review_duplicates(self):
        ''' 
        Only inputs translations if 'translations_manual_override.csv' is in the overrides folder
        '''
        df = Overrides(2, Translation, self).try_run_step()

        Duplicates(df, self).create_duplicates_for_review()

        return
    
    

    def step_03_removed_duplicates_and_review_meds(self):
        '''
        Requires Ollama (local AI): 
        Download and install from: https://ollama.com/download

        If duplicates_manual_override is not in overrides folder, removes all but the last submission. (Duplicate based on birthdate) 
        Only inputs manual overrides if 'duplicates_manual_override.csv' is in the overrides folder (keep flag_shared column empty unless a birthdate is shared by 2 different individuals, only flag the shared birthdate individual with the smaller 'participant_id' number)
        
        Set medications (and supplements) configs before running 'config.med_text_cols'.

        Expect this step to take a few minutes...
        '''
        df = Overrides(3, Duplicates, self).try_run_step()

        Medications(df, self).create_medications_for_review()

        return



    def step_04_medications_and_review_genomics(self):
        '''
        Requires Ollama (local AI)

        The included 'config.meds_dict' csv should be updated based on the 'add_to_ref' column in 'medications_manual_override.csv' before running this step.

        medications_manual_override.csv' must be in the overrides folder 

        Medications/supplements are input as dummy variables by individual med/sup and by their 'functional_class'.
        '''
        df = Overrides(4, Medications, self).try_run_step()
        
        Genomics(df, self).create_genomics_for_review()

        return



    def step_05_genomics_and_standardize(self, age_units = ['days', 'months', 'years']):
        '''
        genomics_manual_override.csv' must be in the overrides folder 

        Splits protein variants (see configs), and maps regions based on UniProt regions
        
        Computes age based on each modules submission_date and the 'birthdate'

        (in progress... )
        Standardizes all 'config.age_dependent' columns
        Outputs descriptive statistics of cleaned csv
        '''
        overrides = Overrides(5, Genomics, self)

        df = overrides.try_input_override_df()
        df = Standardize(df, self).try_get_age(age_units)

        overrides.create_step_main_and_archive(df)

        return
