from pathlib import Path

import pandas as pd # external import

# local import
from .csv_kit import CsvKit
from . version import Version
from . import utils
from . import console


class Archiver:
    
    def __init__(self, archive_path = None):
        self.csvkit = CsvKit()

        if archive_path is None:
            self.archive_path = Path('archive')
        else:
            self.archive_path = Path(archive_path)
        
        self.version = Version(self.archive_path)

    
    # cleaner
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
        
        return



    # cleaner
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

        self.csvkit.create_main(df, main_filename, Path(main_path))
        self.path = self.csvkit.main_path

        if filename_get_version is not None:
            filename_get_version = self.version.get_max_version(filename_get_version)
        
        self.create_archive_csv_if_needed(archive_filename, df, filename_get_version)

        return self.path



    # translation
    def get_last_archive_df(self, fname):
        ''' Create filename with version suffix based on filenames in directory '''
        if self.version.get_max_version(fname) == 0:
            return None

        last_version_translations_review_df = self.version.try_last_version_path(fname)

        return last_version_translations_review_df



    def create_archive_csv_if_needed(self, filename, df, version = None):
        ''' 
        Create read-only csv with version suffixed filename based on filenames in directory
        '''
        archive_file_path = self.get_archive_path(filename, df, version)
        self.create_archive_csv_if_changed(filename, df, archive_file_path)
        self.last_archived_file = self.csvkit.read_only_path
        console.archive_file_saved_to(self.last_archived_file)

        

    def get_archive_path(self, fname, df, version = None):
        ''' Create filename with version suffix based on filenames in directory '''
        fname = Path(fname).stem # strip any file extensions if needed
        if version is None:
            version = self.version.get_output_version(fname, df)

        filepath = self.archive_path / f'{fname}_v{version:03d}.csv'

        return filepath


        
    def create_archive_csv_if_changed(self, filename, df, path):
        if not path.exists():
            self.csvkit.create_read_only(df, path)
        else:
            print(f"\nNo changes detected for '{filename}'.  Reusing existing archive copy.")



    def _get_overrides_df(self, filename, main_path):
        csv_path = self.csvkit.if_exists_path(filename, main_path)
        try:
            df = pd.read_csv(csv_path) if csv_path else None
            return df
        except Exception:
            return None
