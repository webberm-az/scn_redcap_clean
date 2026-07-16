import pandas as pd # external import

# local imports
from . import config, paths, utils
from .csv_writer import CsvWriter

class DuplicateMap:

    def __init__(self, full_data, cleaned_data, protected_ids):
        self.subset_columns = config.filter_columns
        self.id_col = config.merge_on_id_column
        self._full_data = full_data.copy()

        self._full_data[self.id_col] = utils.format_id_column(
            self._full_data[self.id_col])

        # in functions
        self.is_duplicated = self._full_data.duplicated(self.subset_columns, False)
        self._duplicates_data = self._full_data[self.is_duplicated]
        self._cleaned_data = cleaned_data.copy()
        formatted_protected = [utils.format_id(i) for i in protected_ids]
        self._protected_ids = set(formatted_protected)
        
        self._cleaned_ids = set(self._cleaned_data[self.id_col])
        self._map_data = []
        self.map_csvname = ''
        self.csv_writer = CsvWriter()

    def write_to_file(self):
        if self._duplicates_data.empty:
            return

        self._map_ids()
        self.map_data = pd.DataFrame(self._map_data)
        self.csv_writer.main_and_archive(self.map_data, self.map_csvname, paths.REF)

        return

    def _map_ids(self):
        grouped_duplicates = self._duplicates_data.groupby(self.subset_columns)
        
        for subset_key, subset in grouped_duplicates:
            subset_ids = set(subset[self.id_col])
            self._map_subset(subset_key, subset_ids)

    def _map_subset(self, subset_key, subset_ids):
        deleted_ids = subset_ids - self._cleaned_ids
        if not deleted_ids:
            return
            
        record = {
            'duplicate_match_value': self._format_duplicate_keys(subset_key),
            'kept_id': self._get_kept_ids(subset_ids, deleted_ids),
            'deleted_ids': self._join_ids(deleted_ids),
            'shared_birthdate_flag': self._is_protected(subset_ids)
        }

        self._map_data.append(record)

    def _format_duplicate_keys(self, duplicate_keys):
        if isinstance(duplicate_keys, tuple):
            return ' ,  '.join(map(str, duplicate_keys))
            
        return str(duplicate_keys)

    def _get_kept_ids(self, subset_ids, deleted_ids):
        ids = set(subset_ids) - set(deleted_ids)
        ids = self._join_ids(ids)

        return ids

    def _is_protected(self, subset_ids):
        is_protected = any(subset_id in self._protected_ids for subset_id in subset_ids)
        if is_protected:
            return True
            
        return ''

    def _join_ids(self, ids):
        formatted_ids = [utils.format_id(i) for i in ids]
        sorted_ids = sorted(list(formatted_ids))
        joined_ids = ', '.join(map(str, sorted_ids))

        return joined_ids
