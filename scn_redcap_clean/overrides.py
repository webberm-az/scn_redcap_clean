from .csv_writer import CsvWriter
from .csv_kit import CsvKit
from . import utils


class Overrides:
    
    def __init__(self, step_number, Class, paths):
        self.paths = paths
        self.archiver = CsvWriter(self.paths)
        self.step_number = step_number
        self.Class_instance = Class
        
        self.process_name = self.Class_instance.__name__.lower()
        self.override_csv_name = f'{self.process_name}_manual_override'

        self.csvkit = CsvKit()
        self.df = self.get_last_step_df()
        self.override_csv_path = self.csvkit.if_exists_path(
            self.override_csv_name, self.paths.overrides)
        
        self.archiver.archive_overrides(self.override_csv_name)


    def get_last_step_df(self):
        last_step = utils.get_step_config(self.step_number - 1)
        df = self.csvkit.try_path_to_df(last_step, self.paths.steps)

        return df



    # in Cleaner for Translations, Duplicates, Medication & Genomics
    def run(self):
        df = self.try_input_override_df()
        self.create_step_main_and_archive(df)
        
        return df



    def try_input_override_df(self):
        df = self.df
        method = self._get_class_instance_method('try_input_override_df')
        df = method()
        
        return df



    def create_step_main_and_archive(self, df):
        cur_step = utils.get_step_config(self.step_number)
        self.archiver.main_and_archive(df, cur_step, self.paths.steps)



    def _get_class_instance_method(self, method):
        Class_instance = self.Class_instance
        instance = Class_instance(self.df, self.paths)
        method = getattr(instance, method)

        return method
