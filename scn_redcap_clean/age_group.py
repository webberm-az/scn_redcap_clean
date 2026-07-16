import pandas as pd
from . import config, console
from .units import Unit

class AgeGroup:
    def __init__(self, df):
        self.df = df.copy()

    def bin_age_column(self, age_column: str, unit: Unit):
        '''Bins a numeric column into discrete categories using the config dictionary'''
        if age_column not in self.df.columns:
            console.error_missing({age_column}, 'not found')
            return self.df

        bins, labels = self._unpack_config_age_group_dict(unit)
        if not bins or not labels:
            console.error(f"'config.age_groups' for {unit.name} not found")
            return self.df
            
        if not len(labels) == (len(bins) - 1):
            console.error(f"'config.age_groups' {unit.name} bin-label mismatch.")
            return self.df

        self.add_age_group_column(age_column, bins, labels)

        return self.df

    def _unpack_config_age_group_dict(self, unit):
        groups = config.age_groups.get(unit, [])
        
        # Prepend 0 (age always starts at 0)
        bins = [0.0] + [float(g[0]) for g in groups]
        labels = [g[1] for g in groups]

        return bins, labels

    def add_age_group_column(self, age_column, bins, labels):
        output_column = f'{age_column}_groups'
        self.df[output_column] = pd.cut(
            self.df[age_column], bins = bins, labels = labels, include_lowest = True)
