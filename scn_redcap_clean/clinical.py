from . import config
from .age import Age 
from .cleaning_step import CleaningStep
from .meds import Medications
from .genomics import Genomics


class Clinical(CleaningStep):
    ''' Combine Medication and Genomics Overrides into one step '''
    
    process_name = 'clinical'

    def __init__(self, df):
        self.df = df.copy()


    def review_dfs(self):
        ''' 
        Generates both review dataframes using the ORIGINAL dataframe.
        Returns them in a dictionary for the Review class to archive.
        '''
        meds_df = Medications(self.df).review_df()
        genomics_df = Genomics(self.df).review_df()

        return meds_df, genomics_df
    

    
    def input_override(self):
        ''' Runs overrides for Meds, passes the updated df to Genomics, and returns the final df. '''
        meds = Medications(self.df)
        self.df = self._safe_input(meds)

        genomics = Genomics(self.df)
        self.df = self._safe_input(genomics)

        self.df = self._safe_get_age()

        return self.df



    def _safe_input(self, instance):
        df = instance.input_override()
        if df is not None:
            return df
        
        return self.df


    
    def _safe_get_age(self):
        if config.age_units is None:
            return self.df

        age = Age()
        self.df = age.insert(self.df, units = config.age_units)
    
        return self.df