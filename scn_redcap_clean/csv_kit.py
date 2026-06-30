from pathlib import Path
from typing import Optional, Union, List, cast

import pandas as pd # external import

# local imports
from . import utils
from . import console
from . import config


class CsvKit:

    def __init__(self) -> None:
        self.main_path = None
        self.read_only_path = None


    def add_suffix(self, csv_name: Union[str, Path]) -> Path:
        ''' Adds .csv to name if needed '''
        csv_name = Path(csv_name)
        csv_name = csv_name.with_suffix('.csv')

        return csv_name



    def try_convert_path_to_df(
        self, csv_name: Union[str, Path],  dir_path: Union[str, Path]
        ) -> Optional[pd.DataFrame]:
        ''' Returns df from csv_name and directory path '''
        if not self.if_exists_path(csv_name, dir_path):
            print('DEBUG NO PATH EXISTS')
            return None
        
        df = self._try_read_csv()

        return df



    def if_exists_path(
        self, csv_name: Union[str, Path], dir_path: Union[str, Path]) -> Optional[Path]:
        
        potential_path = Path(dir_path) / self.add_suffix(csv_name)
        if not potential_path.exists(): 
            return None
        
        self.main_path = potential_path
        
        return self.main_path



    def create_main(
            self, df, output_filename: Union[str, Path], dir_path: Union[str, Path]
            ) -> None:
        ''' Create editable csv to main_path '''
        if df is None:
            console.alert(f"'{output_filename}' is 'None'. No csv created.")
            return
        
        self.main_path = Path(dir_path) / self.add_suffix(output_filename)
        df.to_csv(self.main_path, index = False)
        console.file_saved_to(output_filename, self.main_path)



    def save_csv(self, df: pd.DataFrame, output_filepath: Union[str, Path]) -> None:
        ''' Create editable csv to main_path '''
        df.to_csv(output_filepath, index = False)
        console.action_to_path('File saved', output_filepath)



    def create_read_only(self, df: pd.DataFrame, path: Union[str, Path]) -> None:
        ''' Create read-only csv '''
        self.read_only_path = Path(path)
        df.to_csv(self.read_only_path, index = False)
        try: 
            self.read_only_path.chmod(0o444)
        except PermissionError: 
            pass
        


    def get_df_dropna_subset(
            self, raw_path: Union[str, Path], filename: Union[str, Path], 
            filter_subset: List[str]) -> pd.DataFrame:
        
        clean_filename = self.add_suffix(filename)
        df = self.robust_read_csv(Path(raw_path) / clean_filename)
        df = utils.if_missing_drop_row(df, filter_subset)

        return df



    def instruct_missing_csv(
            self, filename: Union[str, Path], dir: Union[str, Path], role_name: str, 
            set_config) -> None:
        
        clean_filename = self.add_suffix(filename)
        raw_path = Path(dir) / f'{clean_filename}'
        console.alert_missing_config_file(dir, role_name, set_config, str(raw_path))



    def append_override_rows(
            self, override_csv: Union[str, Path], df: pd.DataFrame) -> pd.DataFrame:
        ''' Adds all rows in override_csv to df '''
        override_df = self._get_matching_col_df(df, override_csv)
    
        df = pd.concat([df, override_df], ignore_index = True)
        
        return df



    def _get_matching_col_df(self, df, override_csv):
        ''' Reads override_csv and loops through cols to match data types '''
        override_df = self.robust_read_csv(override_csv)
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
            if col == config.merge_on_id_column: 
                return override_df[col].astype('float64')
            override_df[col] = override_df[col].astype(df[col].dtype)
            return override_df[col]
        
        except Exception as e:
            console.error(f'Could not match columns: {e}')
            return override_df[col]



    def _try_read_csv(self):
        try:
            if self.main_path is None:
                return None

            path = cast(Path, self.main_path)
            df = self.robust_read_csv(path)
            return df
        
        except Exception as e:
            console.error(f'{e}')
            return None


    def robust_read_csv(self, filepath: Union[str, Path]) -> pd.DataFrame:
        """Reads a CSV file securely, handling mixed international encodings."""
        # Encodings to try in order of likelihood for international Excel users
        encodings_to_try = ['utf-8-sig', 'cp1252', 'latin1', 'utf-16']
        
        for encoding in encodings_to_try:
            try:
                return pd.read_csv(filepath, encoding = encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        
        df = pd.read_csv(filepath, encoding = 'utf-8-sig', encoding_errors = 'replace')
        
        return df