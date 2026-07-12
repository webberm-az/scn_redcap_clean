from pathlib import Path
from typing import Union, List, Pattern, Any, Iterable, cast

import pandas as pd # external import

from . import console


auto = {"id": "utils.auto"} # creates a parameter_input = utils.auto 


def is_n_matches(pattern: Pattern[str], string: str, n: int) -> bool:
    ''' Returns True if at least n of pattern elements found in string '''
    count = 0

    for _ in pattern.finditer(string):
        count += 1
        if count >= n:
            return True

    return False



def get_max_file_index(existing_files, extract_int_func):
    '''
    Scans a directory and extracts an ingteger using extract_int_func.
    extract_int_func(filename_str) must return an int (or None).
    '''
    max_num = 0
    latest_file = None

    for file in existing_files:
        number = extract_int_func(file)
        
        if number is not None and number > max_num:
            max_num = number
            latest_file = file

    return max_num, latest_file



#       df:

def get_cols_if_in_df(
        df: pd.DataFrame, override_df: pd.DataFrame, id_col: Any) -> List[Any]:
    ''' Returns shared columns between df and override_df excluding id_col '''
    shared_cols = set(df.columns) & set(override_df.columns)
    clean_shared_cols = [col for col in shared_cols if col != id_col]
    
    return clean_shared_cols



def if_missing_drop_row(
        df: pd.DataFrame, filter_subset: Union[str, Iterable[str]]) -> pd.DataFrame:
    ''' Removes rows where col is blank or missing '''
    subset = [filter_subset] if isinstance(filter_subset, str) else list(filter_subset)

    df[subset] = df[subset].replace('', pd.NA) # set empty to NA
    df = df.dropna(subset = subset, how = 'all') # drop all NA

    return df
    



def add_column_if_dne(colname: Any, df: pd.DataFrame, input: Any = '') -> pd.DataFrame:
    if colname not in df.columns:
        df[colname] = input
    
    return df



def match_rows_to_ref_id( # check ref_df ????
        df: pd.DataFrame, ref_df: pd.DataFrame, id_column: Any) -> pd.Series:
    df[id_column] = df[id_column].astype('float64')
        
    return cast(pd.Series, df[id_column])



def is_df_identical(current_df, last_df):
    if last_df.astype(str).equals(current_df.astype(str)):
        return True

    return False



def make_duplicate_orig_cols(df: pd.DataFrame, rep_cols: List[str]) -> pd.DataFrame:
    '''
    Creates df with duplicated rep_cols with '_orig' suffix added to col names
    '''
    for col in rep_cols: 
        df[f'{col}_orig'] = df[col]

    return df



def format_id_column(id_column_set) -> pd.DataFrame:
    ''' 
    Formats IDs to strings, dropping .0 for integers but keeping true decimals 
    '''
    id_column_set = id_column_set.copy()

    id_column_set = id_column_set.apply(format_id)
    
    return id_column_set


def format_id(value):
    if pd.isna(value) or value == '':
        return value
        
    try:
        float_val = float(value)
        if float_val.is_integer():
            return str(int(float_val))
        return str(float_val)
    except (ValueError, TypeError):
        return str(value)



#       txt:

def write_txt_file(content: str, filename: Union[str, Path], output_dir: Path) -> None:
    '''
    Safely writes a string content to a txt within an output directory.
    '''        
    file_path = get_txt_filepath(filename, output_dir)
    create_txt(content, filename, file_path)



def create_txt(content, filename, file_path):
    # Path.write_text automatically opens, writes, and closes the file safely.
    file_path.write_text(content, encoding = 'utf-8')
    console.file_saved(filename, file_path)



def get_txt_filepath(filename, output_dir):
    filename = ensure_txt_suffix(filename)
    file_path = output_dir / filename

    return file_path



def ensure_txt_suffix(filename):
    ''' Adds '.txt' to name if needed '''
    filename = ensure_suffix(filename, '.txt')
    
    return filename



def ensure_suffix(filename: Union[str, Path], suffix_str) -> Path:
        ''' Adds suffix_str to name if needed '''

        if not suffix_str.startswith('.'):
            suffix_str = f'.{suffix_str}'

        filename = Path(filename).with_suffix(suffix_str)

        return filename



def append_to_txt(content: str, filename: Union[str, Path], output_dir: Path) -> None:
    '''
    Appends text to a file without overwriting existing content.
    Creates the file if it doesn't exist.
    '''        
    file_path = get_txt_filepath(filename, output_dir)
    _append_txt(content, file_path)
    action = 'Text entry added'
    console.view_txt_file(action, file_path.name)



def _append_txt(content, file_path):
    with open(file_path, mode='a', encoding='utf-8') as file:
        file.write(f'{content}\n')
