import numpy as np
import pandas as pd

from . import config, schemas
from .ref_map import RefMap

class MedsMap:
    def __init__(self, meds_ref_data, override_data):
        self.meds_ref_data = meds_ref_data
        self.override_data = override_data
        self.name = 'Name'
        self.main_header = config.main_header
        self.function_header = config.function_header
        self.from_col = config.from_col

    def get_long_data(self):  
        override_data = self.override_data.copy()
        recommended_term = schemas.recommended_term_str()
        override_data[self.name] = self._get_main_name(override_data[recommended_term])

        if self.meds_ref_data is not None:
            mapped_data = self._get_mapped_data(override_data)
            return mapped_data
            
        return override_data

    def _get_main_name(self, term_column):
        if isinstance(term_column, pd.Series):
            ref_map = RefMap(self.meds_ref_data)
            main_names_column = ref_map.get_main_names(term_column)

            return main_names_column

    def _get_mapped_data(self, o_data):
        o_data[self.name] = o_data[self.name].astype(str).str.lower().str.strip()    
        mapped_data = self._merge_override_with_map(o_data)
        mapped_data = self._fillna_classes(mapped_data, o_data)

        return mapped_data

    def _merge_override_with_map(self, override_data):
        meds_ref_data = self._get_clean_meds_ref_data()
        merged_data = pd.merge(
            override_data, meds_ref_data, left_on = self.name,\
                 right_on = self.main_header, how = "left")
        
        return merged_data

    def _fillna_classes(self, mapped_data, override_data):
        mapped_data[self.main_header] = mapped_data[self.main_header].fillna(
            override_data[self.name])
        
        na_classes = self._get_na_class(mapped_data)
        class_data = mapped_data[self.function_header].fillna(na_classes)
        mapped_data[self.function_header] = class_data.str.lower().str.replace(' ', '_')
        
        return mapped_data

    def _get_clean_meds_ref_data(self):
        if self.meds_ref_data is None:
            return pd.DataFrame(columns = [self.main_header, self.function_header])

        data = self.meds_ref_data.copy()
        data[self.main_header] = data[self.main_header].astype(str).str.lower().str.strip()
        data[self.function_header] = data[self.function_header].astype(str).str.strip()
        
        return data

    def _get_na_class(self, data):
        is_med = data[self.from_col].str.contains('med', case = False, na = False)
        na_classes = np.where(is_med, 'na_medication', 'supplement')
        na_classes_series = pd.Series(na_classes, index = data.index)

        return na_classes_series
