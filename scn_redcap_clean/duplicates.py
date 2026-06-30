import pandas as pd

# local imports
from . import config # global configs
from .archiver import Archiver
from .csv_kit import CsvKit
from . import utils
from . import console


class Duplicates:
    def __init__(self, df, delegate):
        self.df = df
        self.paths = delegate.paths
        self.archiver = Archiver(self.paths)
        self.csvkit = CsvKit()
        self.dup_col = config.filter_columns
        self.id_col = config.merge_on_id_column
        self.flag_shared_col = 'flag_shared_birthdate'



    def create_duplicates_for_review(self):
        ''' 
        Outputs csv files for duplicates review 
        (1 file for record keeping and 1 file for manual override editting)
        Duplicates are identified by dup_col w/ 'birthdate' as default. 
        '''
        df = self._get_duplicates_for_review_df()
        get_version = config.name_02_main

        # outputs csvs to review folder, a version to archive, and txt to overrides
        self.archiver.create_csvs_review_and_archive(df, 'duplicates', get_version)

        return df



    def try_input_override_df(self):
        ''' 
        Removes duplicates in dup_col keeping submission with highest id_col value 
        '''
        
        self.try_manual_override('duplicates_manual_override')
        df = self.clean_duplicates()
        self.df = self._drop_override_note_cols(df)
        
        return self.df



    def clean_duplicates(self):
        shared_birthdate_ids = self._get_flagged_ids()
        df = self._drop_duplicates(shared_birthdate_ids)
        self.df = df.sort_values(self.id_col).reset_index(drop = True)

        return self.df 



    def try_manual_override(self, override_filename):
        override_csv_path = self.csvkit.if_exists_path(
            override_filename, self.paths.overrides)        
        if override_csv_path is not None:
            self.df = self.csvkit.append_override_rows(override_csv_path, self.df)
        else:
            self._alert_no_override_file(override_filename) # skips manual overrides


    def _get_duplicates_for_review_df(self):
        sorted_duplicates_df = self._get_sorted_duplicates()
        utils.add_column_if_dne('override_explanation', sorted_duplicates_df)
        final_df = utils.add_column_if_dne(
            self.flag_shared_col, sorted_duplicates_df, '')
        
        return final_df



    def _get_sorted_duplicates(self):
        # df of all duplicates based on dup_col
        duplicates_df = self._get_duplicates_df()
        sorted_duplicates_df = self._sort_duplicates(duplicates_df)
        
        return sorted_duplicates_df 

    

    def _get_duplicates_df(self):
        if self.df is None:
            return
        
        duplicates = self.df.duplicated(self.dup_col, keep = False)
        duplicates_df = self.df[duplicates]

        return duplicates_df



    def _sort_duplicates(self, duplicates_df):
        sort_key = [self.dup_col, self.id_col]
        sorted_duplicates_df = (duplicates_df.sort_values(sort_key))

        return sorted_duplicates_df



    def _alert_no_override_file(self, override_filename):
        override_description = 'manual override duplicates'
        proceeding_message = f"with last submission for each duplicated '{self.dup_col}'"
        console.missing_override(
            override_filename, override_description, proceeding_message)  



    def _drop_duplicates(self, shared_birthdate_ids):
        ''' 
        Drops duplicates in dup_col keeping submission with highest id_col value 
        and restores original id_col order (ascending)
        '''

        df_sorted = self.df.sort_values(by = self.id_col, ascending = True)
        is_duplicate = df_sorted.duplicated(subset=self.dup_col, keep='last')
        is_protected = df_sorted[self.id_col].isin(shared_birthdate_ids)
        drop_mask = is_duplicate & ~is_protected

        self.df = df_sorted[~drop_mask].sort_values(
            by = self.id_col).reset_index(drop = True) # type: ignore
        
        return self.df
    
    

    def _keep_last_duplicate_only(self, not_shared_bday_df):
        not_shared_bday_df = self._sort_rows_by_id(not_shared_bday_df)
        clean_not_shared_bday_df = not_shared_bday_df.drop_duplicates(
            subset = self.dup_col, keep = 'last').copy()

        return clean_not_shared_bday_df
    


    def _sort_rows_by_id(self, not_shared_bday_df):
        not_shared_bday_df[self.id_col] = pd.to_numeric(
            not_shared_bday_df[self.id_col], errors = 'coerce')
        sorted_not_shared_bday_df = not_shared_bday_df.sort_values(self.id_col)

        return sorted_not_shared_bday_df



    def _get_flagged_ids(self):
        ''' Returns a set of IDs where the shared birthdate flag has been set '''
        if self.flag_shared_col not in self.df.columns:
            return set()
            
        cleaned_text = self.df[self.flag_shared_col].fillna('').astype(str).str.strip()
        
        is_not_blank = cleaned_text != ''

        is_flagged_id = set(self.df.loc[is_not_blank, self.id_col])
        
        return is_flagged_id



    def _drop_override_note_cols(self, df):
        drop_cols = ['override_explanation', self.flag_shared_col]
        self.df = df.drop(columns = drop_cols, errors = 'ignore')

        return self.df

