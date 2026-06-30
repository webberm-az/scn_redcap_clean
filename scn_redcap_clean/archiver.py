from pathlib import Path

# local import
from .csv_kit import CsvKit
from . version import Version
from . import utils
from . import console


class Archiver:
    
    def __init__(self, paths):

        self.paths = paths
        self.csvkit = CsvKit()
        self.version = Version(self.paths.archive)

    
    # cleaner
    def create_archive_overrides(self, filename, main_path = None):
        '''
        For manual override archiving
        Copies CSVs from main_path (with override as default) as read-only in archive folder
        '''
        if main_path is None:
            main_path = self.paths.overrides
        
        main_path = Path(main_path)
        df = self._get_overrides_df(filename, main_path)
        if df is None: 
            return None

        self.create_archive_csv_if_needed(filename, df) # version to archive folder
        
        return



    # cleaner
    def create_csvs_main_and_archive(
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
        
        self.create_archive_csv_if_needed(archive_csvname, df, csvname_get_version)

        return self.path



    # translation
    def get_last_archive_df(self, fname):
        ''' Create filename with version suffix based on filenames in directory '''
        if self.version.get_max_version(fname) == 0:
            return None

        last_version_translations_review_df = self.version.try_last_version_path(fname)

        return last_version_translations_review_df


    def create_csvs_review_and_archive(self, df, step, csvname_get_version = None):
        '''
        Create CSVs editable version to main_path and read-only to archive folder
        '''
        main_csv_name = f'{step}_manual_override'
        archive_csv_name = f'{step}_for_review'

        self.create_csvs_main_and_archive(
            df, main_csv_name, self.paths.review, archive_csv_name, csvname_get_version)
        
        content = 'Additional explanations: \n'
        utils.write_txt_file(content, main_csv_name, self.paths.overrides)



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

        filepath = self.paths.archive / f'{fname}_v{version:03d}.csv'

        return filepath


        
    def create_archive_csv_if_changed(self, csvname, df, path):
        if not path.exists():
            self.csvkit.create_read_only(df, path)
        else:
            print(f"\nNo changes detected for '{csvname}'. Reusing existing archive copy.")



    def _get_overrides_df(self, filename, main_path):
        csv_path = self.csvkit.if_exists_path(filename, main_path)
        try:
            df = self.csvkit.robust_read_csv(csv_path) if csv_path else None
            return df
        except Exception:
            return None
