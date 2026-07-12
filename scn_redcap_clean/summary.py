from . import paths

class Summary:
    
    def __init__(self, step_changes: list):
        self.step_changes = step_changes

    def changes(self):
        markdown_report = self._generate_markdown()
        log_filepath = paths.NOTES_OVERRIDE / 'step_changes.md'
        
        with open(log_filepath, 'w') as f:
            f.write(markdown_report)
            
    def _generate_markdown(self):
        lines = ["# Summary \n\n"]
        for changes in self.step_changes:
            lines.append(f"## {changes.step_name}")
            lines.append(f"* Rows Added: {changes.added_rows}")
            lines.append(f"* Rows Deleted: {changes.deleted_rows}\n")
        return '\n'.join(lines)