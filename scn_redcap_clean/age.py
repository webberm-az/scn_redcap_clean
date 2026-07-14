import pandas as pd

from . import config
from .units import Unit
from .age_group import AgeGroup


class Age: 
    def __init__(self):
        self.ave_days_in_month = 365 / 12
        self.end_date = 'end_date'
        self.include_age_groups = config.include_age_groups


    def insert(self, data, units = [Unit.days, Unit.months, Unit.years]):
        data = data.copy()

        self.unit_list = [units] if isinstance(units, Unit) else units
        for sub_date_col, suffix in config.module_suffix_age.items():
            if sub_date_col not in data.columns:
                continue
            
            data = self._get_age_in_unit_list(data, sub_date_col, suffix)
            data = self._cleaned_df(data, suffix)
            if self.include_age_groups:
                data = self._insert_age_groups(data, suffix)

        self.data = data
                
        return self.data



    def _insert_in_days(self, data, sub_date_col, suffix):
        data = self._prepare_dates(data, sub_date_col)
        days_col = self._get_column_name(Unit.days, suffix)
        data[days_col] = (data[self.end_date] - data[config.birthdate]).dt.days
        
        return data



    def _insert_in_months(self, data, sub_date_col, suffix):
        days_col = self._get_column_name(Unit.days, suffix)
        if days_col not in data.columns:
            data = self._insert_in_days(data, sub_date_col, suffix)

        months_col = self._get_column_name(Unit.months, suffix)
        data[months_col] = (data[days_col] / self.ave_days_in_month).round(1)
        
        return data



    def _insert_in_years(self, df, sub_date_col, suffix):
        months_col = self._get_column_name(Unit.months, suffix)
        if months_col not in df.columns:
            df = self._insert_in_months(df, sub_date_col, suffix)

        years_col = self._get_column_name(Unit.years, suffix)
        df[years_col] = (df[months_col] / 12).round(2)
        
        return df



    def _cleaned_df(self, df, suffix):
        extra_columns_to_drop = self._get_columns_to_drop(suffix)
        df = df.drop(columns = extra_columns_to_drop, errors = 'ignore')

        return df



    def _insert_age_groups(self, df, suffix):
        age_group = AgeGroup(df)
        for unit in self.unit_list:
            self._add_age_group_col(df, unit, suffix, age_group)

        return age_group.df



    def _add_age_group_col(self, df, unit, suffix, age_group):
        age_column = self._get_column_name(unit, suffix)
        
        if age_column in df.columns:
            age_group.df = age_group.bin_age_column(age_column, unit = unit)
        
        return



    def _prepare_dates(self, df, sub_date_col):
        df = self._get_end_date(df, sub_date_col)
        df[config.birthdate] = pd.to_datetime(df[config.birthdate]).copy()
        df[sub_date_col] = pd.to_datetime(df[sub_date_col]).copy()

        return df



    def _get_column_name(self, unit, suffix):
        column_name = f'age_in_{unit.name}_{suffix}'

        return column_name



    def _get_end_date(self, df, sub_date_col):
        df[self.end_date] = pd.to_datetime(df[sub_date_col]).copy()
        if config.death_month in df.columns and config.death_year in df.columns:
            
            death_dates = self._cat_est_death_dates(df)
            
            is_deceased = death_dates.notna() & (death_dates < df[sub_date_col])
            
            df.loc[is_deceased, self.end_date] = death_dates[is_deceased]
            
        return df



    def _cat_est_death_dates(self, df):
        death_dates = pd.to_datetime(pd.DataFrame(
            {'year': df[config.death_year], 
            'month': df[config.death_month], 
            'day': 15 }), errors = 'coerce')

        return death_dates
            


    def _get_age_in_unit_list(self, df, sub_date_col, suffix):
        if Unit.years in self.unit_list:
                df = self._insert_in_years(df, sub_date_col, suffix)
            
        elif Unit.months in self.unit_list:
            df = self._insert_in_months(df, sub_date_col, suffix)
        
        elif Unit.days in self.unit_list:
            df = self._insert_in_days(df, sub_date_col, suffix)

        return df


    
    def _get_columns_to_drop(self, suffix):
        columns = [self.end_date]
        columns_list = self._get_extra_unit_columns(suffix)
        columns.extend(columns_list)
        
        return columns



    def _get_extra_unit_columns(self, suffix):
        columns = []
        for unit in Unit:
            column_name_list = self._get_extra_column(unit, suffix)
            columns.extend(column_name_list)
            
        return columns



    def _get_extra_column(self, unit, suffix):
        if unit not in self.unit_list:
            column_name = self._get_column_name(unit, suffix)
            return [column_name]
            
        return []
