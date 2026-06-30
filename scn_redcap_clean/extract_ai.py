from . import config
from . import utils


class ExtractorAI:
    ''' Extracts raw genomic and protein variants using local AI Ollama. '''
    
    def __init__(self, schema, delegate):

        self.df = delegate.df.copy()
        self.local_ai = delegate.local_ai
        self.columns = delegate.extractor_cols
        self.prompt = delegate.prompt
        self.schema = schema
        self.process_name = f'{self.schema.__name__.lower()[:-4]}s'

        self.ollama_results_col = f'ollama_{self.process_name}_results'
        self.ai_conf_col = 'ollama_confidence'
        self.id_col = config.merge_on_id_column
        self.base_long_cols = [self.id_col, 'from_column', 'raw_text']



    def get_for_review(self):
        ''' 
        Outputs csv files for genomic variants review 
        (1 file for record keeping and 1 file for manual override editting)
        Genomic variants are extracted using local AI Ollama
        '''
        self.local_ai.ensure_local_ai()

        final_df = self._get_for_review_df()

        return final_df



    def _get_for_review_df(self):
        preped_df = self._prep_long_form_df()
        extraction_df = self._extract_df(preped_df)
        sorted_df = extraction_df.sort_values(by = self.ai_conf_col, ascending = True)
        utils.add_column_if_dne('override_explanation', sorted_df)
        
        return sorted_df



    def _prep_long_form_df(self):
        long_df = self._get_long_df()
        
        long_df['raw_text'] = long_df['raw_text'].astype(str).str.strip()
        is_not_empty = long_df['raw_text'] != ''
        is_not_nan = long_df['raw_text'].str.lower() != 'nan'
        active_rows_only = is_not_empty & is_not_nan
        long_df = long_df[active_rows_only]
        
        return long_df



    def _get_long_df(self):
        id_vars = [self.id_col]
        from_col_name = self.base_long_cols[1]
        raw_extract_col = self.base_long_cols[2]
        long_df = self.df.melt(id_vars, self.columns, from_col_name, raw_extract_col)
        
        return long_df



    def _extract_df(self, df):
        
        print(f"Extracting {self.process_name} text using local '{self.local_ai.model}' and calculating confidence scores...")
        
        ollama_results = df['raw_text'].apply(
            lambda text: self.local_ai.extract_term(self.prompt, text))
        
        df[self.ollama_results_col], df[self.ai_conf_col] = zip(*ollama_results)
        
        one_ai_term_per_row_df = self._get_exploded_df(df)
        
        return one_ai_term_per_row_df



    def _get_exploded_df(self, df):
        ''' Format ollama output for easy manual review '''
        exploded_df = df.explode(self.ollama_results_col)

        self._get_schema_cols()

        for col in self.schema_cols:
            exploded_df[col] = self._get_exploded_col(col, exploded_df)

        final_cols = self.base_long_cols + self.schema_cols + [self.ai_conf_col]
        exploded_df = exploded_df[final_cols]
        
        return exploded_df



    def _get_schema_cols(self):
        list_field = self.schema.model_fields[self.local_ai.json_field_name]
        inner_model = list_field.annotation.__args__[0]
    
        self.schema_cols = list(inner_model.model_fields.keys())



    def _get_exploded_col(self, col, exploded_df):
        exploded_col = exploded_df[self.ollama_results_col].apply(
            lambda item: item.get(col, '') if isinstance(item, dict) else '')

        return exploded_col 