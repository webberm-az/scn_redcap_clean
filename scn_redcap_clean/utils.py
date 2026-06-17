from pathlib import Path

import pandas as pd # external import



def is_n_matches(pattern, string, n):
    ''' Returns True if at least n of pattern elements found in string '''
    count = 0

    for _ in pattern.finditer(string):
        count += 1
        if count >= n:
            return True

    return False



def get_cols_if_in_df(df, override_df, id_col):
    ''' Returns shared columns between df and override_df excluding id_col '''
    shared_cols = set(df.columns) & set(override_df.columns)
    clean_shared_cols = [col for col in shared_cols if col != id_col]
    
    return clean_shared_cols



def if_missing_drop_row(df, filter_subset):
    ''' Removes rows where col is blank or missing '''
    subset = [filter_subset] if isinstance(filter_subset, str) else list(filter_subset)

    df[subset] = df[subset].replace('', pd.NA) # set empty to NA
    df = df.dropna(subset = subset, how = 'all') # drop all NA

    return df
    


def write_txt_file(content: str, filename: str, output_dir: Path):
    '''
    Safely writes a string content to a txt within an output directory.
    '''        
    file_path = get_txt_filepath(filename, output_dir)
    create_txt(content, filename, file_path)



def create_txt(content, filename, file_path):
    # Path.write_text automatically opens, writes, and closes the file safely.
    file_path.write_text(content, encoding='utf-8')
    print(f'| Info | {filename} txt file saved to: {file_path}')



def get_txt_filepath(filename, output_dir):
    filename = add_txt_suffix(filename)
    file_path = output_dir / filename

    return file_path



def add_txt_suffix(filename):
    if not filename.endswith('.txt'):
        filename = f'{filename}.txt'
    
    return filename



def append_to_txt(content: str, filename: str, output_dir: Path):
    '''
    Appends text to a file without overwriting existing content.
    Creates the file if it doesn't exist.
    '''        
    file_path = get_txt_filepath(filename, output_dir)
    _append_txt(content, file_path)
    print(f'Text entry added text to: {file_path.name}')



def _append_txt(content, file_path):
    with open(file_path, mode='a', encoding='utf-8') as file:
        file.write(f'{content}\n')



def view_txt_file(filename: str, output_dir: Path):
    '''
    Reads a text file and prints its entire contents to the console.
    '''
    file_path = get_txt_filepath(filename, output_dir)
    alert_filepath_DNE(file_path)
    # Read and print contents
    print(f'\n   |  {filename}  |')
    print(file_path.read_text(encoding='utf-8'))
    print('` ` ` ` ` ` ` ` ` ` ` ` ` ` ` ` ` ` ` `\n')



def alert_filepath_DNE(file_path):
    if not file_path.exists():
        print(f"| Error | '{file_path}' does not exist.")
        return



def add_column_if_dne(colname, df, input = ''):
    if colname not in df.columns:
        df[colname] = input
    
    return df



def match_rows_to_ref_id(df, ref_df, id_column):
    df[id_column] = df[id_column].astype(ref_df[id_column].dtype)
        
    return df[id_column]




def is_df_identical(current_df, last_df):
    if last_df.astype(str).equals(current_df.astype(str)):
        return True

    return False



