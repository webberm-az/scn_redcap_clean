import os
import certifi
os.environ['SSL_CERT_FILE'] = certifi.where()

# local imports
from . import paths
from .data import Data
from .proceed import Proceed


class Cleaner:
    '''
    Runs data cleaning steps. Each step outputs a main step csv to the 'steps' folder. Review csvs for the next step are output to the 'review' folder.
    cleaner.proceed.{step} continues the cleaning process.
    Each step also copies csv outputs as read-only to the '__archive__' folder for version history.
    '''
    def __init__(self, override = 'if_exists'):
        paths.setup_workspace()
        self.data = Data()
        self.proceed = Proceed(override)
        self.override = override


    def clean(self, override = 'default'):
        ''' 
        Creates a 'base' file and merges csvs in csv_list (if csvs are in the 'original_data_folder').
        '__base__.csv' is created based on 'config.module' and 'config.raw_module_csv' settings and used to filter only participant_id's with at least 1 response in the specified 'config.module' list. 'Data Dictionary' configs (and all required configs) must be set before running.

        Automatically runs the cleaning steps until a manual review is needed. 
        '''
        df = self.data.assemble()

        if override == 'default':
            override = self.override

        self.proceed.review_translations(df, self.data.language_cols, override)
