import pandas as pd

# local imports
from . import config, console, paths, utils # global configs
from .cleaning_step import CleaningStep
from .csv_kit import CsvKit
from .duplicate_map import DuplicateMap


class DuplicateAccounts(CleaningStep):

    process_name = 'duplicate_accounts'
    map_csvname = f'{process_name}_id_map'

    def __init__(self, data):
        self.data = data.copy()
        self.csvkit = CsvKit()
        self.dup_col = config.filter_columns
        self.id_col = config.merge_on_id_column
        self.flag_shared_col = 'flag_shared_birthdate'
        self.process_name = DuplicateAccounts.process_name
        self.protected_ids = set()


    def review_df(self):
        sorted_duplicates_df = self._get_sorted_duplicates()
        if sorted_duplicates_df is None or sorted_duplicates_df.empty:
            self.skipped = True
            return None
        
        final_df = self._format_review_df(sorted_duplicates_df)
        
        return final_df



    def create_final_data(self):
        ''' 
        Removes duplicates in dup_col keeping submission with highest id_col value 
        '''
        self._attempt_manual_override(f'{self.process_name}_manual_override')

        full_data = self.data.copy()

        df = self._clean_duplicates()
        self.data = self._drop_override_note_cols(df)
        self.data[self.id_col] = utils.format_id_column(self.data[self.id_col])
        self._create_map(full_data)

        return self.data



    def _create_map(self, full_data):
        duplicate_map = DuplicateMap(full_data, self.data, self.protected_ids)
        duplicate_map.map_csvname = self.map_csvname
        duplicate_map.write_to_file()



    def _format_review_df(self, sorted_df):
        utils.add_column_if_dne('override_explanation', sorted_df)
        utils.add_column_if_dne(self.flag_shared_col, sorted_df)

        dup_cols_first_df = self._put_dup_cols_first(sorted_df)
        final_df_with_spacing = self._add_duplicate_row_pad(dup_cols_first_df)

        return final_df_with_spacing


    def _put_dup_cols_first(self, df):
        dup_cols = [self.dup_col] if isinstance(self.dup_col, str) else self.dup_col
        remaining_cols = [column for column in df.columns if column not in dup_cols]
        dup_cols_first_df = df[dup_cols + remaining_cols]
        
        return dup_cols_first_df



    def _add_duplicate_row_pad(self, df):
        grouped = df.groupby(self.dup_col, sort = False)
        spaced_duplicates = []
        
        blank_row = pd.DataFrame([{col: '' for col in df.columns}])
        
        for _, group in grouped:
            spaced_duplicates.append(group)
            spaced_duplicates.append(blank_row)
            
        spaced_df = pd.concat(spaced_duplicates, ignore_index = True)
        
        return spaced_df.iloc[:-1]



    def _clean_duplicates(self):
        self.protected_ids = self._get_flagged_ids()
        df = self._drop_duplicates()
        self.data = df.sort_values(self.id_col).reset_index(drop = True)

        return self.data 



    def _attempt_manual_override(self, override_filename):
        override_csv_path = self.csvkit.path(override_filename, paths.OVERRIDES)        
        if override_csv_path is not None:
            self.data = self.csvkit.append_override_rows(override_csv_path, self.data)
        else:
            self._alert_no_override_file(override_filename)



    def _get_sorted_duplicates(self):
        # df of all duplicates based on dup_col
        duplicates_df = self._get_duplicates_df()
        if duplicates_df is None:
            return None
        sorted_duplicates_df = self._sort_duplicates(duplicates_df)
        
        return sorted_duplicates_df 

    

    def _get_duplicates_df(self):
        if self.data is None:
            return None
        
        duplicates = self.data.duplicated(self.dup_col, keep = False)
        duplicates_df = self.data[duplicates]

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



    def _drop_duplicates(self):
        ''' 
        Drops duplicates in dup_col keeping submission with highest id_col value 
        and restores original id_col order (ascending)
        '''

        df_sorted = self.data.sort_values(by = self.id_col, ascending = True)
        is_duplicate = df_sorted.duplicated(subset = self.dup_col, keep = 'last')
        is_protected = df_sorted[self.id_col].isin(list(self.protected_ids))
        drop_mask = is_duplicate & ~is_protected

        self.data = df_sorted[~drop_mask].sort_values(
            by = self.id_col).reset_index(drop = True) # type: ignore
        
        return self.data
    
    

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
        if self.flag_shared_col not in self.data.columns:
            return set()
            
        cleaned_text = self.data[self.flag_shared_col].fillna('').astype(str).str.strip()
        
        is_not_blank = cleaned_text != ''

        is_flagged_id = set(self.data.loc[is_not_blank, self.id_col])
        
        return is_flagged_id



    def _drop_override_note_cols(self, df):
        drop_cols = ['override_explanation', self.flag_shared_col]
        self.data = df.drop(columns = drop_cols, errors = 'ignore')

        return self.data
        