from abc import ABC, abstractmethod
import pandas as pd

class CleaningStep(ABC):
    def __init__(self, df: pd.DataFrame):
        self.df = df

    @abstractmethod
    def input_override(self) -> pd.DataFrame:
        pass