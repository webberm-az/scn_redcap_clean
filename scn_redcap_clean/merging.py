# local imports
from . import utils
from . import config # global configs
from .csv_kit import CsvKit


class Merging:

    def __init__(self):
        self.id_col = config.merge_on_id_column
        self.csvkit = CsvKit()


    def get_merged_module_df(self, csv_list, text_columns = None, merge_on_file = None):
        '''
        Merges a list of CSVs on 'participant_id' and removes 
        rows where 'birthdate' is blank or missing
        '''
        self.active_text_cols = text_columns if text_columns is not None else []
        merged_df = self.merge_csvs(csv_list, merge_on_file)

        existing_filter_columns = self.get_existing_filter_columns(merged_df)

        if existing_filter_columns: 
            merged_df = utils.if_missing_drop_row(merged_df, existing_filter_columns)
        else: 
            console.error_missing(config.filter_columns, 'column(s) must be in at least 1 csv file.')
            
        return merged_df



    def get_existing_filter_columns(self, merged_df):
        filter_cols = self.get_filter_columns()
        existing_filters = self.get_existing_columns(merged_df, filter_cols)  
        
        return existing_filters



    def get_filter_columns(self):
        if isinstance(config.filter_columns, str):
            filter_cols = [config.filter_columns] 
        else:
            filter_cols = config.filter_columns

        return filter_cols



    def get_existing_columns(self, merged_df, filter_cols):
        existing_filters = [col for col in filter_cols if col in merged_df.columns]

        return existing_filters



    def merge_csvs(self, csv_list, merge_on_file = None):
        ''' Merges a list of CSVs on 'participant_id' '''
        # initialize main df w/ merge_on_file to merge on id_col ensuring consistent id_col type
        merge_on_file = self._set_merge_on_file(csv_list, merge_on_file)
        merge_on_file_df = self._get_merge_on_file_df(merge_on_file)
        # left merges all files based on id_col in merge_on_file
        merged_df = self._get_combined_df(csv_list, merge_on_file, merge_on_file_df)
                
        return merged_df



    def _get_merge_on_file_df(self, merge_on_file):
        merge_on_file_clean = self.csvkit.add_suffix(merge_on_file)
        merge_on_file_df = self.csvkit.get_df_dropna_subset(config.raw_data_dir, merge_on_file_clean, self.id_col)

        return merge_on_file_df



    def _get_combined_df(self, csv_list, merge_on_file, merged_df):
        ''' Initializes combined_data df with merge_on_file ensuring consistent id_col type '''        
        for csv in csv_list: 
            csv_clean = self.csvkit.add_suffix(csv)
            merged_df = self._safe_merge(csv_clean, merge_on_file, merged_df)
        
        return merged_df
    


    def _safe_merge(self, csv_name, merge_on_file, merged_df):
        ''' Merges a list of CSVs on 'participant_id' '''
        if csv_name != merge_on_file:
            merged_df = self._merge(csv_name, merged_df)
        
        return merged_df



    def _set_merge_on_file(self, csv_list, merge_on_file):
        ''' Sets merge_on_file to first file in list if merge_on_file = None '''
        if not csv_list: 
            raise ValueError('csv files list is empty')
        
        if merge_on_file is None:
            merge_on_file = csv_list[0] # default to first file in list if not specified
        
        merge_on_file_clean = str(self.csvkit.add_suffix(merge_on_file))
        
        return merge_on_file_clean
                    


    def _merge(self, csv_name, merged_df):
        ''' Merges df with csv on id_col and returns merged df '''
        merging_df = self.csvkit.get_df_dropna_subset(config.raw_data_dir, csv_name, self.id_col)
        merged_df = self.merge_dropping_shared_cols(merged_df, merging_df, csv_name)

        return merged_df



    def merge_dropping_shared_cols(self, base_df, merging_df, csv_name):
        ''' Returns df with shared columns between df and override_df dropped excluding id_col '''
        merging_df = self._drop_duplicate_cols(base_df, merging_df)
        merging_df = self.get_shared_colname_not_duplicate(base_df, merging_df, csv_name)
        base_df = base_df.merge(merging_df, on = self.id_col, how = 'left')

        return base_df



    def get_shared_colname_not_duplicate(self, base_df, merging_df, csv_name):
        remaining_shared_cols = utils.get_cols_if_in_df(base_df, merging_df, self.id_col)
        
        if remaining_shared_cols:
            self.rename_dict = {}
            self.get_rename_dict(remaining_shared_cols, csv_name)
            merging_df = merging_df.rename(columns = self.rename_dict)
        
        return merging_df
        


    def get_rename_dict(self, remaining_shared_cols, csv_name):
        self.rename_dict = {}
        for col in remaining_shared_cols:
            self._get_new_col_name(col, csv_name)



    def _get_new_col_name(self, col, csv_name):
        new_col_name = self._suffix_col_name_with_csv_name(col, csv_name)
        self._add_to_rename_dict_and_alert(col, new_col_name)
        
        self._if_active_text_col_add_new(col, new_col_name) # for translation tracking

        return new_col_name



    def _suffix_col_name_with_csv_name(self, col, csv_name):
        csv_str = str(csv_name)
        clean_suffix = csv_str.replace('.csv', '').replace(' ', '_').replace('.', '_')
        new_col_name = f'{col}_{clean_suffix}'

        return new_col_name



    def _add_to_rename_dict_and_alert(self, col, new_col_name):
        self.rename_dict[col] = new_col_name
        print(f"Matching Column names with different contents found for '{col}'.")
        print(f"Keeping 1st instance as '{col}' and matching instance as '{new_col_name}'.\n")



    def _if_active_text_col_add_new(self, col, new_col_name):
        if hasattr(self, 'active_text_cols') and col in self.active_text_cols:
            self._if_not_in_active_append(new_col_name)



    def _if_not_in_active_append(self, new_col_name):
        if new_col_name not in self.active_text_cols:
            self.active_text_cols.append(new_col_name)  



    def _drop_duplicate_cols(self, base_df, merging_df):
        ''' Returns df with shared columns between df and override_df dropped excluding id_col '''
        self.cols_to_drop = []
        self._get_cols_to_drop(base_df, merging_df)
        merging_df = merging_df.drop(columns = self.cols_to_drop)

        return merging_df


    
    def _get_cols_to_drop(self, base_df, merging_df):
        shared_colnames = utils.get_cols_if_in_df(base_df, merging_df, self.id_col)
        self._from_shared_get_cols_to_drop(base_df, merging_df, shared_colnames)



    def _from_shared_get_cols_to_drop(self, base_df, merging_df, shared_colnames):
        base_aligned = base_df.set_index(self.id_col)
        merging_aligned = merging_df.set_index(self.id_col)
        common_ids = base_aligned.index.intersection(merging_aligned.index)
        self._get_col_to_drop(shared_colnames, base_aligned, merging_aligned, common_ids)



    def _get_col_to_drop(self, shared_colnames, base_aligned, merging_aligned, common_ids):
        for col in shared_colnames:
            # force matching type for comparison
            base_vals_as_str = self._get_base_vals_as_str(base_aligned, common_ids, col)
            merging_vals_as_str = self._get_merging_vals_as_str(merging_aligned, common_ids, col)
            self._get_exact_duplicates(base_vals_as_str, merging_vals_as_str, col)



    def _get_base_vals_as_str(self, base_aligned, common_ids, col):
        base_vals = base_aligned.loc[common_ids, col]
        base_vals_as_str = base_vals.astype(str)

        return base_vals_as_str



    def _get_merging_vals_as_str(self, merging_aligned, common_ids, col):
        merging_vals = merging_aligned.loc[common_ids, col]
        merging_vals_as_str = merging_vals.astype(str)

        return merging_vals_as_str



    def _get_exact_duplicates(self, base_vals, merging_vals, col):
        # .equals() checks both shape and elements
        if base_vals.equals(merging_vals):
            self.cols_to_drop.append(col)
        
