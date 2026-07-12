
from .changes import Changes
from .csv_kit import CsvKit
from .step import Step
from . import paths

class Audit:
    
    def __init__(self, step_enum, data_in, data_out):
        self.step_enum = step_enum
        self.data_in = data_in.copy()
        self.data_out = data_out.copy()
        self.in_cols = set(self.data_in.columns)
        self.out_cols = set(self.data_out.columns)
        self.csvkit = CsvKit()

        self.changes = Changes(self.step_enum)
        self.changes.added_rows = max(0, len(self.data_out) - len(self.data_in))
        self.changes.deleted_rows = max(0, len(self.data_in) - len(self.data_out))
        self.changes.added_cols = list(self.out_cols - self.in_cols)
        self.changes.deleted_cols = list(self.in_cols - self.out_cols)


    def overrides(self): # assuming there's a better way to do this...
        if self.step_enum is Step.translated:
            # self._translated()
            return

        if self.step_enum is Step.duplicates:
            self._duplicates()
            return

        if self.step_enum is Step.medications:
            # self._medications()
            return

        if self.step_enum is Step.genomics:
            # self._genomics()
            return

        # ??? instead
        #method_name = f"_{self.step_enum.process_name}"
        #step_method = getattr(self, method_name, None)
        
        #if step_method:
            #step_method()
            


    def _duplicates(self):
        map_df = self._read_map()
        self._record_duplicate_details(map_df)



    def _read_map(self):
        map_csvname = f"{self.step_enum.process_name}_submission_id_map"
        map_df = self.csvkit.path_to_df(map_csvname, paths.REF)
        
        return map_df



    def _record_duplicate_details(self, map_data):
        filename = f'{self.step_enum.process_name}_mappings'

        if map_data is None or map_data.empty:
            self.changes.details[filename] = []
            return
            
        mappings_list = map_data.to_dict(orient = 'records')
        self.changes.details[filename] = mappings_list