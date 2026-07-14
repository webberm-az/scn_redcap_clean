
from pathlib import Path
from . import config, paths
from .changes import Changes
from .duplicate_accounts import DuplicateAccounts
from .csv_kit import CsvKit
from .step import Step


class Audit:
    
    def __init__(self, original_data_path, revised_data_path):
        self.path_in = original_data_path
        self.path_out = revised_data_path
        self.csvkit = CsvKit()

        self.step_enum = self._get_step_enum()
        self.data_in = self.csvkit.robust_read(self.path_in)
        self.data_out = self.csvkit.robust_read(self.path_out)
        self.in_cols = set(self.data_in.columns)
        self.out_cols = set(self.data_out.columns)

        id = config.merge_on_id_column
        self.in_ids = set(self.data_in[id].dropna()) if id in self.data_in else set()
        self.out_ids = set(self.data_out[id].dropna()) if id in self.data_out else set()

        self._init_changes()
        self._insert_details()


    def _init_changes(self):
        self.changes = Changes()
        self.changes.step_name = self.step_enum.process_name
        self.changes.previous_csv_name = Path(self.path_in).name
        self.changes.current_csv_name = Path(self.path_out).name

        self.changes.added_rows = max(0, len(self.data_out) - len(self.data_in))
        self.changes.deleted_rows = max(0, len(self.data_in) - len(self.data_out))
        self.changes.step_total_rows = len(self.data_out)

        self.changes.added_ids = list(self.out_ids - self.in_ids)
        self.changes.deleted_ids = list(self.in_ids - self.out_ids)
        self.changes.added_ids_count = len(self.changes.added_ids)
        self.changes.deleted_ids_count = len(self.changes.deleted_ids)
        
        self.changes.added_columns = list(self.out_cols - self.in_cols)
        self.changes.deleted_columns = list(self.in_cols - self.out_cols)
        self.changes.added_column_count = len(self.changes.added_columns)
        self.changes.deleted_column_count = len(self.changes.deleted_columns)



    def _insert_details(self):
        match self.step_enum:
            case Step.translated:
                # self._translated()
                return

            case Step.duplicates:
                self._duplicate_accounts()
                return

            case Step.medications:
                # self._medications()
                return

            case Step.genomics:
                # self._genomics()
                return



    def _get_step_enum(self):
        filename = self.path_out.name
        for step in Step:
            is_step_file = step.process_name in filename or step.config_name in filename
            
            if is_step_file:
                return step
                
        raise ValueError(f"Unknown step file: {filename}")



    def _duplicate_accounts(self):
        if 'override' in str(self.path_out):
            return

        map_data, map_csvname = self._get_map()
        self._record_duplicate_details(map_data, map_csvname)



    def _get_map(self):
        map_csvname = DuplicateAccounts.map_csvname
        map_data = self.csvkit.path_to_df(map_csvname, paths.REF)
        
        return map_data, map_csvname



    def _record_duplicate_details(self, map_data, filename):
        if map_data is None or map_data.empty:
            return
            
        mappings_list = map_data.to_dict('records')
        self.changes.details[filename] = mappings_list
