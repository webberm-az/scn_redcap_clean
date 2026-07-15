from .csv_kit import CsvKit
from . import config, console, paths, utils # global configs


class OverrideAppend:
    
    def __init__(self, process_name):

        self.process_name = process_name

        self.override_csv_name = utils.get_manual_cvsname(self.process_name)
        self.id_col = config.merge_on_id_column
        self.csvkit = CsvKit()
        self.override_csv_path = self.csvkit.path( # need
            self.override_csv_name, paths.OVERRIDES)


    def append_override_df(self, df): # for Translations
        ''' If override_csv_name exists in overrides folder inputs translations '''
        if df is None or self.override_csv_path is None:
            self._print_missing_override()
        else:
            df = self.append_override_rows(df)
        
        return df



    def _print_missing_override(self):
        process = self.process_name
        console.missing_override(
                self.override_csv_name, f'{process} input', f'without {process}s')



    def append_override_rows(self, df):
        ''' Adds all rows in override_csv to df '''
        override_df = self._prep_override_df(df)
        df = df.set_index(self.id_col)
        temp_override = override_df.set_index(self.id_col)
        shared_cols = utils.get_column_headers_if_in_df(df, override_df, self.id_col)
        df.update(temp_override[shared_cols])
        df = df.reset_index()
        
        return df



    def _prep_override_df(self, df):
        ''' Prepares the override dataframe by reading the CSV and filtering rows '''
        o_df = self._dropna_id_col()
        # ensure df and override_df 'id_col's are the same type for comparison
        o_df[self.id_col] = o_df[self.id_col].astype(df[self.id_col].dtype)

        return o_df
    


    def _dropna_id_col(self):
        if self.override_csv_path is not None:
            override_df = CsvKit().robust_read(self.override_csv_path)
            # drop rows w/ NA id_col in override file for efficiency
            override_df = override_df.dropna(subset = [self.id_col])

        return override_df
