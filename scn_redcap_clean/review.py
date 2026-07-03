
# local imports
from . import config # global configs
from .csv_writer import CsvWriter
from .duplicates import Duplicates
from .clinical import Clinical
from .translation import Translation


class Review:

    def __init__(self):
        self.archiver = CsvWriter()
        self.skip_str = 'skipped not needed'
        

    def translations(self, df, cols_to_translate):
        '''
        Outputs csv files for translation review 
        (1 file for record keeping and 1 file for manual override editting)
        '''
        translation = Translation(df)
        df = translation.review_df(cols_to_translate)
        if df is None:
            return None
        get_version = config.name_main1

        # outputs csvs to review folder, a version to archive, and txt to overrides
        self.archiver.review_and_archive(df, 'translations', get_version)

        return df



    def duplicates(self, df):
        ''' 
        Outputs csv files for duplicates review 
        (1 file for record keeping and 1 file for manual override editting)
        Duplicates are identified by dup_col w/ 'birthdate' as default. 
        '''
        duplicates = Duplicates(df)
        df = duplicates.review_df()
        if df is None:
            return None

        get_version = config.name_main2

        # outputs csvs to review folder, a version to archive, and txt to overrides
        self.archiver.review_and_archive(df, 'duplicates', get_version)

        return df



    def clinical(self, orig_df):
        ''' 
        Outputs csv files for clinical review (Medications and Genomics)
        '''
        meds_df, genomics_df = Clinical(orig_df).review_dfs()
        get_version = config.name_main3

        if meds_df is not None:
            self.archiver.review_and_archive(meds_df, 'medications', get_version)


        if genomics_df is not None:
            self.archiver.review_and_archive(genomics_df, 'genomics', get_version)

        return meds_df, genomics_df
