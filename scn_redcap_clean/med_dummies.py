import pandas as pd

from . import config

class MedDummies:
    def __init__(self, main_data, override_data):
        self.main_data = main_data.copy()
        self.override_data = override_data.copy()
        self._id_col = config.merge_on_id_column
        self._class_prefix = 'class'
        self._temp_prefix = 'NEW_DUMMY'
        self.main_header = config.main_header
        self.function_header = config.function_header
        self.from_col = config.from_col

    def merged_data(self): # called in OverridePivot
        binary_data = self._get_binary_data()
        full_data = self._merge_full_data(binary_data)
        full_data = self._clean_full_data(full_data)

        return full_data

    def _get_binary_data(self):
        class_binary = self._get_class_dummies_data()
        med_binary = self._get_med_dummies_data()    
        binary_data = self._get_merged_dummies_data(class_binary, med_binary)

        return binary_data

    def _get_class_dummies_data(self):
        suffix_col_header = self._suffix_column_header(self.function_header)
        class_dummies = pd.get_dummies(suffix_col_header, prefix = self._class_prefix)
        class_dummies[self._id_col] = self.override_data[self._id_col].values
        class_matrix = class_dummies.groupby(self._id_col).max()
        
        return class_matrix

    def _get_med_dummies_data(self):
        suffix_col_header = self._suffix_column_header(self.main_header)
        med_dumms = pd.crosstab(
            index = self.override_data[self._id_col], columns = suffix_col_header)
        med_dumms.columns = [f"{self._temp_prefix}_{col}" for col in med_dumms.columns]
        med_dummies_data = (med_dumms > 0).astype(int)

        return med_dummies_data

    def _suffix_column_header(self, new_header):
        suffix = self.override_data[new_header].astype(str) + '_' + self.override_data[self.from_col].astype(str)

        return suffix

    def _get_merged_dummies_data(self, d1, d2):
        binary_data = pd.merge(
            d1, d2, left_index = True, right_index = True, how = 'outer').reset_index()

        return binary_data

    def _merge_full_data(self, binary_data):
        full_data = pd.merge(
            self.main_data, binary_data, on = self._id_col, how = "left")
        
        new_binary_cols = self._get_all_new_binary_cols(binary_data)
        full_data[new_binary_cols] = full_data[new_binary_cols].fillna(0).astype(int)

        return full_data

    def _get_all_new_binary_cols(self, binary_data):
        new_binary_cols = [
            col for col in binary_data.columns 
            if col.startswith((f'{self._class_prefix}_', f'{self._temp_prefix}_'))]
        
        return new_binary_cols

    def _clean_full_data(self, full_data):
        full_data.columns = [
            col.replace(f'{self._temp_prefix}_', '').replace(' ', '_') 
            for col in full_data.columns]
        
        return full_data
