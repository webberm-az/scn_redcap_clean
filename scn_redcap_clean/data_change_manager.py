
from pathlib import Path
from . import config, paths
from .data_change import DataChange
from .duplicate_accounts import DuplicateAccounts
from .csv_kit import CsvKit
from .step import Step

class DataChangeManager:
    
    def __init__(self, original_data_path, revised_data_path):
        self.path_in = Path(original_data_path)
        self.path_out = Path(revised_data_path)
        self.csvkit = CsvKit()

        self.step_enum = self._get_step_enum()
        self.data_in = self.csvkit.robust_read(self.path_in)
        self.data_out = self.csvkit.robust_read(self.path_out)
        self.in_cols = set(self.data_in.columns)
        self.out_cols = set(self.data_out.columns)

        self.in_ids = self._extract_ids(self.data_in)
        self.out_ids = self._extract_ids(self.data_out)
        self.details = {}

    def build_record(self):
        self._get_details()
        data_change = self._get_data_change()

        return data_change

    def _extract_ids(self, data):
        id = config.merge_on_id_column
        id_set = set(data[id].dropna()) if id in data else set()

        return id_set

    def _get_details(self):
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

    def _get_data_change(self):
        added_ids_list, deleted_ids_list = self._id_change_lists()
        added_cols_list, deleted_cols_list = self._col_change_lists()

        data_change = DataChange(
            step_name = self.step_enum.process_name,
            previous_csv_name = self.path_in.name,
            current_csv_name = self.path_out.name,

            added_rows = max(0, len(self.data_out) - len(self.data_in)),
            deleted_rows = max(0, len(self.data_in) - len(self.data_out)),
            total_rows_count = len(self.data_out),

            added_ids = added_ids_list,
            deleted_ids = deleted_ids_list,
            added_ids_count = len(added_ids_list),
            deleted_ids_count = len(deleted_ids_list),
            
            added_columns = added_cols_list,
            deleted_columns = deleted_cols_list,
            added_column_count = len(added_cols_list),
            deleted_column_count = len(deleted_cols_list),
            
            details = self.details
        )

        return data_change

    def _id_change_lists(self):
        added_ids_list = list(self.out_ids - self.in_ids)
        deleted_ids_list = list(self.in_ids - self.out_ids)

        return added_ids_list, deleted_ids_list

    def _col_change_lists(self):
        added_cols_list = list(self.out_cols - self.in_cols)
        deleted_cols_list = list(self.in_cols - self.out_cols)

        return added_cols_list, deleted_cols_list

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

        return

    def _get_map(self):
        map_csvname = DuplicateAccounts.get_map_csvname()
        map_data = self.csvkit.path_to_df(map_csvname, paths.REF)
        
        return map_data, map_csvname

    def _record_duplicate_details(self, map_data, filename):
        if map_data is None or map_data.empty:
            return
            
        mappings_list = map_data.to_dict('records')
        self.details[filename] = mappings_list
