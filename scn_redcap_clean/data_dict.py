from typing import Optional, List, Dict, cast

import pandas as pd # external import
from pandas import DataFrame

from . import config # global configs


class DataDict:

    def __init__(self, data_df: pd.DataFrame, dict_df: pd.DataFrame):
        self.data_df = data_df
        self.dict_df = dict_df
 

    def get_columns_by_type(
        self, 
        type: str, 
        match_type: bool = True, 
        dict_df: Optional[pd.DataFrame] = None) -> List[str]:
        current_dict_df = dict_df if dict_df is not None else self.dict_df
        is_type = current_dict_df[config.field_type_column] == type
        col_type = is_type if match_type else ~is_type
        
        col_match_list = current_dict_df[col_type][config.col_names_column].tolist()
        data_df = cast(DataFrame, self.data_df)
        col_match = [col for col in col_match_list if col in data_df.columns]
        
        return col_match



    def get_columns(
        self, type: str, modules: List[str]) -> Dict[str, List[str]]:
        '''Splits relevant data dictionary columns into safe, verified groups.'''
        
        module_dict_df = self.get_module_dict_df(modules)
        module_type_list = self.get_columns_by_type(type, dict_df = module_dict_df)
        module_other_list = self.get_columns_by_type(
            type, match_type = False, dict_df = module_dict_df)

        field_dict = {type: module_type_list, 'other': module_other_list}
        
        return field_dict



    def get_module_dict_df(self, modules: List[str]) -> pd.DataFrame:
        module_col_list = self.dict_df[config.module_column].isin(modules)
        module_dict_df = self.dict_df[module_col_list].copy()
        
        if not isinstance(module_dict_df, pd.DataFrame):
            raise TypeError(f"Expected pd.DataFrame, got {type(module_dict_df)}")
            
        return module_dict_df
