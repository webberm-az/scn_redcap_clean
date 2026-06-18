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
        self.df = self._drop_duplicates_and_sort()
        
        return self.df



    def try_manual_override(self, override_filename):
        override_csv_path = self.csvkit.if_exists_path(override_filename, self.paths.overrides)
        if override_csv_path is not None:
            self.df = self.csvkit.append_override_rows(override_csv_path, self.df)
        else:
            self._alert_no_override_file(override_filename) # skips manual overrides


    def _get_duplicates_for_review_df(self):
        sorted_duplicates_df = self._get_sorted_duplicates()
        utils.add_column_if_dne('override_explanation', sorted_duplicates_df)
        final_df = utils.add_column_if_dne('is_shared_birthdate', sorted_duplicates_df, 'No')
        
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
        console.missing_override(override_filename, override_description, proceeding_message)  



    def _drop_duplicates_and_sort(self):
        ''' 
        Drops duplicates in dup_col keeping submission with highest id_col value 
        and restores original id_col order (ascending)
        '''
        self._keep_last_duplicate_only()
        self.df = self.df.sort_values(self.id_col).reset_index(drop = True)

        return self.df
    


    def _keep_last_duplicate_only(self):
        self._sort_rows_by_id()
        self.df = self.df.drop_duplicates(subset = self.dup_col, keep = 'last').copy()
    


    def _sort_rows_by_id(self):
        self.df[self.id_col] = pd.to_numeric(self.df[self.id_col], errors = 'coerce')
        self.df = self.df.sort_values(self.id_col)
