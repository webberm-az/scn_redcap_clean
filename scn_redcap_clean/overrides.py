from .csv_writer import CsvWriter
from .csv_kit import CsvKit
from . import paths, utils


class Overrides:
    
    def __init__(self):
        self.csv_writer = CsvWriter()
        self.csvkit = CsvKit()



    # in Cleaner for Translations, Duplicates, Medication & Genomics
    def run(self, step):
        self.df = self.get_df(step)
        self.create_csvs(self.df)
                
        return self.df


    def get_df(self, step):
        self.step = step
        self._init_step_dependencies()
        df = self._get_last_step_df()
        df = self._run_current_step(df)

        return df



    def create_csvs(self, df):
        cur_step = utils.get_step_config(self.step.number)
        self.csv_writer.main_and_archive(df, cur_step, paths.STEPS)


    def _run_current_step(self, df):
        self.csv_writer.archive_overrides(self.override_csv_name)
        df = self.step.run_override(df)

        return df



    def _init_step_dependencies(self):
        self.override_csv_name = f'{self.step.process_name}_manual_override'
        self.override_csv_path = self.csvkit.path(
            self.override_csv_name, paths.OVERRIDES)



    def _get_last_step_df(self):
        last_step = utils.get_step_config(self.step.number - 1)
        df = self.csvkit.path_to_df(last_step, paths.STEPS)

        return df


