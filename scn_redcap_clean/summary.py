from . import paths
from .audit import Audit
from .step import Step
from .step_manager import StepManager
from .version import Version

class Summary:
    
    def __init__(self):
        self.step_manager = StepManager()
        self.version = Version()
        self.all_changes = []
        self._run_audits()


    def changes(self):
        summary = self._write()
        if summary is None:
            return

        self._create(summary)


    def _create(self, summary):
        filepath = paths.STEPS / 'step_changes.md'
        
        with open(filepath, 'w') as file:
            file.write(summary)


    def _write(self):
        self.record = ['# Steps Summary \n']
        self.record.append('--- \n')
        
        if not self.all_changes:
            return self.record.append('No steps recorded \n')

        self._write_changes()

        return '\n'.join(self.record)



    def _write_changes(self):
        self.summarized_step_names = []
        for change in self.all_changes:
            self._write_change(change)
    


    def _write_change(self, change):
        self._step_header(change)
        self._files_header(change)
        self. _body(change)
        self.record.append('\n--- \n')



    def _body(self, change):
        self._rows(change)
        self._columns(change)
        self._details(change)


    def _step_header(self, change):
        formated_step_name = change.step_name.replace('_', ' ').title()
        if formated_step_name not in self.summarized_step_names:
            self.record.append(f'### {formated_step_name}')
            self.summarized_step_names.append(formated_step_name)



    def _files_header(self, change):
        subtitle = f'{change.previous_csv_name}  -->  {change.current_csv_name}\n'
        self._append_header(subtitle)



    def _rows(self, change):
        self._rows_counts(change)
        is_id_change = change.added_ids or change.deleted_ids_count != 0
        if not is_id_change:
            return

        self.record.append(f'\n    * *Added IDs:* {change.added_ids  }  \n    * *Deleted IDs:* {change.deleted_ids}')



    def _rows_counts(self, change):
        rows = self._format_counts('Rows', change.added_rows, change.deleted_rows)
        self.record.append(f'{rows}  |   Current Total {change.step_total_rows}')

        unique_ids = self._format_counts(
            'Unique IDs', change.added_ids_count, change.deleted_ids_count)
        self.record.append(f'{unique_ids}\n')



    def _columns(self, change):
        if not change.added_column_count > 0 or not change.deleted_column_count > 0:
            return 

        self._added_columns(change)
        self._deleted_columns(change)



    def _added_columns(self, change):
        if change.added_column_count > 0:
            self._append_count_list(
                'Added Columns', change.added_column_count, change.added_columns)



    def _deleted_columns(self, change):
        if change.added_column_count > 0:
            self._append_count_list(
                'Dropped Columns', change.deleted_column_count, change.deleted_columns)



    def _details(self, change):
        ''' Unpacks details dictionary to readable markdown '''        
        for filename, data_list in change.details.items():
            if not data_list:
                return

            self._append_detail(filename, data_list)
    


    def _append_detail(self, filename, data_list):
        header = self._snake_to_title(filename)
        self._append_header(header)
        if isinstance(data_list[0], dict):
            self._append_table(data_list)
        else:
            self._append_list(data_list)
            
        self.record.append('') 



    def _append_header(self, header):
        formatted_header = f'\n#### {header} \n'
        self.record.append(formatted_header)



    def _append_table(self, data_list):
        keys = list(data_list[0].keys())
        
        headers = [self._snake_to_title(key) for key in keys]
        
        self._table_row(headers)
        separators = ['---'] * (len(headers) - 1) + ['---:']
        self._table_row(separators)
        
        for item in data_list:
            row_values = self._get_row_values(item, keys)    
            self._table_row(row_values)


    def _table_row(self, text):
        self.record.append('| ' + ' | '.join(text) + ' |')



    def _get_row_values(self, item, keys):
        row_values = []
        for key in keys:
            value = self._get_cell_value(item, key)
            row_values.append(value)

        return row_values



    def _get_cell_value(self, item, key):
        value = str(item.get(key, '')).strip()
        if value == 'nan': 
            value = '-'
        
        return value



    def _snake_to_title(self, snake_case):
        _title = snake_case.replace('_', ' ').title()

        return _title



    def _append_list(self, data_list):
        for item in data_list:
            self.record.append(f'* {item}')



    def _append_count_list(self, label, count, listed):
        self.record.append(f"* **{label} ({count}):** `{', '.join(listed)}`")



    def _format_counts(self, label, plus, minus):
        fstring = f'* **{label}:**  +{plus } | -{minus }'

        return fstring



    def _run_audits(self):
        self._audit_steps()
        self._audit_manual_overrides()
        self._sort_changes()



    def _audit_steps(self):
        
        step_files = self.step_manager.get_paths_steps()

        for file_number in range(len(step_files) - 1):
            self._audit_step(step_files, file_number)



    def _audit_step(self, step_files, file_number):
        previous_path = step_files[file_number]
        revised_path = step_files[file_number + 1]

        self._record_step_changes(previous_path, revised_path)



    def _audit_manual_overrides(self):
        for step in Step:
            self._record_override_changes(step)


            
    def _sort_changes(self):
        self.all_changes.sort(key = self._get_step_order)



    def _get_step_order(self, change):
        steps = [step.process_name for step in Step]
        if change.step_name not in steps:
            at_end = float('inf')
            return at_end
            
        step_order = steps.index(change.step_name)

        return step_order



    def _override_paths(self, step):
        review_name = f'{step.process_name}_for_review'
        path_review = self.version.get_last_version_path(review_name)

        override_name = f'{step.process_name}_manual_override'
        path_override = self.version.get_last_version_path(override_name)

        return path_review, path_override



    def _record_override_changes(self, step):
        if step is Step.clinical:
            return

        path_original, path_revised = self._override_paths(step)
        is_paths = self._is_paths(path_original, path_revised)
        if not is_paths:
            return

        self._record_step_changes(path_original, path_revised)



    def _is_paths(self, path_original, path_revised):
        is_path_original = path_original is not None and path_original.exists()
        is_path_revised = path_revised is not None and path_revised.exists()

        return is_path_original and is_path_revised



    def _record_step_changes(self, original_data_path, revised_data_path):
        audit = Audit(original_data_path, revised_data_path)
        self.all_changes.append(audit.changes)
