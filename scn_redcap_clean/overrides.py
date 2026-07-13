from . import paths
from .csv_writer import CsvWriter
from .csv_kit import CsvKit
from .step_manager import StepManager


class Overrides:
    
    def __init__(self):
        self.csv_writer = CsvWriter()
        self.csvkit = CsvKit()
        self.step_manager = StepManager()


    # in Cleaner for Translations, Duplicates, Medication & Genomics
    def run(self, step_enum):
        self.data = self.get_step_df(step_enum)
        
        self.create_csvs(self.data)
                
        return self.data


    def get_step_df(self, step_enum):
        self.step = step_enum
        self._init_step_dependencies()
        last_step_data, last_step_number = self.step_manager.get_last_step(
            self.step.config_name)
        self.step_number = last_step_number + 1
        current_data = self._run_current_step(last_step_data)

        return current_data



    def exists(self, step_enum):
        override_csv_name = f'{step_enum.process_name}_manual_override'

        return self.csvkit.exists(override_csv_name, paths.OVERRIDES)


    def get_df(self, step_enum):
        self.step = step_enum
        override_csv_name = f'{self.step.process_name}_manual_override'
        data = self.csvkit.path_to_df(override_csv_name, paths.OVERRIDES)

        return data


    def create_csvs(self, data):
        self.filename = f'{self.step_number}_{self.step.config_name}.csv'
        self.csv_writer.main_and_archive(data, self.filename, paths.STEPS)



    def _run_current_step(self, data):
        ''' Instantiates the specific class and runs the method. '''
        self.csv_writer.archive_overrides(self.override_csv_name)
                
        step_instance = self.step.class_name(data.copy())
        data = step_instance.input_override()

        return data



    def _init_step_dependencies(self):
        self.override_csv_name = f'{self.step.process_name}_manual_override'
        self.override_csv_path = self.csvkit.path(
            self.override_csv_name, paths.OVERRIDES)
