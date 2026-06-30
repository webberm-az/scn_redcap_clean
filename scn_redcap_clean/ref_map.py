import pandas as pd


class RefMap:

    def __init__(self, dict_df, main = 'Generic Name', alias = 'Alias', abbr = 'Abbr.'):
        self.dict_df = dict_df
        self.main = main
        self.alias = alias
        self.abbr = abbr
        self._included_terms = set()
        self._alias_to_main = {}
        
        if self.dict_df is not None:
            self._make_maps()


    def is_missing(self, term_series: pd.Series) -> pd.Series:
        '''Compares a series of terms and returns a boolean series (True if missing).'''
        clean_terms = term_series.astype(str).str.lower().str.strip()
        is_missing = ~clean_terms.isin(self._included_terms)
        
        return is_missing



    def get_main_names(self, term_series: pd.Series) -> pd.Series:
        clean_terms = term_series.astype(str).str.lower().str.strip()
        main_names = clean_terms.map(self._alias_to_main).fillna(clean_terms)
        
        return main_names



    def _make_maps(self):
        if self.dict_df is None or self.dict_df.empty:
            return

        clean_df = self.dict_df.dropna(subset=[self.main]).copy()
        for _, row in clean_df.iterrows():
            main = str(row[self.main]).strip()
            self._register_term(main, main)
            self._register_abbr_term(row.get(self.abbr), main)
            self._register_comma_separated_aliases(row.get(self.alias), main)



    def _register_term(self, term: str, main_match: str):
        clean_term = term.lower().strip()
        if clean_term:
            self._included_terms.add(clean_term)
            self._alias_to_main[clean_term] = main_match



    def _register_abbr_term(self, raw_abbr, main_match):
        if pd.notna(raw_abbr):
            self._register_term(str(raw_abbr), main_match)



    def _register_comma_separated_aliases(self, raw_aliases, main_match):
        if pd.notna(raw_aliases):
            for alias in str(raw_aliases).split(','):
                self._register_term(alias, main_match)