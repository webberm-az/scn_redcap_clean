from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class DataChange:
    step_name: str = ""
    previous_csv_name: str = ""
    current_csv_name: str = ""

    added_rows: int = 0
    deleted_rows: int = 0
    total_rows_count: int = 0

    added_ids: List[Any] = field(default_factory = list)
    deleted_ids: List[Any] = field(default_factory = list)
    added_ids_count: int = 0
    deleted_ids_count: int = 0
    
    added_columns: List[str] = field(default_factory = list)
    deleted_columns: List[str] = field(default_factory = list)
    added_column_count: int = 0
    deleted_column_count: int = 0
    
    details: Dict = field(default_factory = dict)