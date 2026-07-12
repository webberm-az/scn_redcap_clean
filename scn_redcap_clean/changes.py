class Changes:
    def __init__(self, step_enum):
        self.step_name = step_enum.process_name
        self.added_rows = 0
        self.deleted_rows = 0
        self.added_cols = []
        self.deleted_cols = []
        self.details = {}