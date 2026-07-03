from .meds import Medications
from .genomics import Genomics

class Clinical:
    ''' Combine Medication and Genomics Overrides into one step '''
    
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
    

    
    def try_input_override_df(self):
        ''' Runs overrides for Meds, passes the updated df to Genomics, and returns the final df. '''
        meds = Medications(self.df)
        self.df = self._safe_input(meds)

        genomics = Genomics(self.df)
        self.df = self._safe_input(genomics)

        return self.df



    def _safe_input(self, instance):
        df = instance.try_input_override_df()
        if df is not None:
            return df
        
        return self.df