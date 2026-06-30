from pathlib import Path
from typing import Dict, List, Set, Tuple
import pandas as pd
from . import config
from .csv_kit import CsvKit
from .duplicate_mapper import DuplicateMapper
from .reporter import Reporter


class Summary:

    def __init__(self, paths):
        self.paths = paths
        self.id_column = config.merge_on_id_column
        self.bday = config.filter_columns
        self.reporter = Reporter()
        self.mapper = DuplicateMapper('is_shared_birthdate')

    def get_sequential_summaries(self) -> None:
        """
        Gathers all archived files, sorts them, and pairs adjacent files 
        that share the same tracking version (e.g., v001 pairs with v001).
        """
        # Sorting guarantees: 01_merge_raw_v001 comes right before 02_translated_v001
        archived_files = sorted(list(self.paths.archive.glob("*.csv")), key=lambda p: p.name)

        for i in range(len(archived_files) - 1):
            base_file = archived_files[i]
            modified_file = archived_files[i + 1]

            if self._are_from_same_version_run(base_file, modified_file):
                self._generate_step_summary(base_file, modified_file)

    def _are_from_same_version_run(self, file_a: Path, file_b: Path) -> bool:
        """Verifies both files share the exact same _vNNN suffix."""
        version_a = self._extract_version_suffix(file_a)
        version_b = self._extract_version_suffix(file_b)
        
        # Ensure versions match and we aren't comparing v001 to v002
        return version_a is not None and version_a == version_b

    def _extract_version_suffix(self, path: Path):
        """Extracts the exact '_vNNN' string from the filename."""
        stem = path.stem
        if '_v' in stem:
            return f"_v{stem.rsplit('_v', 1)[-1]}"
        return None

    def _generate_step_summary(self, base_path: Path, modified_path: Path) -> None:
        """Processes the transition from one specific versioned file to the next."""
        version_tag = self._extract_version_suffix(base_path) or "_v001"
        
        # Clean names for documentation (e.g., "01_merge_raw" and "02_translated")
        base_stage = base_path.stem.replace(version_tag, "")
        mod_stage = modified_path.stem.replace(version_tag, "")
        
        comparison_key = f"{base_stage}_to_{mod_stage}"

        # Load explicit data snapshots
        base_df = pd.read_csv(base_path)
        modified_df = pd.read_csv(modified_path)
        
        # Look for general txt logs matching the modified stage base name
        general_explanation = self._read_explanation_log(mod_stage)

        # Handle deduplication specific mapping logic
        duplicate_mappings = None
        if "duplicate" in mod_stage.lower():
            duplicate_mappings = self.mapper.map_removed_duplicates(base_df, modified_df)

        # Build clean markdown
        markdown_content = self.reporter.generate_markdown_summary(
            step_name=f"{comparison_key.replace('_', ' ').title()} ({version_tag.strip('_')})",
            base_df=base_df,
            modified_df=modified_df,
            general_explanation=general_explanation,
            duplicate_mappings=duplicate_mappings
        )

        self._write_summary_file(comparison_key, version_tag, markdown_content)

    def _read_explanation_log(self, stage_base_name: str) -> str:
        """Finds matching static manual explanation notes."""
        explanation_path = self.paths.overrides / f"{stage_base_name}.txt"
        if explanation_path.exists():
            return explanation_path.read_text(encoding='utf-8')
        return ""

    def _write_summary_file(self, comparison_key: str, version_tag: str, content: str) -> None:
        """Writes the output file, keeping the version tag neatly inside the name."""
        output_name = f"{comparison_key}_{version_tag.strip('_')}_summary.md"
        output_file = self.paths.notes_overrides / output_name
        output_file.write_text(content, encoding='utf-8')
        print(f"| Summary Created | {output_file.name}")