import pandas as pd

from .cleaning_step import CleaningStep
from .csv_writer import CsvWriter
from .csv_kit import CsvKit
from .extract_ai import ExtractorAI
from .local_ai import LocalAI
from .schemas import GenomicList
from .uniprot import UniProtQuery
from . import bio, config, console, paths, utils


class Genomics(CleaningStep):
    ''' Extracts raw genomic and protein variants using local AI Ollama. '''
    

    def __init__(self, df):

        self.df = df.copy()
        self.archiver = CsvWriter()
        self.id_col = config.merge_on_id_column
        self.csvkit = CsvKit()
        self.genomics_dict_df = self.csvkit.path_to_df(
            f'{config.gene_name}_position_map_uniprot', paths.REF)
        self.r_term = 'recommended_term'
        self.term = 'clean_term'

    @classmethod
    def get_process_name(cls):
        process_name = 'genomics'

        return process_name


    def review_df(self):
        ''' 
        Outputs csv files for genomic variants review 
        (1 file for record keeping and 1 file for manual override editting)
        Genomic variants are extracted using local AI Ollama
        '''
        self._try_create_gene_position_refs()
        df = self._get_genomics_for_review()

        return df



    def create_final_data(self):
        '''  Maps genomic variants to UniProt position map and inputs into main csv '''
        override_filename = utils.get_manual_cvsname(self.get_process_name())
        self.override_csv_path = self.csvkit.path(override_filename, paths.OVERRIDES)
        df = self.try_input_mapped_long_df(self.df, self.genomics_dict_df)
        
        return df



    def try_input_mapped_long_df(self, df, map_df): # for Medications and Genomics
        ''' 
        If override_csv_name exists in overrides folder:
        Maps terms using map_df and inputs into main csv
        '''
        self.df = df
        self.map_df = map_df
        if self.df is None or self.override_csv_path is None or self.map_df is None:
            self._alert_errors()
            return None

        override_df = self.csvkit.robust_read(self.override_csv_path) 
        df = self._get_final_df(override_df)
        
        return df



    def _alert_errors(self):
        if self.df is None:
            console.error("No step csvs found in 'steps' folder")
        
        if self.override_csv_path is None:
            console.info_missing_file({self.override_csv_path}, 'overrides')



    def _get_final_df(self, override_df):
        mapped_long_df = self.try_get_mapped_long_df(override_df)
        if mapped_long_df.empty:
            return self.df

        final_df = self.try_get_merged_final_df(self.df, mapped_long_df)

        return final_df



    def try_get_mapped_long_df(self, override_df):
        ''' Reads override csv, cleans prefixes, splits variants, and maps regions. '''
        if override_df.empty:
            return pd.DataFrame()

        override_df = self._prep_override_df(override_df)

        is_cdna, is_protein = self._is_variant_type(override_df)
        override_df = self._get_clean_cdna_col(override_df, is_cdna)
        if is_protein.any():
            override_df = self._populate_protein_metrics(override_df, is_protein)

        return override_df

    
    def _is_variant_type(self, override_df):
        clean_type_col = override_df['variant_type'].str.lower().str.strip()
        is_cdna = clean_type_col == 'cdna'
        is_protein = clean_type_col == 'protein'

        return is_cdna, is_protein


    def _get_clean_cdna_col(self, o_df, is_cdna):
        if is_cdna.any():
            o_df.loc[is_cdna, config.cdna_variant] = o_df.loc[is_cdna, self.term]

        return o_df



    def try_get_merged_final_df(self, main_df, mapped_long_df):
        if mapped_long_df.empty:
            return main_df

        aligned_df = self._align_and_update_main_df(main_df, mapped_long_df)
        final_df = bio.compute_variant_strings(aligned_df)
        final_df = final_df.drop(columns = config.genomic_cols, errors = 'ignore')

        return final_df



    def _prep_override_df(self, o_df):
        o_df = o_df.dropna(subset = [self.r_term]).copy()
        remove_prefix = o_df[self.r_term].str.replace(r'^[cp]\.', '', regex = True)
        o_df[self.term] = remove_prefix.str.strip()

        for col in config.genomics_split_cols:
            o_df[col] = pd.NA if col == config.protein_pos else None

        return o_df



    def _populate_protein_metrics(self, o_df, is_protein):
        is_protein_term_col = o_df.loc[is_protein, self.term]
        aa_orig_1, pos_num, aa_repl_1 = bio.extract_protein_splits(is_protein_term_col)
        
        o_df.loc[is_protein, config.protein_aa_orig_1] = aa_orig_1
        o_df.loc[is_protein, config.protein_pos] = pos_num
        o_df.loc[is_protein, config.protein_aa_repl_1] = aa_repl_1

        if self.genomics_dict_df is not None and not self.genomics_dict_df.empty:
            o_df = self._add_position_regions(o_df, is_protein)

        return o_df



    def _add_position_regions(self, df, is_protein):
        df.loc[is_protein, config.protein_region] = df.loc[is_protein].apply(
            self._get_position_region, axis = 1)
        
        return df



    def _get_position_region(self, row):
        pos = row[config.protein_pos]
        g_dict = self.genomics_dict_df
        if pd.isna(pos) or g_dict is None:
            return ''

        pos_range = (g_dict['start_pos'] <= pos) & (g_dict['end_pos'] >= pos)
        matched_rows = g_dict[pos_range]

        if not matched_rows.empty:
            return matched_rows.iloc[0]['region']
            
        return 'Unknown'



    def _align_and_update_main_df(self, main_df, mapped_long_df):
        updates_wide = mapped_long_df.groupby(self.id_col).first()

        main_idxed = main_df.set_index(self.id_col)
        shared_idx = main_idxed.index.intersection(updates_wide.index)
        
        if not shared_idx.empty:
            for col in config.genomics_split_cols:
                main_idxed = self._update_col(col, shared_idx, updates_wide, main_idxed)
                
        return main_idxed.reset_index()



    def _update_col(self, col, shared_index, updates_wide, main_indexed):
        if col not in main_indexed.columns:
            main_indexed[col] = None
        main_indexed.loc[shared_index, col] = updates_wide.loc[shared_index, col]
        
        return main_indexed



    def _try_create_gene_position_refs(self):
        uniprot = UniProtQuery()
        uniprot.create_gene_position_refs()

    def _get_genomics_for_review(self):
        local_ai = LocalAI(schema = GenomicList, field_name = 'variants')
        extractor_configs = self._get_configs()
        extractor = ExtractorAI(local_ai, extractor_configs)
        df = extractor.get_for_review(self.df)

        return df

    def _get_configs(self):
        extractor_configs = {
            'name': self.get_process_name(),
            'cols': config.genomic_cols,
            'prompt': config.prompt_genomics,
            'schema': GenomicList}

        return extractor_configs