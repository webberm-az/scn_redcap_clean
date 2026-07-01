import pandas as pd

from . import config


class Age: 
    def __init__(self):
        self.ave_days_in_month = 365 / 12


    def get_age(self, df, units = ['days', 'months', 'years']):
        unit_list = [units] if isinstance(units, str) else units
        for sub_date_col, suffix in config.module_suffix_age.items():
            if sub_date_col not in df.columns:
                continue
            
            df = self._get_age_in_unit_list(df, unit_list, sub_date_col, suffix)
            df = self._cleaned_df(df, unit_list, suffix)
                
        return df



    def get_age_in_days(self, df, sub_date_col, suffix):
        df = self._prepare_dates(df, sub_date_col)
        df[f'age_in_days{suffix}'] = (df[self.end_date] - df[config.birthdate]).dt.days
        
        return df



    def get_age_in_months(self, df, sub_date_col, suffix):
        days_col = f'age_in_days{suffix}'
        if days_col not in df.columns:
            df = self.get_age_in_days(df, sub_date_col, suffix)
            
        df[f'age_in_months{suffix}'] = (df[days_col] / self.ave_days_in_month).round(1)
        
        return df



    def get_age_in_years(self, df, sub_date_col, suffix):
        months_col = f'age_in_months{suffix}'
        if months_col not in df.columns:
            df = self.get_age_in_months(df, sub_date_col, suffix)
            
        df[f'age_in_years{suffix}'] = (df[months_col] / 12).round(2)
        
        return df



    def _cleaned_df(self, df, unit_list, suffix):
        extra_columns_to_drop = self._get_columns_to_drop(unit_list, suffix)
        df = df.drop(columns = extra_columns_to_drop, errors = 'ignore')

        return df



    def _prepare_dates(self, df, sub_date_col):
        df = self._get_end_date(df, sub_date_col)
        df[config.birthdate] = pd.to_datetime(df[config.birthdate]).copy()
        df[sub_date_col] = pd.to_datetime(df[sub_date_col]).copy()

        return df



    def _get_end_date(self, df, sub_date_col):
        self.end_date = 'end_date'
        df[self.end_date] = pd.to_datetime(df[sub_date_col]).copy()
        if config.death_month in df.columns and config.death_year in df.columns:
            
            death_dates = self._cat_est_death_dates(df)
            
            is_deceased = death_dates.notna() & (death_dates < df[sub_date_col])
            
            df.loc[is_deceased, self.end_date] = death_dates[is_deceased]
            
        return df


    def _cat_est_death_dates(self, df):
        death_dates = pd.to_datetime(pd.DataFrame(
            {'year': df[config.death_year], 'month': df[config.death_month], 'day': 15
            }), errors = 'coerce')

        return death_dates
            


    def _get_age_in_unit_list(self, df, unit_list, sub_date_col, suffix):
        if 'years' in unit_list:
                df = self.get_age_in_years(df, sub_date_col, suffix)
            
        elif 'months' in unit_list:
            df = self.get_age_in_months(df, sub_date_col, suffix)
        
        elif 'days' in unit_list:
            df = self.get_age_in_days(df, sub_date_col, suffix)

        return df



    def _get_columns_to_drop(self, unit_list, suffix):
        extra_columns_to_drop = []
        if 'days' not in unit_list:
            extra_columns_to_drop.append(f'age_in_days{suffix}')
        
        if 'months' not in unit_list:
            extra_columns_to_drop.append(f'age_in_months{suffix}')
        
        if 'years' not in unit_list:
            extra_columns_to_drop.append(f'age_in_years{suffix}')
        
        extra_columns_to_drop.append(self.end_date)

        return extra_columns_to_drop
