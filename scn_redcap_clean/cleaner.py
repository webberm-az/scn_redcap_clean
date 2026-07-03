import os
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()

# local imports
from . import paths 
from .data import Data
from .overrides import Overrides
from .review import Review
from .standardize import Standardize
from .step import Step


class Cleaner:
    '''
    Data cleaning steps to run in order. Each outputs a main step csv to the steps folder and steps 1-4 output a review csv for the next step to the review folder.
    Each step also copies csv outputs as read-only in archive folder for version history.
    '''
    def __init__(self):
        ''' 
        Creates a 'base' file and merges csvs in csv_list (if csvs are in raw folder).
        '__base__.csv' is created based on 'config.module' and 'config.raw_module_csv' settings and used to filter only participant_id's with at least 1 response in the specified 'config.module' list. 'Data Dictionary' configs must be set.
        '''
        paths.setup_workspace()
        self.overrides = Overrides()
        self.review = Review()


    def s1_translations(self):
        ''' Cleanly merges csvs using the 'base' file participant_id's '''
        data = Data()
        df = data.assemble()
                
           ## track data.language_cols in new cleaned data dict?
        self.review.translations(df, data.language_cols)
        
        return
    


    def s2_duplicates(self):
        ''' 
        Only inputs translations if 'translations_manual_override.csv' is in the overrides folder
        '''
        df = self.overrides.run(Step.translated)

        self.review.duplicates(df)

        return
    
    

    def s3_clinical(self):
        '''
        Requires Ollama (local AI): 
        Download and install from: https://ollama.com/download

        If duplicates_manual_override is not in overrides folder, removes all but the last submission. (Duplicate based on birthdate) 
        Only inputs manual overrides if 'duplicates_manual_override.csv' is in the overrides folder (keep flag_shared column empty unless a birthdate is shared by 2 different individuals, only flag the shared birthdate individual with the smaller 'participant_id' number)
        
        Set medications (and supplements) configs before running 'config.med_text_cols'.

        Expect this step to take a few minutes...
        '''
        df = self.overrides.run(Step.duplicates)

        self.review.clinical(df)

        return



    def standardize(self, age_units = ['days', 'months', 'years']):
        '''
        The included 'config.meds_dict' csv should be updated based on the 'add_to_ref' column in 'medications_manual_override.csv' before running this step.

        'medications_manual_override.csv' and 'genomics_manual_override.csv' must be in the overrides folder 

        Medications/supplements are input as dummy variables by individual med/sup and by their 'functional_class'.

        Splits protein variants (see configs), and maps regions based on UniProt regions
        
        Computes age based on each modules submission_date and the 'birthdate'
        (in progress... )
        Standardizes all 'config.age_dependent' columns
        Outputs descriptive statistics of cleaned csv
        '''
        df = self.overrides.get_df(Step.clinical)

        df = Standardize(df).try_get_age(age_units)

        self.overrides.create_csvs(df)
        
        return
