import pandas as pd

from .cleaning_step import CleaningStep
from .csv_writer import CsvWriter
from .csv_kit import CsvKit
from .extract_ai import ExtractorAI
from .local_ai import LocalAI
from .uniprot import UniProtQuery
from . import bio, config, console, paths, utils, schemas

class Genomics(CleaningStep):
    ''' Extracts raw genomic and protein variants using local AI Ollama. '''
    
    def __init__(self, data):

        self.data = data.copy()
        self.archiver = CsvWriter()
        self.id_col = config.merge_on_id_column
        self.csvkit = CsvKit()
        self.genomics_dict_data = self.csvkit.path_to_df(
            f'{config.gene_name}_position_map_uniprot', paths.REF)
        self.r_term = schemas.recommended_term_str()
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
        data = self._get_genomics_for_review()

        return data

    def create_final_data(self):
        '''  Maps genomic variants to UniProt position map and inputs into main csv '''
        override_filename = utils.get_manual_cvsname(self.get_process_name())
        self.override_csv_path = self.csvkit.path(override_filename, paths.OVERRIDES)
        data = self._input_mapped_long_data(self.data, self.genomics_dict_data)
        
        return data

    def _input_mapped_long_data(self, data, map_data): # for Medications and Genomics
        ''' 
        If override_csv_name exists in overrides folder:
        Maps terms using map_data and inputs into main csv
        '''
        self.data = data
        self.map_data = map_data
        if self.data is None or self.override_csv_path is None or self.map_data is None:
            self._alert_errors()
            return None

        override_data = self.csvkit.robust_read(self.override_csv_path) 
        data = self._get_final_data(override_data)
        
        return data

    def _alert_errors(self):
        if self.data is None:
            console.error("No step csvs found in 'steps' folder")
        
        if self.override_csv_path is None:
            console.info_missing_file({self.override_csv_path}, 'overrides')

    def _get_final_data(self, override_data):
        mapped_long_data = self._get_mapped_long_data(override_data)
        if mapped_long_data.empty:
            return self.data

        final_data = self._get_merged_final_data(self.data, mapped_long_data)

        return final_data

    def _get_mapped_long_data(self, override_data):
        ''' Reads override csv, cleans prefixes, splits variants, and maps regions. '''
        if override_data.empty:
            return pd.DataFrame()

        override_data = self._prep_override_data(override_data)

        is_cdna, is_protein = self._is_variant_type(override_data)
        override_data = self._get_clean_cdna_col(override_data, is_cdna)
        if is_protein.any():
            override_data = self._populate_protein_metrics(override_data, is_protein)

        return override_data

    def _is_variant_type(self, override_data):
        clean_type_col = override_data['variant_type'].str.lower().str.strip()
        is_cdna = clean_type_col == 'cdna'
        is_protein = clean_type_col == 'protein'

        return is_cdna, is_protein

    def _get_clean_cdna_col(self, o_data, is_cdna):
        if is_cdna.any():
            o_data.loc[is_cdna, config.cdna_variant] = o_data.loc[is_cdna, self.term]

        return o_data

    def _get_merged_final_data(self, main_data, mapped_long_data):
        if mapped_long_data.empty:
            return main_data

        aligned_data = self._align_and_update_main_data(main_data, mapped_long_data)
        final_data = bio.compute_variant_strings(aligned_data)
        final_data = final_data.drop(columns = config.genomic_cols, errors = 'ignore')

        return final_data

    def _prep_override_data(self, o_data):
        o_data = o_data.dropna(subset = [self.r_term]).copy()
        remove_prefix = o_data[self.r_term].str.replace(r'^[cp]\.', '', regex = True)
        o_data[self.term] = remove_prefix.str.strip()

        for col in config.genomics_split_cols:
            o_data[col] = pd.NA if col == config.protein_pos else None

        return o_data

    def _populate_protein_metrics(self, o_data, is_protein):
        is_protein_term_col = o_data.loc[is_protein, self.term]
        aa_orig_1, pos_num, aa_repl_1 = bio.extract_protein_splits(is_protein_term_col)
        
        o_data.loc[is_protein, config.protein_aa_orig_1] = aa_orig_1
        o_data.loc[is_protein, config.protein_pos] = pos_num
        o_data.loc[is_protein, config.protein_aa_repl_1] = aa_repl_1

        if self.genomics_dict_data is not None and not self.genomics_dict_data.empty:
            o_data = self._add_position_regions(o_data, is_protein)

        return o_data

    def _add_position_regions(self, data, is_protein):
        data.loc[is_protein, config.protein_region] = data.loc[is_protein].apply(
            self._get_position_region, axis = 1)
        
        return data

    def _get_position_region(self, row):
        pos = row[config.protein_pos]
        g_dict = self.genomics_dict_data
        if pd.isna(pos) or g_dict is None:
            return ''

        pos_range = (g_dict['start_pos'] <= pos) & (g_dict['end_pos'] >= pos)
        matched_rows = g_dict[pos_range]

        if not matched_rows.empty:
            return matched_rows.iloc[0]['region']
            
        return 'Unknown'

    def _align_and_update_main_data(self, main_data, mapped_long_data):
        updates_wide = mapped_long_data.groupby(self.id_col).first()

        main_idxed = main_data.set_index(self.id_col)
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
        local_ai = LocalAI(schema = schemas.GenomicList, field_name = 'variants')
        extractor_configs = self._get_configs()
        extractor = ExtractorAI(local_ai, extractor_configs)
        data = extractor.get_for_review(self.data)

        return data

    def _get_configs(self):
        extractor_configs = {
            'name': self.get_process_name(),
            'cols': config.genomic_cols,
            'prompt': config.prompt_genomics,
            'schema': schemas.GenomicList}

        return extractor_configs