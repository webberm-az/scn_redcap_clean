raw_data_dir = 'raw'  # default raw data folder name

merge_on_id_column = 'participant_id'

filter_columns = 'birthdate' # summary notes assume this is just birthdate


translation_script_threshold = 3

# inputs for special terms
# foreign lanugage must be the key and the translation (or medical term) the value
translation_dict = {
    '布洛芬':'Ibuprofen',
    } 



name_01_main = '01_merged_raw'
name_02_main = '02_translated'
name_03_main = '03_removed_duplicates'



# Data Dictionary
data_dict = 'ToyDict.csv'
module_column = 'Form Name'
field_type_column = 'Field Type'
col_names_column = 'Variable / Field Name'

# Module Specific
modules = ['toy',] # as listed in the Data Dictionary 'Form Name' column

raw_module_file = 'Toy1' # must have all of the module(s) you are filtering by
