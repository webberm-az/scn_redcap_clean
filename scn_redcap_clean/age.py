import pandas as pd

from . import config


class Age: 
    def __init__(self):
        self.average_days_in_month = 365 / 12


    def get_age(self, df, units = ['days', 'months', 'years']):

        unit_list = [units]
        for sub_date_col, suffix in config.module_suffix_age.items():
            if sub_date_col not in df.columns:
                continue
            
            if 'years' in unit_list:
                df = self.get_age_in_years(df, sub_date_col, suffix)
            
            elif 'months' in unit_list:
                df = self.get_age_in_months(df, sub_date_col, suffix)
            
            elif 'days' in unit_list:
                df = self.get_age_in_days(df, sub_date_col, suffix)

            extra_columns_to_drop = []
            if 'days' not in unit_list:
                extra_columns_to_drop.append(f'age_in_days{suffix}')
            
            if 'months' not in unit_list:
                extra_columns_to_drop.append(f'age_in_months{suffix}')
            
            if 'years' not in unit_list:
                extra_columns_to_drop.append(f'age_in_years{suffix}')

            df = df.drop(columns = extra_columns_to_drop, errors = 'ignore')
                
        return df



    def get_age_in_days(self, df, sub_date_col, suffix):
        df = self._prepare_dates(df, sub_date_col)
        df[f'age_in_days{suffix}'] = (df[sub_date_col] - df[config.birthdate]).dt.days
        
        return df



    def get_age_in_months(self, df, sub_date_col, suffix):
        days_col = f'age_in_days{suffix}'
        if days_col not in df.columns:
            df = self.get_age_in_days(df, sub_date_col, suffix)
            
        df[f'age_in_months{suffix}'] = (df[days_col] / self.average_days_in_month).round(1)
        
        return df



    def get_age_in_years(self, df, sub_date_col, suffix):
        months_col = f'age_in_months{suffix}'
        if months_col not in df.columns:
            df = self.get_age_in_months(df, sub_date_col, suffix)
            
        df[f'age_in_years{suffix}'] = (df[months_col] / 12).round(2)
        
        return df



    def _prepare_dates(self, df, sub_date_col):
        df[config.birthdate] = pd.to_datetime(df[config.birthdate]).copy()
        df[sub_date_col] = pd.to_datetime(df[sub_date_col]).copy()
        
        return df
