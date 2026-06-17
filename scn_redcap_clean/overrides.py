import pandas as pd

from . import utils
from . import config # global configs


class Overrides:
    
    def __init__(self, override_csv_path, df):
        self.df = df.copy()
        self.id_col = config.merge_on_id_column
        self.override_csv_path = override_csv_path
        self.override_df = self._prep_override_df()
        self.shared_cols = utils.get_cols_if_in_df(self.df, self.override_df, self.id_col)



    def override(self):
        '''
        Returns merged_raw with translations replacing of foreign text
        '''
        self.append_override_rows()

        return self.df



    def append_override_rows(self):
        ''' Adds all rows in override_csv to df '''
        self.df = self.df.set_index(self.id_col)
        temp_override = self.override_df.set_index(self.id_col)
        self.df.update(temp_override[self.shared_cols])
        self.df = self.df.reset_index()



    def _prep_override_df(self):
        ''' Prepares the override dataframe by reading the CSV and filtering rows '''
        override_df = self._dropna_id_col()
        # ensure df and override_df 'id_col's are the same type for comparison
        override_df[self.id_col] = override_df[self.id_col].astype(self.df[self.id_col].dtype)

        return override_df
    


    def _dropna_id_col(self):
        override_df = pd.read_csv(self.override_csv_path)
        # drop rows w/ NA id_col in override file for efficiency
        override_df = override_df.dropna(subset = [self.id_col])

        return override_df
