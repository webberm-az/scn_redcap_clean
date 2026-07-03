from enum import Enum

from .clinical import Clinical
from .duplicates import Duplicates
from .translation import Translation

class Step(Enum):
    translated = (2, Translation)
    duplicates = (3, Duplicates)
    clinical = (4, Clinical)

    def __init__(self, number, class_name):
        self.number = number
        self.class_name = class_name
        self.process_name = class_name.__name__.lower()
        self.did_run = False
        self.skipped = False
        self.skip_reason = None


    def run_override(self, df):
        ''' Instantiates the specific class and runs the method. '''
        instance = self.class_name(df)
        df = instance.try_input_override_df()
        self._track_skipped(df)

        return df


    def _track_skipped(self, df):
        self.did_run = df is not None
        self.skipped = df is None

        if self.skipped:
            self.skip_reason = "override returned None"

        return df



    def should_run(self, context):
        if self is Step.translated:
            return context.has_language_columns and not context.is_english_only

        return True

''' for Cleaner
for step in Step:
    if not step.should_run(context):
        step.skipped = True
        continue

    df = step.run_override(df, paths)
'''