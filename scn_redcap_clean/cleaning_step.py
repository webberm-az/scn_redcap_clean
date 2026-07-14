from abc import ABC, abstractmethod
import pandas as pd

class CleaningStep(ABC):
    def __init__(self, df: pd.DataFrame):
        self.df = df

    @abstractmethod
    def create_final_data(self) -> pd.DataFrame:
        pass