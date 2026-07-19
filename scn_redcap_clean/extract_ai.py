from . import config, console, utils

class ConsecutiveFailuresError(Exception):
    ''' Raised to interrupt Pandas .apply() '''
    pass

class ExtractorAI:
    ''' Extracts raw genomic and protein variants using local AI Ollama. '''
    
    def __init__(self, local_ai, class_configs):

        self.local_ai = local_ai
        self.columns = class_configs['cols']
        self.prompt = class_configs['prompt']
        self.schema = class_configs['schema']
        self.process_name = class_configs['name']

        self.ollama_results_col = f'ollama_{self.process_name}_results'
        self.ai_conf_col = 'ollama_confidence'
        self.id_col = config.merge_on_id_column
        self.base_long_cols = [self.id_col, 'from_column', 'raw_text']

    def get_for_review(self, data):
        ''' 
        Outputs csv files for genomic variants review 
        (1 file for record keeping and 1 file for manual override editting)
        Genomic variants are extracted using local AI Ollama
        '''
        self.local_ai.ensure_local_ai()

        final_data = self._get_df(data)

        return final_data

    def _get_df(self, data):
        long_data = self._get_long_df(data)
        preped_data = self._prep_long_form_df(long_data)
        extraction_data = self._extract_df(preped_data)
        if extraction_data is None:
            return None
            
        final_data = self._get_for_review_df(extraction_data)

        return final_data

    def _get_long_df(self, data):
        id_vars = [self.id_col]
        from_col_name = self.base_long_cols[1]
        raw_extract_col = self.base_long_cols[2]
        long_df = data.melt(id_vars, self.columns, from_col_name, raw_extract_col)
        
        return long_df

    def _prep_long_form_df(self, data):
        
        data['raw_text'] = data['raw_text'].astype(str).str.strip()
        is_not_empty = data['raw_text'] != ''
        is_not_nan = data['raw_text'].str.lower() != 'nan'
        active_rows_only = is_not_empty & is_not_nan
        data = data[active_rows_only]
        
        return data

    def _extract_df(self, data):
        ollama_results = self._try_ollama_extraction(data)
        if ollama_results is None:
            return
            
        data[self.ollama_results_col], data[self.ai_conf_col] = zip(*ollama_results)
        
        one_ai_term_per_row_df = self._get_exploded_df(data)
        
        return one_ai_term_per_row_df

    def _try_ollama_extraction(self, data):
        self._init_extraction_tracking()
        try:
            ollama_results = data['raw_text'].apply(self._safe_extract)
            return ollama_results
            
        except ConsecutiveFailuresError:
            console.alert(
                f"Aborted: AI timed out {self.max_consecutive_fails} times in a row.")
            return None

    def _init_extraction_tracking(self):
        print(f"Extracting {self.process_name} text using local '{self.local_ai.model}' and calculating confidence scores...")
        self.consecutive_fails = 0
        self.max_consecutive_fails = 3


    def _safe_extract(self, text):
        extracted_terms, confidence_score, is_timeout = self.local_ai.extract_term(
            self.prompt, text)
        
        is_abort = self._is_abort(is_timeout)
        if is_abort:
            raise ConsecutiveFailuresError() # Breaks .apply() loop
            
        return extracted_terms, confidence_score

    def _is_abort(self, is_timeout):
        if not is_timeout:
            self.consecutive_fails = 0
            return False
        
        else:
            self.consecutive_fails += 1
            is_abort = self.consecutive_fails >= self.max_consecutive_fails
            return is_abort

    def _get_for_review_df(self, extraction_df):
        sorted_df = extraction_df.sort_values(by = self.ai_conf_col, ascending = True)
        sorted_df = utils.add_override_explanation_column(sorted_df, self.id_col)
        
        return sorted_df

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
        