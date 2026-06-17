from pathlib import Path
from typing import Union


class Paths:
    
    def __init__(self, raw_data_source: Union[str, Path] = 'raw'):
        self.root = Path.cwd().resolve()
        self.set_raw_data_path(raw_data_source, strict = False)
        self.archive = self._make_dir('archive')
        self.stages = self._make_dir('steps')
        self.overrides = self._make_dir('overrides')
        self.review = self._make_dir('review')
        self.ref = self._make_dir('ref')
        self.docs = self._make_dir('docs')
        self.notes = self._make_dir('notes')
        self._init_notes_subcontents()
        self._make_notes_subcontents()
    


    def _make_dir(self, name): # auto created directory folders
        dir_path = self.root / name
        dir_path.mkdir(parents = True, exist_ok = True)
        return dir_path



    def _init_notes_subcontents(self):
        self.notes_overrides = self.notes / 'override_summaries'
        self.notes_justifications = self.notes / 'decision_logs'
        self.scratchpad = self.notes / 'scratchpad.md'
        self.todo = self.notes / 'todo.md'



    def _make_notes_subcontents(self):
        self.notes_overrides.mkdir(parents=True, exist_ok=True)
        self.notes_justifications.mkdir(parents=True, exist_ok=True)
        if not self.scratchpad.exists():
            self.scratchpad.touch()
        
        if not self.todo.exists():
            self.todo.touch()



    def set_raw_data_path(self, raw_data_source, strict = True):
        '''Updates the raw data location and verifies it exists.'''
        self.try_set_raw_path(raw_data_source)
        self._if_not_exist_make_raw_dir()
    


    def try_set_raw_path(self, raw_data_source):
        input_path = Path(raw_data_source)
        self.get_path(input_path)
        self.raw_data_source = raw_data_source



    def get_path(self, input_path: Path):
        if input_path.is_absolute(): # if input is full path
            self.raw = input_path
        else: # if not full path assume in root directory
            self.raw = self.root / input_path



    def _if_not_exist_make_raw_dir(self):
        if not self.raw.exists():
            self._create_raw_dir_and_alert()



    def _create_raw_dir_and_alert(self):
        self.raw.mkdir(parents = True, exist_ok = True)
        print(f'\n| Alert | Raw data directory not found at: {self.raw} \n'\
            'A raw folder has been created. Add your data before proceeding. \n')

    
