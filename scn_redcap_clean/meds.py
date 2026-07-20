import numpy as np

from . import config, console, paths, schemas, utils
from .cleaning_step import CleaningStep
from .csv_writer import CsvWriter
from .csv_kit import CsvKit
from .extract_ai import ExtractorAI
from .local_ai import LocalAI
from .med_dummies import MedDummies
from .meds_map import MedsMap
from .ref_map import RefMap

class Medications(CleaningStep):
    ''' Standardizes and dummies medications and supplements using local AI Ollama. '''

    def __init__(self, data):
        self.data = data.copy()
        self.csv_writer = CsvWriter()
        self.id_col = config.merge_on_id_column
        self.csvkit = CsvKit()
        self.meds_ref_data = self.csvkit.path_to_df(
            config.meds_dict, paths.REF)

    @classmethod
    def get_process_name(cls):
        process_name = 'medications'

        return process_name

    def review_df(self):
        ''' 
        Outputs csv files for medications review 
        (1 file for record keeping and 1 file for manual override editting)
        Medications and supplements are standardized using local AI Ollama
        '''
        if self.meds_ref_data is None:
            console.alert_missing_config_file(
                'ref', 'Medication and Supplements Map', 'config.meds_dict')
            return None
            
        data = self._get_meds_for_review()

        return data

    def create_final_data(self): # called in Override
        ''' 
        If override_filename exists in overrides folder, maps medications/supplements terms to config.meds_dict and inputs into main csv
        '''
        csvname = utils.get_manual_cvsname(self.get_process_name())
        self.override_csv_path = self.csvkit.path(csvname, paths.OVERRIDES)
        data = self._input_override_data()
        
        return data

    def _get_meds_for_review(self):
        local_ai = LocalAI(schema = schemas.MedicationList, field_name = 'substances')
        extractor_configs = self._get_configs()
        extractor = ExtractorAI(local_ai, extractor_configs)
        data = extractor.get_for_review(self.data)
        add_to_ref_header = 'add_to_ref'
        data = self._get_add_to_ref_col(data, add_to_ref_header)
        if data is None:
            return 
            
        data = utils.put_front_columns_first(data, self.id_col, add_to_ref_header)
        return data

    def _get_configs(self):
        extractor_configs = {
            'name': self.get_process_name(),
            'cols': config.med_text_cols,
            'prompt': config.prompt_meds,
            'schema': schemas.MedicationList}

        return extractor_configs

    def _get_add_to_ref_col(self, meds_data, add_to_ref_header):
        if meds_data is None:
            return None
        ref_map = RefMap(self.meds_ref_data)
        recommended_term = schemas.recommended_term_str()
        is_missing = ref_map.is_missing(meds_data[recommended_term])
        meds_data[add_to_ref_header] = np.where(is_missing, 'MISSING IN REF', '')

        return meds_data

    def _input_override_data(self):
        ''' 
        If override_csv_name exists in overrides folder:
        Maps terms using map_data and inputs into main csv
        '''
        if self.data is None or self.override_csv_path is None or \
            self.meds_ref_data is None:
            self._alert_errors()
            return None

        self.override_data = self.csvkit.robust_read(self.override_csv_path) 
        data = self._get_final_data()
        
        return data

    def _alert_errors(self):
        if self.data is None:
            console.error("No step csvs found in 'steps' folder")
        
        if self.override_csv_path is None:
            console.info_missing_file({self.override_csv_path}, 'overrides')
        
        if self.meds_ref_data is None:
            console.print_missing_override_dict(
                self.get_process_name(), 'config.meds_dict')

    def _get_final_data(self):
        meds_map = MedsMap(self.meds_ref_data, self.override_data)
        mapped_long_data = meds_map.get_long_data()
        if mapped_long_data.empty:
            return self.data
        med_dummies = MedDummies(self.data, mapped_long_data)
        final_data = med_dummies.merged_data()

        return final_data
