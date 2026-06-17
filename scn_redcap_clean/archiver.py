from pathlib import Path

import pandas as pd # external import

# local import
from .csv_kit import CsvKit
from . import utils



class Archiver:
    
    def __init__(self, archive_path = None):
        self.csvkit = CsvKit()

        if archive_path is None:
            self.archive_path = Path('archive')
        else:
            self.archive_path = Path(archive_path)



    def create_archive_overrides(self, filename, main_path = Path('overrides')):
        '''
        For manual override archiving
        Copies CSVs from main_path (with override as default) as read-only in archive folder
        '''
        main_path = Path(main_path)
        df = self._get_overrides_df(filename, main_path)
        
        if df is None: 
            return None

        self.create_archive_csv_if_needed(filename, df) # version to archive folder

        csv_path = self.csvkit.if_exists_path(filename, main_path)


        return csv_path



    def _get_overrides_df(self, filename, main_path):
        csv_path = self.csvkit.if_exists_path(filename, main_path)
        try:
            df = pd.read_csv(csv_path) if csv_path else None
            return df
        except Exception:
            return None


    def create_csvs_main_and_archive(
            self, 
            df, 
            main_filename, 
            main_path, 
            archive_filename = None, 
            filename_get_version = None):
        '''
        Create CSVs editable version to main_path and read-only to archive folder
        '''
        if archive_filename is None:
            archive_filename = main_filename
        self.get_main_file_path(df, main_filename, main_path) # also create 
        if filename_get_version is not None:
            filename_get_version = self.get_max_version(filename_get_version)
        self.create_archive_csv_if_needed(archive_filename, df, filename_get_version)
        self.last_archived_file = self.csvkit.read_only_path
        print(f"(Archive version saved as read-only to: {self.last_archived_file} )\n")

        return self.path



    def create_archive_csv_if_needed(self, filename, df, version = None):
        ''' 
        Create read-only csv with version suffixed filename based on filenames in directory
        '''
        archive_file_path = self.get_archive_path(filename, df, version)
        self.create_archive_csv_if_changed(filename, df, archive_file_path)

        
        

    
    def create_archive_csv_if_changed(self, filename, df, path):
        if not path.exists():
            self.csvkit.create_read_only(df, path)
        else:
            print(f"\nNo changes detected for '{filename}'. Reusing existing archive copy.")



    def get_archive_path(self, fname, df, version = None):
        ''' Create filename with version suffix based on filenames in directory '''
        fname = Path(fname).stem # strip any file extensions if needed
        if version is None:
            version = self.get_output_version(fname, df)

        filepath = self.archive_path / f'{fname}_v{version:03d}.csv'

        return filepath

    
    def if_identical_get_last_archive_df(self, fname, current_df):
        ''' Create filename with version suffix based on filenames in directory '''
        last_version_translations_review_df = self.get_last_archive_df(fname)
        if last_version_translations_review_df is None:
            return None
        
        if utils.is_df_identical(current_df, last_version_translations_review_df):
            return last_version_translations_review_df

        return None



    def get_last_archive_df(self, fname):
        ''' Create filename with version suffix based on filenames in directory '''
        if self.get_max_version(fname) == 0:
            return None

        last_version_translations_review_df = self._try_last_version_trans_review_path(fname)

        return last_version_translations_review_df


    def _try_last_version_trans_review_path(self, fname):
        try:
            last_version_trans_review_path = self.get_last_archive_path(fname)
            last_version_translations_review_df = pd.read_csv(last_version_trans_review_path)
            return last_version_translations_review_df
        except Exception:
            return None



    def get_last_archive_path(self, fname):
        ''' Create filename with version suffix based on filenames in directory '''
        fname = Path(fname).stem # strip any file extensions if needed
        version = self.get_max_version(fname)
        filepath = self.archive_path / f'{fname}_v{version:03d}.csv'

        return filepath



    def get_version_df(self, version, fname):
        filepath = self.archive_path / f'{fname}_v{version:03d}.csv'
        if filepath.exists():
            return pd.read_csv(filepath)



    def get_main_file_path(self, df, output_filename, main_path):
        main_path = Path(main_path)
        self.csvkit.create_main(df, output_filename, main_path)
        self.path = self.csvkit.main_path



    def get_output_version(self, fname, df):
        ''' Gets version suffix based on filenames in directory '''
        max_version = self.get_max_version(fname)

        max_version_if_duplicate = self._if_identical_and_get_version(df, fname, max_version)
        if max_version_if_duplicate is not None:
            return max_version_if_duplicate

        return max_version + 1



    def get_max_version(self, fname):
        existing = self.archive_path.glob(f'{fname}_v*.csv')
        past_versions_found = [0]
        for file in existing: 
            self._get_all_versions(file, past_versions_found)

        max_version = max(past_versions_found)

        return max_version



    def _get_all_versions(self, file, versions):
        ''' Gets each file version suffix existing in the directory '''
        suffix = file.stem.rsplit('_v', 1)[-1]
        if suffix.isdigit():
            versions.append(int(suffix))


    
    def _if_identical_and_get_version(self, current_df, fname, max_version):
        if max_version == 0 or max_version is None:
            print("_if_identical_and_get_version ARCHIVER max version")
            print(max_version)
            return None
        
        is_data_identical = self._try_is_identical(current_df, fname, max_version)
        if is_data_identical:
            print("_if_identical_and_get_version ARCHIVER max version IS INDENTICAL")
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

