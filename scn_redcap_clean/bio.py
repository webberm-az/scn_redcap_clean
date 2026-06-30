from Bio import SeqUtils
import pandas as pd
from . import config


def extract_protein_splits(term_series):
    segments = _get_split_p(term_series)
    aa_orig_1, pos_num, aa_repl_1 = _get_standardized_aa_1_split_p(segments)

    return aa_orig_1, pos_num, aa_repl_1



def _get_split_p(term_series):
    aa_num_aa = r'^([A-Za-z\?]+)(\d+)([A-Za-z\*\?]+)$'
    segments = term_series.str.extract(aa_num_aa)

    return segments



def _get_standardized_aa_1_split_p(segments):
    aa_orig_1 = segments[0].apply(standardize_aa_seq1)
    pos_num = pd.to_numeric(segments[1], errors = 'coerce')
    aa_repl_1 = segments[2].apply(standardize_aa_seq1)
    
    return aa_orig_1, pos_num, aa_repl_1



def standardize_aa_seq1(aa_str):
    try:
        return SeqUtils.seq1(aa_str) if len(aa_str) == 3 else aa_str.upper()
    except Exception:
        return ''



def aa_to_seq3(aa_seq1):
    try:
        return SeqUtils.seq3(aa_seq1) if pd.notna(aa_seq1) else ''
    except Exception:
        return ''



def compute_variant_strings(df):
    has_protein = df[config.protein_pos].notna()
    position_num_str = _get_position_str(df)

    df = _add_aa3_cols(has_protein, df, position_num_str)
    df = _add_protein_aa1_col(has_protein, df, position_num_str)

    return df



def _get_position_str(df):
    pos_str = df[config.protein_pos].map(lambda x: f"{x:.0f}" if pd.notna(x) else "")

    return pos_str



def _add_aa3_cols(has_protein, df, pos_str):
    orig_3 = df[config.protein_aa_orig_1].apply(aa_to_seq3).fillna('')
    df[config.protein_aa_orig_3] = orig_3.where(has_protein, None)

    repl_3 = df[config.protein_aa_repl_1].apply(aa_to_seq3).fillna('')
    df[config.protein_aa_repl_3] = repl_3.where(has_protein, None)

    v3 = orig_3 + pos_str + repl_3
    df[config.protein_variant_3] = v3.where(has_protein, None)

    return df



def _add_protein_aa1_col(has_protein, df, pos_str):
    v1 = _get_variant_aa1(pos_str, df)
    df[config.protein_variant_1] = v1.where(has_protein, None)

    return df



def _get_variant_aa1(pos_str, df):
    orig_1 = df[config.protein_aa_orig_1].fillna('')
    repl_1 = df[config.protein_aa_repl_1].fillna('')
    v1 = orig_1 + pos_str + repl_1

    return v1
    