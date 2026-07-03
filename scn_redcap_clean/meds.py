import numpy as np
import pandas as pd

from . import config, console, paths, utils
from .csv_writer import CsvWriter
from .csv_kit import CsvKit
from .extract_ai import ExtractorAI
from .local_ai import LocalAI
from .ref_map import RefMap
from .schemas import MedicationList


class Medications:
    ''' Standardizes and dummies medications and supplements using local AI Ollama. '''
    
    def __init__(self, df):

        self.df = df.copy()
        self.archiver = CsvWriter()
        self.id_col = config.merge_on_id_column
        self.csvkit = CsvKit()
        self.meds_dict_df = self.csvkit.path_to_df(
            config.meds_dict, paths.REF)
        self.step_number = 4



    def review_df(self):
        ''' 
        Outputs csv files for medications review 
        (1 file for record keeping and 1 file for manual override editting)
        Medications and supplements are standardized using local AI Ollama
        '''
        if self.meds_dict_df is None:
            console.alert_missing_config_file(
                'ref', 'Medication and Supplements Map', 'config.meds_dict')
            return None
            
        df = self._get_meds_for_review()

        return df



    def try_input_override_df(self): # called in Override
        ''' 
        If override_filename exists in overrides folder, maps medications/supplements terms to config.meds_dict and inputs into main csv
        '''
        self.override_csv_path = self.csvkit.path( 
            'medications_manual_override', paths.OVERRIDES)
        df = self.try_input_mapped_long_df(self.df, self.meds_dict_df)
        
        return df



    def try_input_mapped_long_df(self, df, map_df): # for Medications and Genomics
        ''' 
        If override_csv_name exists in overrides folder:
        Maps terms using map_df and inputs into main csv
        '''
        self.df = df
        self.map_df = map_df
        self.override_csv_path = self.csvkit.path( 
            'medications_manual_override', paths.OVERRIDES)
        if self.df is None or self.override_csv_path is None or self.map_df is None:
            self._alert_errors()
            return None

        override_df = self.csvkit.robust_read(self.override_csv_path) 
        df = self._get_final_df(override_df)
        
        return df



    def _alert_errors(self):
        if self.df is None:
            last_step = utils.get_step_config(self.step_number - 1)
            console.error_missing(last_step, "not in 'steps' folder")
        
        if self.override_csv_path is None:
            console.info_missing_file({self.override_csv_path}, 'overrides')
        
        if self.map_df is None:
            console.print_missing_override_dict('medications', 'config.meds_dict')



    def _get_final_df(self, override_df):
        mapped_long_df = self.try_get_mapped_long_df(override_df)
        if mapped_long_df.empty:
            return self.df

        final_df = self.try_get_merged_final_df(self.df, mapped_long_df)

        return final_df



    def try_get_mapped_long_df(self, override_df): # called in OverrideManager        
        self.name = 'Name'
        override_df[self.name] = self._get_main_name(override_df['recommended_term'])

        if self.meds_dict_df is not None:
            mapped_df = self._get_mapped_df(override_df)
            return mapped_df
            
        return override_df



    def try_get_merged_final_df(self, df, mapped_long_df): # called in OverridePivot
        binary_df = self._get_binary_df(mapped_long_df)
        full_df = self._merge_full_df(df, binary_df)
        full_df = self._clean_full_df(full_df)

        return full_df



    def _get_meds_for_review(self):
        local_ai = LocalAI(schema = MedicationList, field_name = 'substances')
        extractor_configs = self._get_configs()
        extractor = ExtractorAI(local_ai, extractor_configs)
        df = extractor.get_for_review(self.df)
        df = self._get_add_to_ref_col(df)

        return df


    def _get_configs(self):
        extractor_configs = {
            'name': 'medications',
            'cols': config.med_text_cols,
            'prompt': config.prompt_meds,
            'schema': MedicationList}

        return extractor_configs



    def _get_add_to_ref_col(self, meds_df):
        if meds_df is None:
            return None
        
        is_missing = RefMap(self.meds_dict_df).is_missing(meds_df['recommended_term'])
        meds_df['add_to_ref'] = np.where(is_missing, 'MISSING IN REF', '')

        return meds_df



    def _get_main_name(self, term_column):
        if isinstance(term_column, pd.Series):
            main_names_column = RefMap(self.meds_dict_df).get_main_names(term_column)

            return main_names_column



    def _get_mapped_df(self, o_df):
        o_df[self.name] = o_df[self.name].astype(str).str.lower().str.strip()    
        mapped_df = self._merge_override_with_map(o_df)
        mapped_df = self._fillna_classes(mapped_df, o_df)

        return mapped_df



    def _merge_override_with_map(self, o_df):
        self.main = 'Generic Name'
        m_dict = self._get_clean_meds_dict_df()
        merged_df = pd.merge(
            o_df, m_dict, left_on = self.name, right_on = self.main, how = "left")
        
        return merged_df



    def _fillna_classes(self, mapped_df, o_df):
        mapped_df[self.main] = mapped_df[self.main].fillna(o_df[self.name])
        
        na_classes = self._get_na_class(mapped_df)
        classes_df = mapped_df[self.function].fillna(na_classes)
        mapped_df[self.function] = classes_df.str.lower().str.replace(' ', '_')
        
        return mapped_df



    def _get_clean_meds_dict_df(self):
        self.function = 'functional_class'
        if self.meds_dict_df is None:
            return pd.DataFrame(columns = [self.main, self.function])

        m_dict = self.meds_dict_df.copy()
        m_dict[self.main] = m_dict[self.main].astype(str).str.lower().str.strip()
        m_dict[self.function] = m_dict[self.function].astype(str).str.strip()
        
        return m_dict



    def _get_na_class(self, mapped_df):
        self.from_col = 'from_column'
        is_med = mapped_df[self.from_col].str.contains('med', case = False, na = False)
        na_classes = np.where(is_med, 'na_medication', 'supplement')
        na_classes_series = pd.Series(na_classes, index = mapped_df.index)

        return na_classes_series



    def _get_binary_df(self, long_df):
        class_binary = self._get_class_dummies_df(long_df)
        med_binary = self._get_med_dummies_df(long_df)    
        binary_df = self._get_merged_dummies_df(class_binary, med_binary)

        return binary_df



    def _merge_full_df(self, main_df, binary_df):
        full_df = pd.merge(main_df, binary_df, on = self.id_col, how = "left")
        
        new_binary_cols = self._get_all_new_binary_cols(binary_df)
        full_df[new_binary_cols] = full_df[new_binary_cols].fillna(0).astype(int)

        return full_df



    def _clean_full_df(self, full_df):
        full_df.columns = [
            col.replace(f'{self.temp_prefix}_', '').replace(' ', '_') 
            for col in full_df.columns]
        
        return full_df



    def _get_all_new_binary_cols(self, binary_df):
        new_binary_cols = [
            col for col in binary_df.columns 
            if col.startswith((f'{self.class_prefix}_', f'{self.temp_prefix}_'))]
        
        return new_binary_cols



    def _get_class_dummies_df(self, df):
        self.class_prefix = 'class'
        class_dummies = pd.get_dummies(df[self.function], prefix = self.class_prefix)
        class_dummies[self.id_col] = df[self.id_col].values
        class_matrix = class_dummies.groupby(self.id_col).max()
        
        return class_matrix



    def _get_med_dummies_df(self, df):
        self.temp_prefix = 'NEW_DUMMY'
        med_dumms = pd.crosstab(index = df[self.id_col], columns = df[self.main])
        med_dumms.columns = [f"{self.temp_prefix}_{col}" for col in med_dumms.columns]
        med_dummies_df = (med_dumms > 0).astype(int)

        return med_dummies_df



    def _get_merged_dummies_df(self, d1, d2):
        binary_df = pd.merge(
            d1, d2, left_index = True, right_index = True, how = 'outer').reset_index()

        return binary_df
