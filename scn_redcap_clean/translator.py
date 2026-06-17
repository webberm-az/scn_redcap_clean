import re

# external imports
import argostranslate.translate

# local imports
from . import config # global configs


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
