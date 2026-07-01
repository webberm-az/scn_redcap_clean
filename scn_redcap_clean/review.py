
# local imports
from . import config # global configs
from .csv_writer import CsvWriter
from .duplicates import Duplicates
from .genomics import Genomics
from .meds import Medications
from .translation import Translation


class Review:

    def __init__(self, df, paths):
        self.df = df
        self.paths = paths
        self.archiver = CsvWriter(self.paths)
        

    def translations(self, cols_to_translate):
        '''
        Outputs csv files for translation review 
        (1 file for record keeping and 1 file for manual override editting)
        '''
        df = Translation(self.df, self.paths, cols_to_translate).review_df()
        get_version = config.name_main1

        # outputs csvs to review folder, a version to archive, and txt to overrides
        self.archiver.review_and_archive(df, 'translations', get_version)

        return df



    def duplicates(self):
        ''' 
        Outputs csv files for duplicates review 
        (1 file for record keeping and 1 file for manual override editting)
        Duplicates are identified by dup_col w/ 'birthdate' as default. 
        '''
        df = Duplicates(self.df, self.paths).review_df()
        get_version = config.name_main2

        # outputs csvs to review folder, a version to archive, and txt to overrides
        self.archiver.review_and_archive(df, 'duplicates', get_version)

        return df



    def clinical(self):
        ''' 
        Outputs csv files for duplicates review 
        (1 file for record keeping and 1 file for manual override editting)
        Duplicates are identified by dup_col w/ 'birthdate' as default. 
        '''
        df = Medications(self.df, self.paths).review_df()
        get_version = config.name_main3
        
        if df is None:
            df = self.df
        else:
            # outputs csvs to review folder, a version to archive, and txt to overrides
            self.archiver.review_and_archive(df, 'medications', get_version)

        df = self._genomics(get_version)

        return df



    def _genomics(self, get_version):
        ''' 
        Outputs csv files for genomic variants review 
        (1 file for record keeping and 1 file for manual override editting)
        Genomic variants are extracted using local AI Ollama
        '''
        df = Genomics(self.df, self.paths).review_df()

        # outputs csvs to review folder, a version to archive, and txt to overrides
        self.archiver.review_and_archive(df, 'genomics', get_version)

        return df
