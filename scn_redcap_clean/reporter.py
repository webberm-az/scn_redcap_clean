from typing import Dict, List, Optional
import pandas as pd
from . import config


class Reporter:

    def __init__(self, explanation_column: str = 'override_explanation'):
        self.id_column = config.merge_on_id_column
        self.explanation_column = explanation_column

    def add_markdown_summary(
        self, 
        step_name: str, 
        base_df: pd.DataFrame, 
        modified_df: pd.DataFrame, 
        general_explanation: str = '',
        duplicate_mappings: Optional[Dict[str, List[str]]] = None
    ) -> str:
        '''Constructs a clean Markdown representation of changes between states.'''
        lines = [
            f"# Step Summary: {step_name.replace('_', ' ').title()}",
            '\n## Base Metrics',
            f'* **Initial Row Count:** {len(base_df)}',
            f'* **Adjusted Row Count:** {len(modified_df)}',
            f'* **Rows Dropped:** {len(modified_df) - len(base_df)} rows'
        ]

        # Extract specific column commentary if present
        if self.explanation_column in base_df.columns:
            lines.append('\n## Column-Level Override Explanations')
            commentary_df = base_df.dropna(subset=[self.explanation_column])
            
            if not commentary_df.empty:
                for _, row in commentary_df.iterrows():
                    p_id = row[self.id_column]
                    note = row[self.explanation_column]
                    lines.append(f'* **Participant {p_id}:** {note}')
            else:
                lines.append('*No specific column overrides noted.*')

        # Inject Duplicate Submission Mapping Detail if relevant
        if duplicate_mappings:
            lines.append('\n## Duplicate Participant Mappings (Same Birthdate)')
            lines.append('The following secondary submissions were merged/dropped into the primary record:')
            for primary_id, omitted_ids in duplicate_mappings.items():
                lines.append(f"* **Primary ID {primary_id}** consumed repeated submission IDs: `{', '.join(omitted_ids)}`")

        # Append general summary documentation at the bottom
        if general_explanation.strip():
            lines.append('\n---')
            lines.append('## General Step Explanations')
            lines.append(general_explanation.strip())

        return '\n'.join(lines)