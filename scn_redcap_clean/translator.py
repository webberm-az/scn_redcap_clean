import os
import re

# external imports
import argostranslate.translate
import langdetect
import pandas as pd

# local imports
from .script import Script
from . import config # global configs


langdetect.DetectorFactory.seed = 0
os.environ['ARGOS_DEVICE_TYPE'] = 'cpu'


class Translator:
    ''' Translates non-English text to English using argostranslate and langdetect packages '''

    _ASTERISK_CLEANER = re.compile(r'''
            \s* # match zero or more spaces on the left side
            \* # match asterisk character (*)
            \s* # match zero or more spaces on the right side
        ''', re.VERBOSE)


    def __init__(self, packages):
        # e.g. special_terms = {'布洛芬':'Ibuprofen',}  inputs for special terms

        self.special_terms = self._format_special_terms(config.translation_dict)
        
        # finds 3 (default) characters in a non-latin script before classifying 
        self.script = Script()
        self.packages = packages



    def to_english(self, text, lang):
        ''' Returns translated, cleaned text '''
        self.special_terms = self._format_special_terms(config.translation_dict)
        if not text:
            return text

        text = self._replace_special_terms(text)

        if not self.packages.ensure_lang_installed(lang):
            return text

        translated_and_cleaned = self._translate_and_clean(text, lang)
        
        return translated_and_cleaned



    def _replace_special_terms(self, text):
        ''' Swaps 1st terms with  2nd term anywhere inside the string '''
        if not self.special_terms:
            return text
            
        for orig_term, translated_term in self.special_terms.items():
            text = self._get_translated(orig_term, translated_term, text)
        
        return text



    def _get_translated(self, orig_term, translated_term, text):
        if str(orig_term).lower() in str(text).lower():
            text = text.replace(orig_term, translated_term)
        
        return text



    def detect_language(self, row, text_columns):
        ''' Detect language by all input columns for each row '''
        self.special_terms = self._format_special_terms(config.translation_dict)
        combined_text = self._combine_text(row, text_columns)
        
        if not combined_text or combined_text.isdigit(): 
            return 'en'

        non_latin_script = self.script.detect_lang_character(combined_text)
        if non_latin_script: 
            return non_latin_script

        lang = self._get_detected_lang(combined_text)
        
        return lang



    def _translate_and_clean(self, text, lang):
        translated = argostranslate.translate.translate(text, lang, 'en')
        translated_and_cleaned = self._ASTERISK_CLEANER.sub('*', translated)

        return translated_and_cleaned



    def _format_special_terms(self, special_terms):
        if not special_terms:
            return {}
        formatted_terms = self._lower_key_term(special_terms)

        return formatted_terms



    def _lower_key_term(self, special_terms):
        special_terms = {
            str(key_term).lower(): translation 
            for key_term, translation in special_terms.items()}

        return special_terms



    def _combine_text(self, row, text_columns):
        # clean and filter valid text elements from row
        text_segments = self._clean_cols(row, text_columns)
        combined_text = ' '.join(text_segments)

        return combined_text



    def _clean_cols(self, row, text_columns):
        ''' Isolates, cleans, and filters valid text elements from row and text_columns '''
        text_segments = []
        
        for col in text_columns:
            cell_val = row[col]
            cleaned_str = self._clean_cells(cell_val) 
            text_segments = self._if_clean_append(cleaned_str, text_segments)

        return text_segments


    
    def _clean_cells(self, cell_val):
        ''' Cleans each cell value (strips whitespace and converts to string) '''
        cleaned_str = ''
        if pd.notna(cell_val):
            cleaned_str = str(cell_val).strip()      
              
        return cleaned_str
    


    def _if_clean_append(self, cleaned_str, text_segments):
        ''' Appends cleaned string to text_segments if not empty '''
        if cleaned_str != '':
            text_segments.append(cleaned_str)

        return text_segments



    def _get_detected_lang(self, combined_text):
        ''' Returns language code for translation '''
        try:
            predictions = langdetect.detect_langs(combined_text)

            # map Chinese codes zh-cn or zh-tw to zh for argostranslate.translate.translate()
            lang = self._get_lang_prediction_defaults(predictions)
            return lang
        except Exception: 
            return 'en'
        


    def _get_lang_prediction_defaults(self, predictions):
        top_prediction = predictions[0]
        is_probably_english = self._is_probably_english(top_prediction)
        if is_probably_english: 
            return 'en'

        lang = self.packages.normalize_from_code(top_prediction.lang) # not needed for english
        
        return lang


    
    def _is_probably_english(self, top_prediction):
        is_prob_english = (top_prediction.lang == 'en' and top_prediction.prob > 0.8)

        return is_prob_english