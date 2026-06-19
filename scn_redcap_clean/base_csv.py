from pathlib import Path

import pandas as pd

from .csv_kit import CsvKit
from .field_dict import FieldDict
from . import config # global configs


class BaseCSV:

    def __init__(self, paths):
        self.paths = paths
        self.csvkit = CsvKit()
        self.dict_df = self.csvkit.try_convert_path_to_df(config.data_dict, Path('ref'))
        self.data_df = self.csvkit.try_convert_path_to_df(config.raw_module_csv, config.raw_data_dir)
        self.modules = config.modules
        self.field_dict = FieldDict(self.data_df, self.dict_df)


    def output_base_csv_to_raw(self):
        base_df = self.filter_id_by_modules()

        if base_df is not None:
            self._save_and_report(base_df)
            


    def filter_id_by_modules(self):
        if self._is_data_missing():
            return None

        module_columns = self.field_dict.get_module_columns_by_type(
            type = 'checkbox', modules = self.modules)
        
        checkbox_cols = module_columns['checkbox']
        other_cols = module_columns['other']

        base_df = self.get_rows_at_least_one_reponse(checkbox_cols, other_cols)

        return base_df



    def _is_data_missing(self):
        if self.dict_df is not None and self.data_df is not None:
            return False

        self._alert_missing_files()
            
        return True



    def _alert_missing_files(self):
        if self.dict_df is None:
            self.csvkit.instruct_missing_csv(
                config.data_dict, 'ref', 'Data Dictionary', 'config.data_dict')

        if self.data_df is None:
            self.csvkit.instruct_missing_csv(
                config.raw_module_csv, 'raw', 'Raw Module Data', 'config.raw_module_csv')



    def get_rows_at_least_one_reponse(self, checkbox_cols, other_cols):
        is_row_all_zero_checkbox = self._are_all_checkboxes_zero(checkbox_cols)
        is_row_all_na_other = self._are_all_text_fields_na(other_cols)
        
        completely_empty_rows = is_row_all_zero_checkbox & is_row_all_na_other
        
        rows_at_least_one_reponse = self.data_df[~completely_empty_rows].copy()
        
        return rows_at_least_one_reponse



    def _are_all_checkboxes_zero(self, columns):
        if not columns:
            entire_row_zero = pd.Series(True, index = self.data_df.index)
            return entire_row_zero
        
        entire_row_zero = self._get_checkbox_all_zero(columns)
        
        return entire_row_zero



    def _are_all_text_fields_na(self, columns):
        if not columns: # no other columns in module
            entire_row_na = pd.Series(True, index = self.data_df.index)
            return entire_row_na

        entire_row_na = self._get_other_all_na(columns)
        
        return entire_row_na



    def _save_and_report(self, df: pd.DataFrame):
        self.csvkit.create_main(df, 'base', config.raw_data_dir)
        print(f'Raw base file response count: {len(df)}\n')



    def _get_checkbox_all_zero(self, columns):
        always_filled_cols_df = self.data_df[columns]
        is_zero_or_na_col = always_filled_cols_df.fillna(0) == 0
        entire_row_zero = (is_zero_or_na_col).all(axis=1)

        return entire_row_zero



    def _get_other_all_na(self, columns):
        other_cols_df = self.data_df[columns]
        is_na_col = other_cols_df.isna()
        entire_row_na = is_na_col.all(axis=1)

        return entire_row_na
