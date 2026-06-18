import re

from . import utils
from . import config # global configs


class Script:
    ''' Detects non-latin scripts using character ranges '''

    KOREAN = re.compile(r'[\uac00-\ud7af]')
    JAPANESE = re.compile(r'[\u3040-\u30ff]')
    CHINESE = re.compile(r'[\u4e00-\u9fff]')
    CYRILLIC = re.compile(r'[\u0400-\u04ff\u0500-\u052f]')
    ARABIC = re.compile(r'[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff]')
    DEVANAGARI = re.compile(r'[\u0900-\u097f]')
    GREEK = re.compile(r'[\u0370-\u03ff\u1f00-\u1fff]')

    # lang code mapping
    LANG_CHARS = [
        (KOREAN, 'ko'),
        (JAPANESE, 'ja'),
        (CHINESE, 'zh'),
        (CYRILLIC, 'ru'),
        (ARABIC, 'ar'),
        (DEVANAGARI, 'hi'),
        (GREEK, 'el'),
    ]

    def __init__(self):
        self.min_chars_detect = config.translation_script_threshold



    def detect_lang_character(self, text):
        ''' Detects language by non-latin characters in text '''
        if not text:
            return None

        for lang, code in self.LANG_CHARS:
            if utils.is_n_matches(lang, text, self.min_chars_detect):
                return code

        return None