from pathlib import Path
import shutil
from typing import Union

from .base_csv import BaseCSV
from .csv_kit import CsvKit

from . import config, console


ROOT = Path.cwd().resolve()

PROJECT = ROOT / 'project'
REF = PROJECT / 'ref'
REVIEW = PROJECT / 'review'
STEPS = PROJECT / 'steps'
OVERRIDES = PROJECT / 'overrides'


HIDDEN = PROJECT / '.__internal__'
RAW = HIDDEN / 'raw'
ARCHIVE = HIDDEN / 'archive'
NOTES = HIDDEN / 'notes'

NOTES_OVERRIDE = NOTES / 'override_summaries'
NOTES_JUSTIFY = NOTES / 'decision_logs'
SCRATCHPAD = NOTES / 'scratchpad.md'
TODO = NOTES / 'todo.md'

csvkit = CsvKit()

def init_directories():
    # Create main directories
    folders = [
        PROJECT, HIDDEN, STEPS, OVERRIDES, REVIEW, REF, 
        RAW, ARCHIVE, NOTES, NOTES_OVERRIDE, NOTES_JUSTIFY]
    
    for dir_path in folders:
        dir_path.mkdir(parents = True, exist_ok = True)
    
    SCRATCHPAD.touch(exist_ok = True)
    TODO.touch(exist_ok = True)



def setup_workspace():
    '''
    Create folders and copy files from user_data_source to __raw__ or ref based on configs.
    '''
    init_directories()

    orig_data_paths = _get_path_list()
    if not orig_data_paths:
        _create_orig_dir()
        return

    if not _is_data_dict_to_ref(orig_data_paths):
        return
    
    _meds_dict_to_ref(orig_data_paths)
    _to_raw(orig_data_paths)



def copy_meds_dict():
    '''Stand alone copy the meds dictionary to the ref folder before medications step'''
    orig_data_paths = _get_path_list()
    if not orig_data_paths:
        return
    _meds_dict_to_ref(orig_data_paths)



def make_dir(name):
    ''' create new (local) directory folder if needed '''
    dir_path = PROJECT / name
    dir_path.mkdir(parents = True, exist_ok = True)
    
    return dir_path



def _create_orig_dir():
    created_dir = ROOT / 'original_files'
    created_dir.mkdir(parents = True, exist_ok = True)
    config.original_data_folder = created_dir
    console.alert_missing_file('Original data to clean', config.original_data_folder)
    console.custom_alert('Missing', "Location of original data to clean set by 'config.original_data_folder' does not exist.")
    print(f"An '{created_dir.name}' folder has been created. config.original_data_folder has been updated to this location. Add your data before proceeding. \n ")

    return



def _get_path_list():
    if not config.original_data_folder:
        return []
    if isinstance(config.original_data_folder, (str, Path)): 
        path_list = [Path(config.original_data_folder)]
    else:
        path_list = [Path(p) for p in config.original_data_folder]

    valid_paths = _get_valid_path_list(path_list)
            
    return valid_paths



def _get_valid_path_list(path_list):
    valid_paths = []
    for path_obj in path_list:
        valid_paths = _get_valid_path(path_obj, valid_paths)
            
    return valid_paths



def _get_valid_path(path_obj, valid_paths):
    
    if not path_obj.is_absolute():
        path_obj = ROOT / path_obj
        
    if path_obj.exists() and path_obj.is_dir():
        valid_paths.append(path_obj)
            
    return valid_paths 



def _to_raw(orig_data_paths):
    _required_to_raw(orig_data_paths)
    if not _is_id_subset_csv2raw(orig_data_paths):
        ensure_id_subset_csv_to_raw()



def ensure_id_subset_csv_to_raw():
    id_subset_csv = csvkit.ensure_suffix(config.id_subset_csv)
    if Path(id_subset_csv) == Path('__base__.csv'):
        base_csv = BaseCSV()
        base_csv.create()



def _required_to_raw(orig_data_paths):
    required_csvs = _get_required_csv_list()

    for csv_name in required_csvs:
        _required_csv2raw(csv_name, orig_data_paths)



def _get_required_csv_list():
    required_csvs = set(config.csv_list)
    if config.raw_module_csv:
        required_csvs.add(config.raw_module_csv)
    
    return required_csvs



def _required_csv2raw(csv_name, orig_data_paths):
    csv_name = csvkit.ensure_suffix(csv_name)
    found_file = _find_file(csv_name, orig_data_paths)
    if not found_file:
        console.error_missing(csv_name, f'not found in {config.original_data_folder}')
        raise FileNotFoundError()
    
    shutil.copy2(found_file, RAW / csv_name)



def _is_id_subset_csv2raw(orig_data_paths):
    id_subset_csv = csvkit.ensure_suffix(config.id_subset_csv)
    if Path(id_subset_csv) == Path('__base__.csv'):
        return False
        
    found_file = _find_file(id_subset_csv, orig_data_paths)
    if found_file:
        shutil.copy2(found_file, RAW / id_subset_csv)
        return True

    _loud_alerts_config_change()
    config.id_subset_csv = '__base__'
    
    return False
    


def _loud_alerts_config_change():
    message_reset = "\n Resetting 'config.id_subset_csv' to default:\n config.id_subset_csv = '__base__'"
    console.custom_alert('ALERT ALERT', message_reset)
    
    message_not_found = f"not found in '{config.original_data_folder}'"
    console.error_missing(config.id_subset_csv, message_not_found)
    print(f"Replacing '{config.id_subset_csv}' with '__base__' based on active {config.merge_on_id_column}'s in '{config.raw_module_csv}' for '{config.modules}'")



def _is_data_dict_to_ref(orig_data_paths):
    orig_data_dict = _find_file(config.data_dict, orig_data_paths)
    
    if not orig_data_dict:
        console.alert_missing_config_file('ref','data dictionary', 'config.data_dict')
        return False

    orig_data_dict = _confirm_required_columns(orig_data_dict)
    if not orig_data_dict:
        return False
    
    shutil.copy2(orig_data_dict, REF / config.data_dict)
    return True
    


def _find_file(filename, folders) -> Union[Path, None]:
    ''' Helper to locate a file across one or more source directories. '''

    # is there a cleaner way to code this ???
    for folder in folders:
        found_path = _search_folder(filename, folder)
        if found_path:
            return found_path
    
    return None



def _search_folder(filename, folder) -> Union[Path, None]:
    ''' Searches all files in folder, including subfolder files '''
    for file_path in folder.rglob(filename):
        if file_path.is_file():
            return file_path
            
    return None



def _meds_dict_to_ref(orig_data_paths):
    meds_dict_src = _find_file(config.meds_dict, orig_data_paths)
    if meds_dict_src:
        shutil.copy2(meds_dict_src, REF / config.meds_dict)



def _confirm_required_columns(orig_data_dict):            
    missing_cols = _get_missing_cols(orig_data_dict)
    if missing_cols:
        message = f'column(s) are not in {config.data_dict}. Ensure correct file and data dictionary configs.'
        console.error_missing(missing_cols, message)
        return None
    
    return orig_data_dict



def _get_missing_cols(file_path):
    required_columns = [
        config.module_column, config.field_type_column, config.col_names_column] 
        
    data_dict_df = csvkit.robust_read(file_path)
            
    missing_cols = [col for col in required_columns if col not in data_dict_df]

    return missing_cols

