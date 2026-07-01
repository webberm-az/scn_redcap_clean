from pathlib import Path

# local import
from .csv_kit import CsvKit
from . version import Version
from . import utils
from . import console


class CsvWriter:
    
    def __init__(self, paths):

        self.paths = paths
        self.csvkit = CsvKit()
        self.version = Version(self.paths.archive)

    
    # cleaner
    def archive_overrides(self, filename, main_path = None):
        '''
        For manual override archiving
        Copies CSVs from main_path (with override as default) as read-only in archive folder
        '''
        if main_path is None:
            main_path = self.paths.overrides
        
        main_path = Path(main_path)
        df = self.csvkit.try_path_to_df(filename, main_path)
        if df is None: 
            return None

        self.archive_if_changed(filename, df) # version to archive folder
        
        return



    # cleaner
    def main_and_archive(
            self, df, main_csvname, main_path, 
            archive_csvname = None, csvname_get_version = None):
        '''
        Create CSVs editable version to main_path and read-only to archive folder
        '''
        if archive_csvname is None:
            archive_csvname = main_csvname

        self.csvkit.create_main(df, main_csvname, Path(main_path))
        self.path = self.csvkit.main_path

        if csvname_get_version is not None:
            csvname_get_version = self.version.get_max_version(csvname_get_version)
        
        self.archive_if_changed(archive_csvname, df, csvname_get_version)

        return self.path



    def review_and_archive(self, df, step, csvname_get_version = None):
        '''
        Create CSVs editable version to main_path and read-only to archive folder
        '''
        main_csv_name = f'{step}_manual_override'
        archive_csv_name = f'{step}_for_review'

        self.main_and_archive(
            df, main_csv_name, self.paths.review, archive_csv_name, csvname_get_version)
        
        content = 'Additional explanations: \n'
        utils.write_txt_file(content, main_csv_name, self.paths.overrides)



    def archive_if_changed(self, filename, df, version = None):
        ''' 
        Create read-only csv with version suffixed filename based on filenames in directory
        '''
        archive_file_path = self._get_archive_path(filename, df, version)
        self._archive_if_new(filename, df, archive_file_path)
        self.last_archived_file = self.csvkit.read_only_path
        console.archive_file_saved_to(self.last_archived_file)

        
        
    def _archive_if_new(self, csvname, df, path):
        if not path.exists():
            self.csvkit.create_read_only(df, path)
            return
        
        print(f"\nNo changes detected for '{csvname}'. Reusing existing archive copy.")

    def _get_archive_path(self, fname, df, version = None):
        ''' Create filename with version suffix based on filenames in directory '''
        fname = Path(fname).stem # strip any file extensions if needed
        if version is None:
            version = self.version.get_output_version(fname, df)

        filepath = self.paths.archive / f'{fname}_v{version:03d}.csv'

        return filepath
