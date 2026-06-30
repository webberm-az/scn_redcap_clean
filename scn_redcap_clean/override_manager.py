from .csv_kit import CsvKit
from . import config, console, utils # global configs


class OverrideManager:
    
    def __init__(self, step_number, delegate):
        self.step_number = step_number
        self.delegate = delegate
        self.paths = delegate.paths
        self.df = delegate.df.copy()
        self.process_name = delegate.__class__.__name__.lower()
        self.override_csv_name = f'{self.process_name}_manual_override'
        self.id_col = config.merge_on_id_column
        self.csvkit = CsvKit()
        self.override_csv_path = self.csvkit.if_exists_path(
            self.override_csv_name, self.paths.overrides)


    def try_input_mapped_long_df(self, map_df): # for Medications and Genomics
        ''' 
        If override_csv_name exists in overrides folder:
        Maps terms using map_df and inputs into main csv
        '''
        self.map_df = map_df
        if self.df is None or self.override_csv_path is None or self.map_df is None:
            self._alert_errors()
            return None

        override_df = self.csvkit.robust_read_csv(self.override_csv_path) 
        df = self._get_final_df(override_df)
        
        return df



    def try_append_override_df(self): # for Translations
        ''' If override_csv_name exists in overrides folder inputs translations '''
        df = self.df
        print(self.override_csv_path )
        if df is None or self.override_csv_path is None:
            self._print_missing_override()
        else:
            df = self.append_override_rows()
        
        return df



    def _print_missing_override(self):
        process = self.process_name
        console.missing_override(
                self.override_csv_name, f'{process} input', f'without {process}s')



    def append_override_rows(self):
        ''' Adds all rows in override_csv to df '''
        override_df = self._prep_override_df()
        self.df = self.df.set_index(self.id_col)
        temp_override = override_df.set_index(self.id_col)
        shared_cols = utils.get_cols_if_in_df(self.df, override_df, self.id_col)
        self.df.update(temp_override[shared_cols])
        self.df = self.df.reset_index()
        
        return self.df



    def _prep_override_df(self):
        ''' Prepares the override dataframe by reading the CSV and filtering rows '''
        o_df = self._dropna_id_col()
        # ensure df and override_df 'id_col's are the same type for comparison
        o_df[self.id_col] = o_df[self.id_col].astype(self.df[self.id_col].dtype)

        return o_df
    


    def _dropna_id_col(self):
        if self.override_csv_path is not None:
            override_df = CsvKit().robust_read_csv(self.override_csv_path)
            # drop rows w/ NA id_col in override file for efficiency
            override_df = override_df.dropna(subset = [self.id_col])

        return override_df



    def _alert_errors(self):
        if self.df is None:
            last_step = utils.get_step_config(self.step_number - 1)
            console.error_missing(last_step, "not in 'steps' folder")
        
        if self.override_csv_path is None:
            console.info_missing_file({self.override_csv_path}, 'overrides')
        
        if self.map_df is None:
            self._print_missing_override_dict()



    def _print_missing_override_dict(self):
        process = self.process_name
        message = f"without the {process}s map in 'ref' folder"
        console.missing_override(self.map_df, f'{process} input', message)



    def _get_final_df(self, override_df):
        mapped_long_df = self.delegate.try_get_mapped_long_df(override_df)
        if mapped_long_df.empty:
            return self.df

        final_df = self.delegate.try_get_merged_final_df(self.df, mapped_long_df)

        return final_df
