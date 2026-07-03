from . import config  # global configs
from .age import Age 
from .csv_kit import CsvKit



class Standardize:

    def __init__(self, df):

        self.df = df.copy()
        self.id_col = config.merge_on_id_column
        self.csvkit = CsvKit()


    def try_get_age(self, age_units):
        if age_units is not None:
            df = Age().get_age(self.df, units = age_units)
        
        return df