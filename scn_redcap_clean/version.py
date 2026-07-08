from pathlib import Path

# local import
from .csv_kit import CsvKit
from . import utils


class Version:
    
    def __init__(self, dir_path):
        self.csvkit = CsvKit()
        self.dir_path = dir_path

    # archiver
    def get_output_version(self, fname, df):
        ''' Gets version suffix based on filenames in directory '''
        max_version = self.get_max_version(fname)

        max_version_if_duplicate = self._if_identical_and_get_version(df, fname, max_version)
        if max_version_if_duplicate is not None:
            return max_version_if_duplicate

        return max_version + 1


    # archiver
    def get_last_version_path(self, fname):
        ''' Create filename with version suffix based on filenames in directory '''
        fname = Path(fname).stem # strip any file extensions if needed
        version = self.get_max_version(fname)
        filepath = self.dir_path / f'{fname}_v{version:03d}.csv'

        return filepath



    def get_max_version(self, fname):
        current_files = Path(self.dir_path).glob(f'{fname}_v*.csv')
        max_version, _ = utils.get_max_file_index(current_files, self._extract_v_number)
        return max_version



    def _extract_v_number(self, filepath):
        ''' Gets each file version suffix '_v{number}' existing in the directory '''
        version_number = filepath.stem.rsplit('_v', 1)[-1]
        if version_number.isdigit():
            return int(version_number)



    def get_version_df(self, version, fname):
        filepath = self.dir_path / f'{fname}_v{version:03d}.csv'
        if filepath.exists():
            return self.csvkit.robust_read(filepath)



    def try_last_version_path(self, fname):
        try:
            last_version_path = self.get_last_version_path(fname)
            last_version_df = self.csvkit.robust_read(last_version_path)
            return last_version_df
        except Exception:
            return None


    
    def _if_identical_and_get_version(self, current_df, fname, max_version):
        if max_version == 0 or max_version is None:
            return None
        
        is_data_identical = self._try_is_identical(current_df, fname, max_version)
        if is_data_identical:
            return max_version
        
        return None



    def _try_is_identical(self, current_df, fname, max_version):
        try:
            last_df = self.get_version_df(max_version, fname)            
            is_identical = utils.is_df_identical(current_df, last_df)

            return is_identical
        
        except Exception:
            pass

        return False
