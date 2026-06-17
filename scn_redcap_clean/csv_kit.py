from pathlib import Path

import pandas as pd # external import

# local imports
from . import utils

class CsvKit:

    def __init__(self):
        self.main_path = None
        self.read_only_path = None


    def add_suffix(self, csv_name):
        ''' Adds .csv to name if needed '''
        csv_name = Path(csv_name)
        csv_name = csv_name.with_suffix('.csv')

        return csv_name



    def try_convert_path_to_df(self, csv_name, dir_path):
        ''' Returns df from csv_name and directory path '''
        if not self.if_exists_path(csv_name, dir_path):
            return None
        
        df = self._try_read_csv()

        return df



    def if_exists_path(self, csv_name, dir_path):
        potential_path = Path(dir_path) / self.add_suffix(csv_name)
        if not potential_path.exists(): 
            #print(f"\n | Missing |   {potential_path}\n")
            return None
        
        self.main_path = potential_path
        
        return self.main_path



    def create_main(self, df, output_filename, dir_path):
        ''' Create editable csv to main_path '''
        self.main_path = Path(dir_path) / self.add_suffix(output_filename)
        df.to_csv(self.main_path, index=False)
        print(f'\n{output_filename} file saved to: {self.main_path}')



    def _try_read_csv(self):
        try:
            df = pd.read_csv(self.main_path)
            return df
        
        except Exception:
            return None



    def create_read_only(self, df, path): # static function
        ''' Create read-only csv '''
        self.read_only_path = Path(path)
        df.to_csv(self.read_only_path, index=False)
        try: 
            self.read_only_path.chmod(0o444)
        except PermissionError: 
            pass
        


    def get_df_dropna_subset(self, raw_path, filename, filter_subset):
        clean_filename = self.add_suffix(filename)
        df = pd.read_csv(Path(raw_path) / clean_filename)
        df = utils.if_missing_drop_row(df, filter_subset)

        return df



    def make_duplicate_orig_cols(self, file_path, rep_cols):
        '''
        Creates df with duplicated rep_cols with '_orig' suffix added to col names
        '''
        df = pd.read_csv(file_path)
        for col in rep_cols: 
            df[f'{col}_orig'] = df[col]

        return df



    def append_override_rows(self, override_csv, df):
        ''' Adds all rows in override_csv to df '''
        override_df = self._get_matching_col_df(df, override_csv)
    
        df = pd.concat([df, override_df], ignore_index = True)

        return df



    def _get_matching_col_df(self, df, override_csv):
        ''' Reads override_csv and loops through cols to match data types '''
        override_df = pd.read_csv(override_csv)
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
            override_df[col] = override_df[col].astype(df[col].dtype)
            return override_df[col]
        except Exception:
            return override_df[col]



    def instruct_missing_csv(self, filename, dir, role_name, set_config):
        clean_filename = self.add_suffix(filename)
        raw_path = Path(dir) / f'{clean_filename}'
        print(
        f"\n | {role_name} Missing |   {raw_path}\n"
        f"set filename using  {set_config} = 'your_file_name'  and store in  '{dir}' folder"
        )