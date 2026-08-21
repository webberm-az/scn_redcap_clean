import pandas as pd

# local imports
from . import config, console, paths, utils # global configs
from .cleaning_step import CleaningStep
from .csv_kit import CsvKit
from .duplicate_map import DuplicateMap

class DuplicateAccounts(CleaningStep):

    def __init__(self, data):
        self.data = data.copy()
        self.csvkit = CsvKit()
        self.dup_col = config.filter_columns
        self.id_col = config.merge_on_id_column
        self.flag_shared_col = 'flag_shared_birthdate'
        self.protected_ids = set()
    
    @classmethod
    def get_process_name(cls):
        process_name = 'duplicate_accounts'

        return process_name

    @classmethod
    def get_map_csvname(cls):
        map_csvname = f'{cls.get_process_name()}_id_map'

        return map_csvname

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
        self._attempt_manual_override()

        full_data = self.data.copy()

        df = self._clean_duplicates()
        self.data = self._drop_override_note_cols(df)
        self.data[self.id_col] = utils.format_id_column(self.data[self.id_col])
        self._create_map(full_data)

        return self.data

    def _create_map(self, full_data):
        duplicate_map = DuplicateMap(full_data, self.data, self.protected_ids)
        duplicate_map.map_csvname = self.get_map_csvname()
        duplicate_map.write_to_file()

    def _format_review_df(self, sorted_df):
        utils.add_column_if_dne(self.flag_shared_col, sorted_df)

        dup_cols_first_df = utils.put_front_columns_first(
            sorted_df, self.id_col, self.flag_shared_col, self.dup_col)
        final_df_with_spacing = self._add_duplicate_row_pad(dup_cols_first_df)

        return final_df_with_spacing

    def _redorder_columns(self, data):
        dup_cols = [self.dup_col] if isinstance(self.dup_col, str) else self.dup_col
  
        front_columns = [self.id_col, self.flag_shared_col] + dup_cols + [utils.get_explanation_header()]
        
        valid_front_headers = utils.get_valid_headers(data, front_columns)
        
        remaining_headers = [col for col in data.columns if col not in valid_front_headers]
        
        data = data[valid_front_headers + remaining_headers]
        
        return data

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

    def _attempt_manual_override(self):
        override_filename = utils.get_manual_cvsname(self.get_process_name())
        override_csv_path = self.csvkit.path(override_filename, paths.OVERRIDES)        
        if override_csv_path is not None:
            self.data = self._append_override_rows(override_csv_path, self.data)
        else:
            self._alert_no_override_file(override_filename)

    def _append_override_rows(self, override_csv, df):
        ''' Adds all rows in override_csv to df '''
        override_df = self._get_matching_col_df(df, override_csv)
        override_df = override_df.dropna(subset = [config.merge_on_id_column])
        df = self._drop_duplicate_id(df, override_df)
        df = pd.concat([df, override_df], ignore_index = True)
        
        return df


    def _get_matching_col_df(self, df, override_csv):
        ''' Reads override_csv and loops through cols to match data types '''
        override_df = self.csvkit.robust_read(override_csv)
        for col in override_df.columns:
            override_df[col] = self._ensure_col_match(col, df, override_df)
        
        return override_df

    def _ensure_col_match(self, col, df, override_df):
        ''' Only loops columns that exists in the base df '''
        if col in df.columns:
            col_typed = self._try_col_match(col, df, override_df)
            return col_typed

        return override_df[col]

    def _try_col_match(self, col, df, override_df):
        try:
            if col == self.id_col: 
                return override_df[col].astype('float64')
            
            target_type = df[col].dtype
            
            if pd.api.types.is_integer_dtype(target_type):
                override_df[col] = override_df[col].astype('Int64')
            else:
                override_df[col] = override_df[col].astype(target_type)

            return override_df[col]
        
        except Exception as e:
            console.error(f'Could not match columns: {e}')
            return override_df[col]

    def _drop_duplicate_id(self, base_df, override_df):
        override_id = override_df[self.id_col].unique().tolist()
        
        is_duplicate_id = base_df[self.id_col].isin(override_id)
        
        df = base_df[~is_duplicate_id]

        return df

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
        date_match = pd.to_datetime(
            df_sorted[self.dup_col], errors = 'coerce', format = 'mixed')
        is_duplicate = date_match.duplicated(keep = 'last') & date_match.notna()
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
        drop_cols = [utils.get_explanation_header(), self.flag_shared_col]
        self.data = df.drop(columns = drop_cols, errors = 'ignore')

        return self.data
        