from .csv_writer import CsvWriter
from .csv_kit import CsvKit
from . import utils


class Overrides:
    
    def __init__(self, paths):
        self.paths = paths
        self.csv_writer = CsvWriter(self.paths)
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
        self.csv_writer.main_and_archive(df, cur_step, self.paths.steps)


    def _run_current_step(self, df):
        self.csv_writer.archive_overrides(self.override_csv_name)
        df = self.step.run_override(df, self.paths)

        return df



    def _init_step_dependencies(self):
        self.override_csv_name = f'{self.step.process_name}_manual_override'
        self.override_csv_path = self.csvkit.if_exists_path(
            self.override_csv_name, self.paths.overrides)



    def _get_last_step_df(self):
        last_step = utils.get_step_config(self.step.number - 1)
        df = self.csvkit.try_path_to_df(last_step, self.paths.steps)

        return df


