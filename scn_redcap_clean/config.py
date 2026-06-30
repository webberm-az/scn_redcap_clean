from . import utils

'''    ____________________________  Required  __________________________________    '''

# Data Dictionary CSV
data_dict = 'ToyDict.csv'


# Module Specific
modules = ['toy',] # as listed in the Data Dictionary 'Form Name' column


raw_module_csv = 'Toy1' # must have all of columns of the module(s) you are filtering by


module_suffix_age = {
    'submission_date' : '_toy',
    'submission_date_2': '_mod2' # if more than 1 module is timestamped
}


c_genomic = 'genomic_text1'
p_genomic = 'genomic_p._text2'


med_text_cols = ['toy_meds', 'toy_supps']


meds_dict = 'Toy_clinical_taxonomy.csv'


age_dependent = ['toy_check1', 'toy_check2', 'toy_check3', 'toy_check4', 'toy_yesno']





'''    ____________________________  Defaults  __________________________________    '''

raw_data_dir = 'raw'  # default raw data folder name

merge_on_id_column = 'participant_id'

filter_columns = 'birthdate' # summary notes assume this is just birthdate

# for age on Module submission date
birthdate = 'birthdate'

no_translate_cols = [c_genomic, p_genomic, birthdate, merge_on_id_column]


# Steps CSV Names
name_01_main = '01_merged_raw'
name_02_main = '02_translated'
name_03_main = '03_removed_duplicates'
name_04_main = '04_medications'
name_05_main = '05_genomics_and_standardized'




# __Merging___________________________
language_text_columns = utils.auto
drop_na_col = True

# Data Dictionary
module_column = 'Form Name'
field_type_column = 'Field Type'
col_names_column = 'Variable / Field Name'




# __Translation_______________________
translation_script_threshold = 3

# inputs for special terms
# foreign lanugage must be the key and the translation (or medical term) the value
translation_dict = {
    '布洛芬':'Ibuprofen',
    } 




#  __Genomics_________________________
# for UniProt Ref Map
gene_name = 'SCN8A'

# Schema Columns 
protein_aa_orig_1 = 'aa_orig_1'
protein_pos = 'pos_num'
protein_aa_repl_1 = 'aa_replace_1'
protein_region = 'region'
cdna_variant = 'c._variant'

protein_aa_orig_3 = 'aa_orig_3'
protein_aa_repl_3 = 'aa_replace_3'

protein_variant_1 = 'p._variant_aa1'
protein_variant_3 = 'p._variant_aa3'

protein_split_cols = [protein_aa_orig_1, protein_pos, protein_aa_repl_1, protein_region]
genomics_split_cols = protein_split_cols + [cdna_variant]
all_generated_genomics_cols = genomics_split_cols + [
    protein_aa_orig_3, protein_aa_repl_3, protein_variant_1, protein_variant_3]

# AI Prompts
prompt_genomics = (
    'You are an expert biocurator processing messy clinical records to extract gene ' 'mutations. Identify and extract two distinct types of variants:\n'
    "1. cDNA variants (Coding DNA): Typically prefixed with 'c.' or containing " "nucleotide changes like '+', '>', 'del', or 'ins' (e.g., 'c.2345+1T>G', " "'1333G>A').\n"
    "2. Protein variants (Amino Acid): Typically prefixed with 'p.' or containing " "amino acid letters and positions (e.g., 'p.E1483K', 'N984K', 'Glu1483Lys').\n\n"
    'CRITICAL: Do not copy the raw clinical text exactly. Your job is to standardize ' 'the format into clean HGVS notation following the explicit instructions and ' 'examples provided in the JSON schema fields (e.g., stripping spaces, adding ' 'prefixes, and dropping outer parentheticals). If no genetic variation is present ' 'in the text, return an empty list.'
    'CRITICAL RULES:\n'
    '1. DO NOT add transcript accession numbers (e.g., NM_..., NG_...). Output ONLY ' 'the variant itself.\n'
    '2. DO NOT change the numbers or positions provided in the raw text. If the text ' "says 3333, output 3333. Never swap a position with a known 'famous' mutation. \n"
    "3. If the input is a valid cDNA variant, keep the 'c.' prefix. If it is protein, " "keep the 'p.' prefix.\n"
    '4. Your only task is to fix the formatting (spaces, parentheticals, case), NOT to' ' validate the mutation biology.')

prompt_meds = (
    'Analyze this text and extract all medications and supplements. '
    'Translate any foreign language terms into direct English equivalents. '
    'Return the basic English term without attempting to standardize to highly '
    "specific chemical variants (e.g., translate 'Vitamina B12' to 'Vitamin B12', NOT " "'Cyanocobalamin'; translate '卡马西平片' to 'Carbamazepine'). "
    'Do not guess or add chemical precision that is not explicitly present in the ' 'original text.')