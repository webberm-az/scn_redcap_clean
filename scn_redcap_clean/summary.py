from . import paths, utils
from .data_change_manager import DataChangeManager
from .summary_formatter import SummaryFormatter
from .step import Step
from .step_manager import StepManager
from .version import Version

class Summary:
    
    def __init__(self):
        self.step_manager = StepManager()
        self.version = Version()
        self.all_changes = []

    def to_file(self):
        self._run_data_change_record()
        formatter = SummaryFormatter(self.all_changes)
        summary = formatter.get_summary()
        if summary is None:
            return

        self._write(summary)

    def _write(self, summary):
        filepath = paths.STEPS / 'cleaning_summary.md'
        
        with open(filepath, 'w') as file:
            file.write(summary)

    def _run_data_change_record(self):
        self._build_step_records()
        self._build_manual_overrides_records()
        self._sort_changes()

    def _build_step_records(self):
        
        step_files = self.step_manager.get_paths_steps()

        for file_number in range(len(step_files) - 1):
            self._build_step_record(step_files, file_number)

    def _build_step_record(self, step_files, file_number):
        previous_path = step_files[file_number]
        revised_path = step_files[file_number + 1]

        self._record_changes(previous_path, revised_path)

    def _build_manual_overrides_records(self):
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

    def _record_override_changes(self, step):
        if step is Step.clinical:
            return

        path_original, path_revised = self._override_paths(step)
        is_paths = self._is_paths(path_original, path_revised)
        if not is_paths:
            return

        self._record_changes(path_original, path_revised)

    def _override_paths(self, step):
        review_name = utils.get_review_cvsname(step.process_name)
        path_review = self.version.get_last_version_path(review_name)
        override_name = utils.get_manual_cvsname(step.process_name)
        path_override = self.version.get_last_version_path(override_name)

        return path_review, path_override

    def _is_paths(self, path_original, path_revised):
        is_path_original = path_original is not None and path_original.exists()
        is_path_revised = path_revised is not None and path_revised.exists()

        return is_path_original and is_path_revised

    def _record_changes(self, original_data_path, revised_data_path):
        data_change_manager = DataChangeManager(original_data_path, revised_data_path)
        record = data_change_manager.build_record()
        self.all_changes.append(record)
