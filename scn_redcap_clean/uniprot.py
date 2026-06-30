import csv
from pathlib import Path
from typing import cast
import requests
import pandas as pd # external import

from .csv_kit import CsvKit
from . import console, config



class UniProtQuery:

    def __init__(self, paths, url = 'https://rest.uniprot.org/uniprotkb/'):
        
        self.paths = paths
        self.url = url
        self.csvkit = CsvKit()


    def create_gene_position_refs(self, gene_name = config.gene_name, taxon_id = '9606'):
        ''' Creates reference csv defaults to human taxon_id for accesion index '''
        self.get_output_path(gene_name)
        if self.output_path.exists() and self.output_path_full.exists(): 
            return None
        
        if self.output_path_full.exists(): 
            self._create_filtered_csv()
            return

        accession = self.get_accession_index(gene_name, taxon_id = taxon_id)
        if accession:
            self.create_position_maps(accession = accession, gene_name = gene_name)
            self._create_filtered_csv()
        else:
            m = f"Could not create structural reference csv for {gene_name}."
            console.info(m)



    def _create_filtered_csv(self):
        df = self.csvkit.robust_read_csv(self.output_path_full)
        membrane_locations = ['Topological domain', 'Transmembrane', 'Intramembrane']
        reduced_df = df[df['type'].isin(membrane_locations)].copy()
        
        reduced_df['region'] = reduced_df.loc[:, 'description'].map(
            self._clean_description)
        reduced_df.loc[reduced_df['start_pos'] == 1, 'region'] = 'N-Terminus'
        if not reduced_df.empty:
            last_row_index = reduced_df.index[-1]
            reduced_df.loc[last_row_index, 'region'] = 'C-Terminus'

        self.csvkit.save_csv(cast(pd.DataFrame, reduced_df), self.output_path)



    def _clean_description(self, raw_desc):
        ''' Normalizes UniProt descriptions into clean structural component names.'''
        if pd.isna(raw_desc) or not isinstance(raw_desc, str):
            return ''
        
        if 'Name=' in raw_desc:
            segment = self._clean_name(raw_desc)
            return segment
        
        if raw_desc == 'Cytoplasmic':
            return 'Cytoplasmic Loop'
        if raw_desc == 'Extracellular':
            return 'Extracellular Loop'
        if raw_desc == 'Pore-forming':
            return 'Pore-forming Region'
        else:
            return ''
            


    def _clean_name(self, raw_desc):
        '''Extracts and normalizes domain-specific feature structural strings.'''
        text_segment = self._isolate_name_str(raw_desc)
        if not text_segment:
            return ''

        base_component = self._format_structural_component(text_segment)
        
        return base_component



    def _isolate_name_str(self, raw_desc):
        '''Isolates content wrapped between 'Name=' and its trailing semi-colon.'''
        if 'Name=' not in raw_desc:
            return ''

        return raw_desc.split('Name=')[-1].split(';')[0].strip()



    def _format_structural_component(self, segment_text):
        '''Maps token strings like 'S6 of repeat IV' to 'DIV-S6'.'''
        domain_map = {
            'repeat I': 'DI',
            'repeat II': 'DII',
            'repeat III': 'DIII',
            'repeat IV': 'DIV'}
        
        segment_label = segment_text.split(' ')[0]
        
        for match_string, domain_label in domain_map.items():
            if match_string in segment_text:
                return f'{domain_label}-{segment_label}'
                
        return segment_label



    def get_output_path(self, gene_name):
        fname = f'{gene_name}_position_map_uniprot'
        dir_ref = Path(self.paths.ref)
        self.output_path_full = dir_ref / self.csvkit.add_suffix(f"{fname}_full")
        self.output_path = dir_ref / self.csvkit.add_suffix(fname)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        


    def get_accession_index(self, gene_name: str, taxon_id: str) -> str | None:
        ''' Queries UniProt search API for the human accession ID of gene_name '''
        gene_name = gene_name.upper().strip()
        params = self._get_request_params(gene_name, taxon_id)
        accession = self._try_get_accession_index(params, gene_name, taxon_id)
        
        return accession



    def _try_get_accession_index(self, params, gene_name, taxon_id):
        try:
            results = self._get_results(params)
            accession = self._get_accession_idx(results, gene_name, taxon_id)
            return accession
            
        except requests.exceptions.RequestException as e:
            print(f'Network error mapping gene name: {e}')
            return None



    def _get_accession_idx(self, results, gene_name, taxon_id):
        if results is None:
            print(f'No results for reviewed: {gene_name} and taxonomy id: {taxon_id}')
            return None

        if results:
            return results[0].get('primaryAccession')



    def _get_request_params(self, gene_name, taxon_id):
        query = f"gene_exact:{gene_name} AND taxonomy_id:{taxon_id} AND reviewed:true"
        fields = 'accession, gene_names'
        top_match = 1
        params = {'query': query, 'fields': fields, 'size': top_match}

        return params


    def _get_results(self, params):
        response = requests.get(f'{self.url}search', params = params, timeout = 10)
        response.raise_for_status()
        data = response.json()
        results = data.get('results', [])

        return results



    def create_position_maps(self, accession, gene_name):
        '''
        Queries UniProt REST API, parses topological/transmembrane features,
        and writes a continuous positional lookup map to a CSV file.
        '''
        print(f'Accessing UniProt for {gene_name} ({accession})...')
        
        data = self._try_get_data(accession)
        if data is None:
            return

        features = self._try_get_clean_features(data)
        if features is None:
            return
        
        self._create_csv(features, gene_name)
        print(f'Created UniProt ref for {gene_name} ({accession})...')
        


    def _try_get_data(self, accession):
        url = f'{self.url}{accession}.json'
        try:
            response = requests.get(url, timeout = 15)
            response.raise_for_status()
            data = response.json()
            return data
        
        except requests.exceptions.RequestException as e:
            console.error(f'Failed to reach UniProt API: {e}')
            return None



    def _try_get_clean_features(self, data):
        features = data.get('features', [])
        if not features:
            console.alert('No features found in UniProt query response.')
            return None
        
        sorted_features = sorted(
            features, key = lambda x: x['location']['start']['value'])

        return sorted_features



    def _create_csv(self, features, gene_name):
        headers = ['gene', 'start_pos', 'end_pos', 'type', 'description']
        
        with open(self.output_path_full, mode = 'w', newline = '', encoding = 'utf-8') as f:
            self._write_csv(features, headers, f, gene_name)



    def _write_csv(self, features, headers, f, gene_name):
        writer = csv.writer(f)
        writer.writerow(headers)
        for feat in features:
            self._write_feat(feat, writer, gene_name)



    def _write_feat(self, feat, writer, gene_name):
        f_type = feat.get('type')
        start = feat['location']['start']['value']
        end = feat['location']['end']['value']
        raw_desc = feat.get('description', '')
            
        writer.writerow([gene_name, start, end, f_type, raw_desc])
