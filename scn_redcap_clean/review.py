
# local imports

from . import config # global configs
from .csv_writer import CsvWriter
from .duplicate_accounts import DuplicateAccounts
from .clinical import Clinical
from .translation import Translation
from .step import Step


class Review:

    def __init__(self):
        self.archiver = CsvWriter()
        

    def translations(self, df, cols_to_translate):
        '''
        Outputs csv files for translation review 
        (1 file for record keeping and 1 file for manual override editting)
        '''
        translation = Translation(df)
        df = translation.review_df(cols_to_translate)
        if df is None:
            return None

        get_version = config.step_name_assembled

        # outputs csvs to review folder, a version to archive, and txt to overrides
        self.archiver.review_and_archive(df, Step.translated.process_name, get_version)

        return df



    def duplicates(self, df):
        ''' 
        Outputs csv files for duplicates review 
        (1 file for record keeping and 1 file for manual override editting)
        Duplicates are identified by dup_col w/ 'birthdate' as default. 
        '''
        duplicates = DuplicateAccounts(df)
        df = duplicates.review_df()
        if df is None:
            return None

        get_version = config.step_name_translated

        # outputs csvs to review folder, a version to archive, and txt to overrides
        self.archiver.review_and_archive(df, Step.duplicates.process_name, get_version)

        return df



    def clinical(self, orig_df):
        ''' 
        Outputs csv files for clinical review (Medications and Genomics)
        '''
        meds_df, genomics_df = Clinical(orig_df).review_dfs()

        if meds_df is None and genomics_df is None:
            return None

        get_version = config.step_name_duplicates

        if meds_df is not None:
            self.archiver.review_and_archive(meds_df, 'medications', get_version)

        if genomics_df is not None:
            self.archiver.review_and_archive(genomics_df, 'genomics', get_version)

        return meds_df, genomics_df
