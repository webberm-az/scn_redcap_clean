import pandas as pd

# local imports
from . import config, console, paths, utils # global configs
from .csv_writer import CsvWriter 
from .csv_kit import CsvKit
from .data_dict import DataDict
from .merge import Merge



class Data:

    def __init__(self):
        self.id_col = config.merge_on_id_column
        self.csv_writer = CsvWriter()
        self.csvkit = CsvKit()
        self.lang_col_headers = config.language_text_columns

    def assemble(self):
        '''
        Cleanly merges csvs using the 'base' file participant_id's and saves to steps and archive folders
        '''
        df = self._get_merged_module_df()
        self.csv_writer.main_and_archive(
            df, f'1_{config.step_name_assembled}', paths.STEPS)
        
        return df    

    def _get_merged_module_df(self):
        if not config.csv_list:
            console.error('No data files in raw data folder to assemble')
            return None
        
        data = Merge(self.lang_col_headers, config.id_subset_csv).on_id()
        self._get_active_text_cols(data)
        existing_filter_columns = self.get_existing_filter_columns(data)

        if existing_filter_columns: 
            data = utils.if_missing_drop_row(data, existing_filter_columns)
        else: 
            console.error_missing(
                config.filter_columns, 'column(s) must be in at least 1 csv file.')

        if config.drop_na_col:
            data = self._drop_entirely_empty_columns(data)
            
        self.lang_col_headers = utils.get_valid_headers(data, self.lang_col_headers)

        return data

    def get_existing_filter_columns(self, merged_df):
        ''' Checks 'config.filter_columns' and returns the list of existing columns '''
        filter_headers = self.get_filter_columns()
        existing_filters = self.get_existing_columns(merged_df, filter_headers)  
        
        return existing_filters

    def get_filter_columns(self):
        if isinstance(config.filter_columns, str):
            filter_cols = [config.filter_columns] 
        else:
            filter_cols = config.filter_columns

        return filter_cols

    def get_existing_columns(self, data, filter_headers): # add console if missing col
        existing_filters = utils.get_valid_headers(data, filter_headers)

        return existing_filters

    def _get_active_text_cols(self, data):
        is_auto_detect = type(self.lang_col_headers) is dict and \
            self.lang_col_headers.get("id") == "utils.auto"
        
        if is_auto_detect:
            detected_cols = self._attempt_get_auto_text_cols(data)
            self._get_active_auto_text_cols(detected_cols)
            self.lang_col_headers = utils.filter_alpha_columns(
                data, self.lang_col_headers)

        else:
            self._format_text_cols()
        
    def _format_text_cols(self):
        if type(self.lang_col_headers) is str:
            self.lang_col_headers = [self.lang_col_headers]
        else:
            self.lang_col_headers = list(self.lang_col_headers)

    def _get_active_auto_text_cols(self, detected_columns):
        not_active = config.no_translate_cols
        self.lang_col_headers = [
            header for header in detected_columns if header not in not_active]
        
    def _attempt_get_auto_text_cols(self, merged_df):
        dict_df = self.csvkit.path_to_df(config.data_dict, paths.REF)

        if dict_df is not None:
            self.lang_col_headers = self._get_auto_text_cols(merged_df, dict_df)
        else:
            self._alert_instruct()
            self.lang_col_headers = []
        
        return self.lang_col_headers

    def _get_auto_text_cols(self, merged_df, dict_df):
        field_dict = DataDict(data_df = merged_df, dict_df = dict_df)
        self.lang_col_headers = field_dict.get_columns_by_type(
            type = 'text', match_type = True)

        return self.lang_col_headers

    def _alert_instruct(self):
        console.alert_missing_config_file('ref', 'Data Dictionary', 'config.data_dict')

    def _drop_entirely_empty_columns(self, merged_df):
        is_empty = merged_df.apply(self._is_column_empty)
        is_id_col = (merged_df.columns == self.id_col)
        cols_to_keep = merged_df.columns[~is_empty | is_id_col]
    
        active_columns_df = merged_df[cols_to_keep].copy()
        
        return active_columns_df

    def _is_column_empty(self, col_df):
        cleaned_col_df = self._strip_whitespace_if_object(col_df)
        
        not_na_column = col_df.notna() & (cleaned_col_df != '')
        not_entirely_na_column = not_na_column.any()
        empty_column = not not_entirely_na_column

        return empty_column

    def _strip_whitespace_if_object(self, col_df):
        if col_df.dtype == 'object':
            return col_df.astype(str).str.strip()
        
        return col_df
