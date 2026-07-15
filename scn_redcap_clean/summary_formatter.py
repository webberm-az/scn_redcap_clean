class SummaryFormatter:
    def __init__(self, data_changes: list):
        self.changes = data_changes
        self.record = ['# Cleaning Summary \n', '--- \n']
        self.summarized_step_names = []
    
    def get_summary(self):        
        if not self.changes:
            self.record.append('No steps recorded \n')
            return '\n'.join(self.record)

        self._append_summary()

        return '\n'.join(self.record)

    def _append_summary(self):
        self.summarized_step_names = []
        for change in self.changes:
            self._append_change(change)

    def _append_change(self, change):
        self._step_header(change)
        self._files_header(change)
        self._body(change)
        self._append_section_divider()

    def _step_header(self, change):
        formated_step_name = change.step_name.replace('_', ' ').title()
        if formated_step_name not in self.summarized_step_names:
            self._append_heading3(formated_step_name)
            self.summarized_step_names.append(formated_step_name)

    def _files_header(self, change):
        subtitle = f'{change.previous_csv_name} &nbsp;&nbsp; ---> &nbsp;&nbsp; \
            {change.current_csv_name}\n'
        self._append_heading4(subtitle)

    def _body(self, change):
        self._rows(change)
        self._columns(change)
        self._details(change)

    def _rows(self, change):
        self._rows_counts(change)
        is_id_change = change.added_ids or change.deleted_ids_count != 0
        if not is_id_change:
            return

        self._append_sub_bullet('Added IDs', change.added_ids)
        self._append_sub_bullet('Deleted IDs', change.deleted_ids)

    def _rows_counts(self, change):
        rows = self._format_counts('Rows', change.added_rows, change.deleted_rows)
        self.record.append(
            f'{rows}  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Current Total &nbsp; {change.total_rows_count}')

        unique_ids = self._format_counts(
            'Unique IDs', change.added_ids_count, change.deleted_ids_count)
        self.record.append(f'{unique_ids}\n')

    def _columns(self, change):
        is_unchanged_count = change.added_column_count == 0 and \
            change.deleted_column_count == 0
        if is_unchanged_count:
            return 

        self._added_columns(change)
        self._deleted_columns(change)

    def _added_columns(self, change):
        if change.added_column_count > 0:
            self._append_count_list(
                'Added Columns', change.added_column_count, change.added_columns)

    def _deleted_columns(self, change):
        if change.deleted_column_count > 0:
            self._append_count_list(
                'Dropped Columns', change.deleted_column_count, change.deleted_columns)

    def _details(self, change):
        ''' Unpacks details dictionary to readable markdown '''        
        for filename, data_list in change.details.items():
            if not data_list:
                continue
                
            self._append_detail(filename, data_list)
    
    def _append_detail(self, filename, data_list):
        self._append_section_divider()
        header = self._snake_to_title(filename)
        self._append_heading4(header)
        if isinstance(data_list[0], dict):
            self._append_table(data_list)
        else:
            self._append_list(data_list)
            
        self.record.append('') 

    def _append_table(self, data_list):
        keys = list(data_list[0].keys())
        
        headers = [self._snake_to_title(key) for key in keys]
        
        self._append_table_header(headers)
        
        for item in data_list:
            row_values = self._get_row_values(item, keys)    
            self._table_row(row_values)

    def _append_table_header(self, headers):
        self._table_row(headers)
        right_align_column = ['---:']
        separators = ['---'] * (len(headers) - 1) + right_align_column
        self._table_row(separators)

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


    # MD formatting

    def _table_row(self, text):
        self.record.append('| ' + ' | '.join(text) + ' |')

    def _append_sub_bullet(self, label, contents):
        self.record.append(f'    * *{label}:* &nbsp;&nbsp; {contents}  \n')

    def _append_section_divider(self):
        self.record.append('\n--- \n')

    def _append_heading3(self, header):
        formatted_header = f'### {header} \n'
        self.record.append(formatted_header)

    def _append_heading4(self, header):
        formatted_header = f'\n#### {header} \n'
        self.record.append(formatted_header)

    def _append_list(self, data_list):
        for item in data_list:
            self.record.append(f'* {item}')

    def _append_count_list(self, label, count, listed):
        self.record.append(f"* **{count} {label}:**\n")
        self.record.append(f"    {', &nbsp;'.join(listed)}")

    def _snake_to_title(self, snake_case):
        _title = snake_case.replace('_', ' ').title()

        return _title

    def _format_counts(self, label, plus, minus):
        fstring = f'* **{label}:** &nbsp;&nbsp; +{plus} &nbsp;&nbsp;| &nbsp; -{minus} &nbsp;&nbsp;'

        return fstring
