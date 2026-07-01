# local imports
from . import config, console, utils # global configs
from .csv_writer import CsvWriter 
from .base_csv import BaseCSV
from .csv_kit import CsvKit
from .data_dict import DataDict
from .merge import Merge


class Data:

    def __init__(self, paths):
        self.paths = paths
        self.id_col = config.merge_on_id_column
        self.archiver = CsvWriter(self.paths)
        self.csvkit = CsvKit()
        self.language_cols = config.language_text_columns


    def assemble(self):
        df = self._get_merged_module_df()
        self.archiver.main_and_archive(
            df, config.name_main1, self.paths.steps)
        
        return df    


    def _get_merged_module_df(self, id_subset_csv = '__base__'):
        '''
        Creates a 'base' file and merges csvs in csv_list (if csvs are in raw folder).
        'base.csv' is created based on 'config.module' and 'config.raw_module_csv' settings and used to filter only participant_id's with at least 1 response in the specified 'config.module' list. 'Data Dictionary' configs must be set.
        '''
        if not config.csv_list:
            console.error('No data files in raw data folder to assemble')
            return None
        
        if id_subset_csv == '__base__':
            BaseCSV(self.paths).create()

        merged_df = Merge(self.language_cols, id_subset_csv).on_id()
        self._try_get_active_text_cols(merged_df)
        existing_filter_columns = self.get_existing_filter_columns(merged_df)

        if existing_filter_columns: 
            merged_df = utils.if_missing_drop_row(merged_df, existing_filter_columns)
        else: 
            console.error_missing(
                config.filter_columns, 'column(s) must be in at least 1 csv file.')

        if config.drop_na_col:
            merged_df = self._drop_entirely_empty_columns(merged_df)
            
        return merged_df



    def get_existing_filter_columns(self, merged_df):
        filter_cols = self.get_filter_columns()
        existing_filters = self.get_existing_columns(merged_df, filter_cols)  
        
        return existing_filters



    def get_filter_columns(self):
        if isinstance(config.filter_columns, str):
            filter_cols = [config.filter_columns] 
        else:
            filter_cols = config.filter_columns

        return filter_cols



    def get_existing_columns(self, merged_df, filter_cols):
        existing_filters = [col for col in filter_cols if col in merged_df.columns]

        return existing_filters



    def _try_get_active_text_cols(self, merged_df):
        if type(self.language_cols) is dict and self.language_cols.get("id") == "utils.auto":
            detected_cols = self._try_get_auto_text_cols(merged_df)
            self._get_active_auto_text_cols(detected_cols)

        else:
            self._format_text_cols()



    def _format_text_cols(self):
        if type(self.language_cols) is str:
            self.language_cols = [self.language_cols]
        else:
            self.language_cols = list(self.language_cols)



    def _get_active_auto_text_cols(self, detected_cols):
        not_active = config.no_translate_cols
        self.language_cols = [col for col in detected_cols if col not in not_active]



    def _try_get_auto_text_cols(self, merged_df):
        dict_df = self.csvkit.try_path_to_df(config.data_dict, self.paths.ref)

        if dict_df is not None:
            self.language_cols = self._get_auto_text_cols(merged_df, dict_df)
        else:
            self._alert_instruct()
            self.language_cols = []
        
        return self.language_cols
                


    def _get_auto_text_cols(self, merged_df, dict_df):
        field_dict = DataDict(data_df = merged_df, dict_df = dict_df)
        self.language_cols = field_dict.get_columns_by_type(
            type = 'text', match_type = True)

        return self.language_cols



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