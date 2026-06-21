from .local_ai import LocalAI
from . import config
from . import utils


class Medications:
    ''' Standardizes medications and supplements using local AI Ollama. '''
    
    def __init__(self, df, paths, archiver):

        self.df = df.copy()
        self.paths = paths
        self.archiver = archiver
        self.local_ai = LocalAI()
        self.ollama_meds_col = 'ollama_meds'
        self.ai_confidence_col = 'ollama_confidence'
        self.id_col = config.merge_on_id_column
        self.base_long_cols = [self.id_col, 'from_column', 'raw_text']


    def create_medications_for_review(
            self, 
            main_filename = 'medications_manual_override', 
            archive_filename = 'medications_for_review'):
        ''' 
        Outputs csv files for medications review 
        (1 file for record keeping and 1 file for manual override editting)
        Medications and supplements are standardized using local AI Ollama
        '''
        self.local_ai.ensure_local_ai()
        final_meds_df = self._get_meds_for_review_df()
        filename_get_version = config.name_03_main

        # outputs csvs to review folder, a version to archive, and txt to overrides
        self.archiver.create_files_review_and_archive(
            final_meds_df, main_filename, archive_filename, filename_get_version)

        return final_meds_df



    def _get_meds_for_review_df(self):
        preped_df = self._prep_long_form_df()
        meds_df = self._extract_meds_df(preped_df)
        sorted_df = meds_df.sort_values(by = self.ai_confidence_col, ascending = True)
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
        value_vars = config.med_text_cols
        var_name = self.base_long_cols[1]
        value_name = self.base_long_cols[2]
        long_df = self.df.melt(id_vars, value_vars, var_name, value_name)
        
        return long_df



    def _extract_meds_df(self, df):

        print(f"Extracting medications and supplements using local '{self.local_ai.model}' and calculating confidence scores...")
        
        prompt = 'Analyze this medication and supplements text. Extract all medications and supplements. Normalize to English generic names.'
        
        # Simple extraction execution via client object link
        meds_results = df['raw_text'].apply(
            lambda text: self.local_ai.analyze_text(prompt, text))
        
        df[self.ollama_meds_col], df[self.ai_confidence_col] = zip(*meds_results)

        df[self.ai_confidence_col] = [score for _, score in meds_results]
        one_ai_term_per_row_df = self._get_exploded_df(df)
        
        return one_ai_term_per_row_df



    def _get_exploded_df(self, df):
        ''' Format ollama output for easy manual review '''
        exploded_df = df.explode(self.ollama_meds_col)
        
        explode_cols = ['original_term', 'standardized_name', 'category']

        for col in explode_cols:
            exploded_df[col] = self._get_exploded_col(col, exploded_df)

        final_cols = self.base_long_cols + explode_cols + [self.ai_confidence_col]
        
        exploded_df = exploded_df[final_cols]
        
        return exploded_df



    def _get_exploded_col(self, col, exploded_df):
        exploded_col = exploded_df[self.ollama_meds_col].apply(
                lambda x: x.get(col, '') if isinstance(x, dict) else '')
        
        return exploded_col       
