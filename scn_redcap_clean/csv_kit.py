from pathlib import Path
from typing import Optional, Union, cast

import pandas as pd # external import

# local imports
from . import config, console, utils

class CsvKit:

    def __init__(self) -> None:
        self.main_path = None
        self.read_only_path = None

    def robust_read(self, filepath: Union[str, Path]) -> pd.DataFrame:
        '''Reads a CSV file securely, handling mixed international encodings.'''
        # Encodings to try in order of likelihood for international Excel users
        encodings_to_try = ['utf-8-sig', 'cp1252', 'latin1', 'utf-16']
        low_memory = config.low_memory_read_csv
        
        for encoding in encodings_to_try:
            try:
                return pd.read_csv(
                    filepath, encoding = encoding, low_memory = low_memory)
            except (UnicodeDecodeError, LookupError):
                continue
        
        df = pd.read_csv(filepath, encoding = 'utf-8-sig', encoding_errors = 'replace')
        
        return df

    def ensure_suffix(self, csv_name: Union[str, Path]) -> Path:
        ''' Adds .csv to name if needed '''
        csv_name = utils.ensure_suffix(csv_name, '.csv')

        return csv_name

    def path_to_df(
        self, csv_name: Union[str, Path],  dir_path: Union[str, Path]
        ) -> Optional[pd.DataFrame]:
        ''' Returns df from csv_name and directory path '''
        if not self.path(csv_name, dir_path):
            return None
        
        df = self._try_read_csv()

        return df

    def path(
        self, csv_name: Union[str, Path], dir_path: Union[str, Path]) -> Optional[Path]:
        
        potential_path = Path(dir_path) / self.ensure_suffix(csv_name)
        if not potential_path.exists(): 
            return None
        
        self.main_path = potential_path
        
        return self.main_path

    def exists(self, csv_name: Union[str, Path], dir_path: Union[str, Path]) -> bool:
        potential_path = Path(dir_path) / self.ensure_suffix(csv_name)
        
        return potential_path.exists()

    def create_main(
            self, df, output_filename: Union[str, Path], dir_path: Union[str, Path]
            ) -> None:
        ''' Create editable csv to main_path '''
        if df is None:
            console.alert(f"'{output_filename}' is 'None'. No csv created.")
            return
        
        self.main_path = Path(dir_path) / self.ensure_suffix(output_filename)
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

    def instruct_missing_csv(
            self, filename: Union[str, Path], dir: Union[str, Path], role_name: str, 
            set_config) -> None:
        
        clean_filename = self.ensure_suffix(filename)
        raw_path = Path(dir) / f'{clean_filename}'
        console.alert_missing_config_file(dir, role_name, set_config, str(raw_path))

    def _try_read_csv(self):
        try:
            if self.main_path is None:
                return None

            path = cast(Path, self.main_path)
            df = self.robust_read(path)
            return df
        
        except Exception as e:
            console.error(f'{e}')
            return None
