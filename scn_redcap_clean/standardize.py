from . import config  # global configs
from .age import Age 
from .csv_kit import CsvKit



class Standardize:

    def __init__(self, df):

        self.df = df.copy()
        self.id_col = config.merge_on_id_column
        self.csvkit = CsvKit()


    def get_age(self):
        if config.age_units is not None:
            df = Age().get_age(self.df, units = config.age_units)
        
        return df