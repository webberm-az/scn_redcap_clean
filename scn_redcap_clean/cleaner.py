import os
import certifi

os.environ['SSL_CERT_FILE'] = certifi.where()

# local imports
from .archiver import Archiver
from .csv_kit import CsvKit
from .duplicates import Duplicates
from .merging import Merging
from .overrides import Overrides
from .paths import Paths
from .translation import Translation
from .base_csv import BaseCSV
from .summary import Summary
from . import config # global configs
from . import utils
from . import console


class Cleaner:

    def __init__(self):
        self.paths = Paths(raw_data_source = config.raw_data_dir)
        self.archiver = Archiver(archive_path = self.paths.archive)
        self.translation = Translation(paths = self.paths, archiver = self.archiver,)
        self.merging = Merging(self.paths)
        self.csvkit = CsvKit()
        self.summary = Summary(paths = self.paths)
        self.base = BaseCSV(self.paths)


    def step_01_merge_raw_and_review_translations(
        self, csv_list, text_columns = utils.auto, drop_na_col = True):
        ''' Returns csv_files as merge_df and outputs translation CSV for review '''
        if not csv_list:
            console.error('No data files in raw data folder to merge')
            return None
        self.base.output_base_csv_to_raw()
        
        merged_df = self.merging.get_merged_module_df(
            csv_list = csv_list, 
            text_columns = text_columns,
            merge_on_file = 'base',
            drop_na_col = drop_na_col)
        
        language_cols = self.merging.active_text_columns

        merged_main_path = self.archiver.create_csvs_main_and_archive(
            merged_df, 
            config.name_01_main, 
            self.paths.stages)

        self.translation.create_translations_for_review(merged_main_path, language_cols)
        
        return
    


    def step_02_translated_and_review_duplicates(
            self,
            override_filename = 'translations_manual_override'):
        '''
        If translations_manual_override is in the overrides folder:
        Overwrites non-english with english translations and output duplicates for review
        Copies override CSV as read-only in archive folder for version history
        '''
        self.archiver.create_archive_overrides(override_filename, self.paths.overrides)

        df = self._try_input_translations_df(override_filename)
        self.archiver.create_csvs_main_and_archive(df, config.name_02_main, self.paths.stages) 
        
        duplicates = Duplicates(df, self.paths, self.archiver)
        duplicates.get_duplicates_for_review()

        return
    
    

    def step_03_removed_duplicates(
            self,
            csv_name = config.name_02_main, 
            override_filename = 'duplicates_manual_override'):
        '''
        Outputs csv files for duplicates review 
        1 file for record keeping (logs) and 1 file for manual override editting (overrides)
        Duplicates are identified by birthdate. 
        '''
        self.archiver.create_archive_overrides(override_filename, self.paths.overrides)
        
        df = self.csvkit.try_convert_path_to_df(csv_name, self.paths.stages)
        duplicates = Duplicates(df, self.paths, self.archiver)
        df = duplicates.clean_duplicates(override_filename)
        self.archiver.create_csvs_main_and_archive(df, config.name_03_main, self.paths.stages)
        
        return



    def _try_input_translations_df(self, override_filename):
        ''' if override_filename exists in overrides folder inputs translations from override_filename '''
        override_csv_path = self.csvkit.if_exists_path(override_filename, self.paths.overrides)
        df = self.csvkit.try_convert_path_to_df(config.name_01_main, self.paths.stages)
        if override_csv_path is not None:
            overrides = Overrides(override_csv_path, df)
            df = overrides.override()
        else:
            console.missing_override(override_filename, 'translation input', 'without translations')
        
        return df

