
from . import paths, utils
from .csv_kit import CsvKit
from .csv_writer import CsvWriter


class StepManager():
    ''' Handles all file system state for the cleaning steps. '''
    
    def __init__(self):
        self.csvkit = CsvKit()
        self.csv_writer = CsvWriter()


    def output_step_number(self, step_process_name):
        last_step_number, _ = self._get_last_step(step_process_name)

        return last_step_number + 1
    


    def get_last_step_df(self, step_process_name):
        df, _ = self.get_last_step(step_process_name)

        return df



    def get_last_step(self, step_config_name):
        ''' Returns previous steps df and number based on csv files in steps folder '''
        last_step_number, last_step_name = self._get_last_step(step_config_name)

        if last_step_name is None:
            return None, 0

        df = self.csvkit.robust_read(last_step_name)

        return df, last_step_number



    def get_max_step(self):
        current_step_csvs = (paths.STEPS).glob('*.csv')
        last_step_number, last_step_name = utils.get_max_file_index(
            current_step_csvs, self._extract_step_number)

        return last_step_number, last_step_name



    def _get_last_step(self, step_process_name):
        current_step_csv = list((paths.STEPS).glob(f'*_{step_process_name}.csv'))
        if current_step_csv:
            last_step_number, last_step_name = self._get_previous_step(current_step_csv)
        else:
            last_step_number, last_step_name = self.get_max_step()

        return last_step_number, last_step_name



    def _get_previous_step(self, existing_file):
        current_step_number = self._extract_step_number(existing_file[0])
        last_step_number = current_step_number - 1
        
        if last_step_number <= 0:
            return 0, None
            
        previous_step_csv = list((paths.STEPS).glob(f'{last_step_number}_*.csv'))
        if previous_step_csv:
            return last_step_number, previous_step_csv[0]
        else:
            return 0, None


    
    def _extract_step_number(self, file_path):
        parts = file_path.name.split('_', 1)
        if parts[0].isdigit():
            return int(parts[0])
        
        return 0
