import pandas as pd # external imports
from typing import cast

# local imports
from . import config, utils # global configs
from .cleaning_step import CleaningStep
from .csv_writer import CsvWriter
from .translator import Translator
from .detector import Detector
from .translation_packages import TranslationPackages
from .csv_kit import CsvKit
from .override_append import OverrideAppend
from .version import Version


class Translation(CleaningStep):

    def __init__(self, df):
        self.data = df
        self.csv_writer = CsvWriter()
        self.id_col = config.merge_on_id_column
        self.detect_script_threshold = config.translation_script_threshold
        self.special_terms = config.translation_dict
        self.packages = TranslationPackages(to_code = 'en')
        self.translator = Translator(self.packages)
        self.csvkit = CsvKit()
        self.detect = Detector(self.packages)
        self.archive_csvname = utils.get_review_cvsname(self.get_process_name())
        self.version = Version()

    @classmethod
    def get_process_name(cls):
        process_name = 'translation'

        return process_name

    def review_df(self, cols_to_translate):
        '''
        Outputs csv files for translation review 
        (1 file for record keeping and 1 file for manual override editting)
        '''
        self.cols_to_translate = cols_to_translate
        if self.cols_to_translate is None:
            return 

        df = self.data

        # df with added english '_orig' cols, '_needs_trans' col, and translated 'cols_to_translate'
        translation_df = self._get_translation_df(df)
        if self._is_no_translations_needed(translation_df):
            self.skipped = True
            return 

        self.packages.print_language_download_summary() 
        final_data = self._get_translations_for_review_df()

        return final_data

    def create_final_data(self): # called in step
        ''' 
        If override_filename exists in overrides folder inputs into main csv
        '''
        df = self.data
        df = OverrideAppend(self.get_process_name()).append_override_df(df)
        
        return df

    def _get_translation_df(self, df):
        '''
        Returns df with added _orig columns, _needs_trans column, and translations 
        '''
        self.cols_to_translate = utils.get_valid_headers(df, self.cols_to_translate)
        needs_trans_idx = self._get_needs_translation_df() 
        self._filter_valid_text_cols(needs_trans_idx)

        # create df w/ duplicated cols_to_translate w/ '_orig' suffix added to col names
        self.data = utils.make_duplicate_orig_cols(df, self.cols_to_translate)
        self._input_eng_translation(needs_trans_idx)

        return self.data

    def _is_no_translations_needed(self, df):
        if '_needs_trans' not in df.columns or not df['_needs_trans'].any():
            print('No foreign languages detected.')
            return True
        
        return False

    def _get_translations_for_review_df(self):
        data = cast(
            pd.DataFrame, self._get_translated_rows_only_df())
        data = utils.add_override_explanation_column(data, self.id_col)

        return data



    def _get_needs_translation_df(self):
        '''
        Creates df of rows needing translation and includes detected langange in '_lang' col
        '''
        last_review_df = self._get_last_archive_df(self.archive_csvname)
        if last_review_df is None:
            detected_needs_trans_idx = self._get_detected_needs_trans_idx()
            return detected_needs_trans_idx
        
        max_version = self.version.get_max_version(self.archive_csvname)
        if max_version is None:
            detected_needs_trans_idx = self._get_detected_needs_trans_idx()
            return detected_needs_trans_idx
        archive_version = self.version.get_max_version(config.step_name_assembled)
        if float(max_version) >= float(archive_version):
            archived_needs_trans_idx = self._get_archived_needs_trans_idx(last_review_df, max_version)
            return archived_needs_trans_idx

        detected_needs_trans_idx = self._get_detected_needs_trans_idx()
        return detected_needs_trans_idx



    def _input_eng_translation(self, needs_trans_idx):
        ''' Inputs english translations for all df cols_to_translate containing text  '''
        print('Translating each text column (if non-english detected)...\n')
        for col in self.cols_to_translate:
            needs_trans = needs_trans_idx & self.data[col].notna() & (self.data[col].astype(str).str.strip() != '')

            for idx in self.data[needs_trans].index:
                self._try_translate_df(idx, col)
                    
                    

    def _try_translate_df(self, idx, col):
        val = str(self.data.at[idx, col]).strip()
        row_lang = self.data.at[idx, '_lang']

        try:
            translated = self.translator.to_english(val, row_lang)
            self.data.at[idx, col] = f'[trans. from {row_lang}] {translated}'

        except Exception as e:
            print(f'\nTranslation failed | Language: {row_lang} | Error: {e}')



    def _get_translated_rows_only_df(self):
        '''
        Returns reduced df of translated rows and columns for easier review
        '''
        # only rows where '_needs_trans' is True
        t_df = self.data[self.data['_needs_trans']].copy() 
        
        keep = [self.id_col, '_lang']
        for col in self.cols_to_translate:
            keep.extend(c for c in (col, f'{col}_orig') if c in t_df.columns)
            
        return t_df[keep]



    def _get_detected_needs_trans_idx(self):
        print('Detecting language (based on whole row language context)...')
        self.data['_lang'] = self.data.apply(lambda row: self.detect.detect_language(
            row, self.cols_to_translate), axis = 1)
        self.data['_needs_trans'] = self.data['_lang'] != 'en' # flag rows needing translation

        return self.data['_needs_trans']



    def _get_archived_needs_trans_idx(
        self, last_version_translations_review_df, max_version):
        print(f"Using language detections from '{self.archive_csvname}' version {max_version}")
        self._input_languages_codes(last_version_translations_review_df)

        return self.data['_needs_trans']



    def _input_languages_codes(self, archived_df):
        ''' Maps past language detection to current df by id_col and _lang'''
        archived_df[self.id_col] = utils.match_rows_to_ref_id(self.data, archived_df, self.id_col)
        map_id_to_lang = archived_df.set_index(self.id_col)['_lang'].to_dict()
        self._create_translation_columns(map_id_to_lang)
        


    def _create_translation_columns(self, map_id_to_lang):
        ''' Omitted id's from archived_df default to english for _lang column '''
        self.data['_lang'] = self.data[self.id_col].map(map_id_to_lang).fillna('en')
        self.data['_needs_trans'] = self.data['_lang'] != 'en'



    def _get_last_archive_df(self, fname):
        ''' Create filename with version suffix based on filenames in directory '''
        if self.version.get_max_version(fname) == 0:
            return None

        last_version_translations_review_df = self.version.try_last_version_path(fname)

        return last_version_translations_review_df


    def _filter_valid_text_cols(self, needs_trans_idx):
        ''' Filters cols_to_translate to remove empty or all numeric columns '''
        translation_data = self.data.loc[needs_trans_idx]
        self.cols_to_translate = utils.filter_alpha_columns(
            translation_data, self.cols_to_translate)