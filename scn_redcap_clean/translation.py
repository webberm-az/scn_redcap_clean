import pandas as pd # external imports

# local imports
from .translator import Translator
from .detector import Detector
from .translation_packages import TranslationPackages
from . import config # global configs
from .csv_kit import CsvKit
from . version import Version
from . import utils


class Translation:

    def __init__(self, paths, archiver, archive_filename = 'translations_for_review'):
        self.paths = paths
        self.archiver = archiver
        self.id_col = config.merge_on_id_column
        self.detect_script_threshold = config.translation_script_threshold
        self.special_terms = config.translation_dict
        self.packages = TranslationPackages(to_code = 'en')
        self.translator = Translator(self.packages)
        self.csvkit = CsvKit()
        self.detect = Detector(self.packages)
        self.archive_filename = archive_filename
        self.df = None
        self.version = Version(self.paths.archive)



    def create_translations_for_review(
            self, 
            file_path, 
            cols_to_translate,
            main_filename = 'translations_manual_override'):
        '''
        Outputs csv files for translation review 
        (1 file for record keeping and 1 file for manual override editting)
        '''
        # df with added english '_orig' cols, _needs_trans col, and translated cols_to_translate
        self.df = self._get_translation_df(file_path, cols_to_translate)
        if self._is_no_translations_needed():
            return pd.DataFrame() # if no translations detected returns empty df

        self.packages.print_language_download_summary() 
        final_translated_df = self._get_translations_for_review_df(cols_to_translate)
        
        # outputs csvs to review folder and a version to archive
        self.archiver.create_csvs_main_and_archive(
            final_translated_df, 
            main_filename, 
            self.paths.review, 
            self.archive_filename,
            filename_get_version = config.name_01_main)

        content = 'Additional explanations: \n'
        utils.write_txt_file(content, main_filename, self.paths.overrides)

        return final_translated_df



    def _get_translation_df(self, file_path, cols_to_translate):
        '''
        Returns df with added _orig columns, _needs_trans column, and translations 
        '''
        # create df w/ duplicated cols_to_translate w/ '_orig' suffix added to col names
        self.df = self.csvkit.make_duplicate_orig_cols(file_path, cols_to_translate)
        needs_trans_idx = self._get_needs_translation_df(cols_to_translate) 
        self._input_eng_translation(cols_to_translate, needs_trans_idx)

        return self.df



    def _is_no_translations_needed(self):
        if '_needs_trans' not in self.df.columns or not self.df['_needs_trans'].any():
            print('No foreign languages detected.')
            return True
        
        return False



    def _get_translations_for_review_df(self, cols_to_translate):
        translated_df = self._get_translated_rows_only_df(cols_to_translate)
        utils.add_column_if_dne('override_explanation', translated_df)

        return translated_df



    def _get_needs_translation_df(self, cols_to_translate):
        '''
        Creates df of rows needing translation and includes detected langange in '_lang' col
        '''
        last_review_df = self.archiver.get_last_archive_df(self.archive_filename)
        if last_review_df is None:
            detected_needs_trans_idx = self._get_detected_needs_trans_idx(cols_to_translate)
            return detected_needs_trans_idx
        
        max_version = self.version.get_max_version(self.archive_filename)
        if max_version is None:
            detected_needs_trans_idx = self._get_detected_needs_trans_idx(cols_to_translate)
            return detected_needs_trans_idx
        archive_version = self.version.get_max_version(config.name_01_main)
        if float(max_version) >= float(archive_version):
            archived_needs_trans_idx = self._get_archived_needs_trans_idx(last_review_df, max_version)
            return archived_needs_trans_idx

        detected_needs_trans_idx = self._get_detected_needs_trans_idx(cols_to_translate)
        return detected_needs_trans_idx



    def _input_eng_translation(self, cols_to_translate, needs_trans_idx):
        ''' Inputs english translations for all df cols_to_translate containing text  '''
        print('Translating each text column (if non-english detected)...\n')
        for col in cols_to_translate:
            needs_trans = needs_trans_idx & self.df[col].notna() & (self.df[col].astype(str).str.strip() != '')

            for idx in self.df[needs_trans].index:
                self._try_translate_df(idx, col)
                    
                    

    def _try_translate_df(self, idx, col):
        val = str(self.df.at[idx, col]).strip()
        row_lang = self.df.at[idx, '_lang']

        try:
            translated = self.translator.to_english(val, row_lang)
            self.df.at[idx, col] = f'[trans. from {row_lang}] {translated}'

        except Exception as e:
            print(f'\nTranslation failed | Language: {row_lang} | Error: {e}')



    def _get_translated_rows_only_df(self, cols_to_translate):
        '''
        Returns reduced df of translated rows and columns for easier review
        '''
        # only rows where '_needs_trans' is True
        t_df = self.df[self.df['_needs_trans']].copy() 
        
        keep = [self.id_col, '_lang']
        for col in cols_to_translate:
            keep.extend(c for c in (col, f'{col}_orig') if c in t_df.columns)
            
        return t_df[keep]



    def _get_detected_needs_trans_idx(self, cols_to_translate):
        print('Detecting language (based on whole row language context)...')
        self.df['_lang'] = self.df.apply(lambda row: self.detect.detect_language(row, cols_to_translate), axis=1)
        self.df['_needs_trans'] = self.df['_lang'] != 'en' # flag rows needing translation

        return self.df['_needs_trans']



    def _get_archived_needs_trans_idx(self, last_version_translations_review_df, max_version):
        print(f"Using language detections from '{self.archive_filename}' version {max_version}")
        self._input_languages_codes(last_version_translations_review_df)

        return self.df['_needs_trans']



    def _input_languages_codes(self, archived_df):
        ''' Maps past language detection to current df by id_col and _lang'''
        archived_df[self.id_col] = utils.match_rows_to_ref_id(self.df, archived_df, self.id_col)
        map_id_to_lang = archived_df.set_index(self.id_col)['_lang'].to_dict()
        self._create_translation_columns(map_id_to_lang)
        


    def _create_translation_columns(self, map_id_to_lang):
        ''' Omitted id's from archived_df default to english for _lang column '''
        self.df['_lang'] = self.df[self.id_col].map(map_id_to_lang).fillna('en')
        self.df['_needs_trans'] = self.df['_lang'] != 'en'
