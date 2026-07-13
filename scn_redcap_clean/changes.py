class Changes:
    def __init__(self):
        self.step_name = str()
        self.previous_csv_name = str()
        self.current_csv_name = str()

        self.added_rows = 0
        self.deleted_rows = 0
        self.step_total_rows = 0

        self.added_ids = []
        self.deleted_ids = []
        self.added_ids_count = 0
        self.deleted_ids_count = 0
        
        self.added_columns = []
        self.deleted_columns = []
        self.added_column_count = 0
        self.deleted_column_count = 0
        
        self.details = {}