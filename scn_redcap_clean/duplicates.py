import pandas as pd

# local imports
from . import config # global configs
from .csv_kit import CsvKit
from . import utils
from . import console


class Duplicates:
    def __init__(self, df, paths, archiver):
        self.df = df
        self.dup_col = config.filter_columns
        self.id_col = config.merge_on_id_column
        self.paths = paths
        self.archiver = archiver
        self.csvkit = CsvKit()
        self.shared_col = 'flag_shared_birthdate'


    def get_duplicates_for_review(
            self, 
            main_filename = 'duplicates_manual_override', 
            archive_filename = 'duplicates_for_review'):
        ''' 
        Outputs csv files for duplicates review 
        (1 file for record keeping and 1 file for manual override editting)
        Duplicates are identified by dup_col w/ 'birthdate' as default. 
        '''
        final_duplicates_df = self._get_duplicates_for_review_df()

        # outputs csvs to review folder and a version to archive
        self.archiver.create_csvs_main_and_archive(
            final_duplicates_df, 
            main_filename, 
            self.paths.review, 
            archive_filename,
            filename_get_version = config.name_02_main)
        
        content = 'Additional explanations: \n'
        utils.write_txt_file(content, main_filename, self.paths.overrides)

        return final_duplicates_df



    def clean_duplicates(self, override_filename):
        ''' Removes duplicates in dup_col keeping submission with highest id_col value '''
        self.try_manual_override(override_filename)

        shared_birthdate_ids = self._get_shared_bday_ids()

        self.df = self._drop_duplicates_and_sort(shared_birthdate_ids)
        
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
        final_df = utils.add_column_if_dne(self.shared_col, sorted_duplicates_df, '')
        
        return final_df



    def _get_sorted_duplicates(self):
        # df of all duplicates based on dup_col
        duplicates_df = self._get_duplicates_df()
        sorted_duplicates_df = self._sort_duplicates(duplicates_df)
        
        return sorted_duplicates_df 

    

    def _get_duplicates_df(self):
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



    def _drop_duplicates_and_sort(self, shared_birthdate_ids):
        ''' 
        Drops duplicates in dup_col keeping submission with highest id_col value 
        and restores original id_col order (ascending)
        '''
        shared_bday_id = self.df[self.id_col].isin(shared_birthdate_ids)
        shared_bday_ids_df = self.df[shared_bday_id].copy()
        not_shared_bday_df = self.df[~shared_bday_id].copy()

        clean_not_shared_bday_df = self._keep_last_duplicate_only(not_shared_bday_df)

        self.df = pd.concat(
            [clean_not_shared_bday_df, shared_bday_ids_df], ignore_index=True)

        self.df = self.df.sort_values(self.id_col).reset_index(drop=True)
        
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

    def _get_shared_bday_ids(self):
        ''' Returns a set of IDs where the shared birthdate flag has been set '''
        if self.shared_col not in self.df.columns:
            return set()
            
        cleaned_text = self.df[self.shared_col].fillna('').astype(str).str.strip()
        
        is_not_blank = cleaned_text != ''

        shared_birthdate_ids = set(self.df.loc[is_not_blank, self.id_col])
        
        return shared_birthdate_ids