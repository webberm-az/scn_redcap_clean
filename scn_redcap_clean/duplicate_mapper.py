from typing import Dict, List
import pandas as pd
from . import config



class DuplicateMapper:
    
    def __init__(self, shared_column: str):
        self.id_column = config.merge_on_id_column
        self.birthdate_column = config.filter_columns
        self.shared_column = shared_column

    def map_removed_duplicates(self, review_df: pd.DataFrame, manual_override_df: pd.DataFrame) -> Dict[str, List[str]]:
        '''
        Maps the final retained participant_id for a birthdate to the participant_ids 
        of rows that were dropped, skipping rows flagged as 'shared' (Yes).
        '''
        # Filter down to true duplicates that were actually removed
        retained_ids = set(manual_override_df[self.id_column].dropna().astype(str))
        
        # Identify rows marked as 'Yes' for shared birthdate to exclude them from mapping
        shared_mask = review_df[self.shared_column].astype(str).str.strip().str.lower() == 'yes'
        unshared_review_df = review_df[~shared_mask]

        birthdate_groups = unshared_review_df.groupby(self.birthdate_column)
        id_mappings: Dict[str, List[str]] = {}

        for birthdate, group in birthdate_groups:
            group_ids = group[self.id_column].astype(str).tolist()
            
            # Find which ID in this birthdate cluster was kept in the manual overrides
            final_retained = [pid for pid in group_ids if pid in retained_ids]
            
            if final_retained:
                # Keep the last/highest ID as final, map others to it
                target_id = final_retained[-1]
                removed_ids = [pid for pid in group_ids if pid != target_id]
                
                if removed_ids:
                    id_mappings[target_id] = id_mappings.get(target_id, []) + removed_ids

        return id_mappings