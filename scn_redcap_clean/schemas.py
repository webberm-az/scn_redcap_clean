import pydantic
from typing import Optional

class Medication(pydantic.BaseModel):
    original_term: str = pydantic.Field(
        description = 'The exact text segment extracted from the original text, in its original language.')
    
    recommended_term: str = pydantic.Field(
        description = 'The direct English translation of the original_term. Do not add chemical precision.')



class MedicationList(pydantic.BaseModel):

    substances: list[Medication] = pydantic.Field(
        description = 'List of extracted medications or supplements.')



class Genomic(pydantic.BaseModel):
    variant_type: Optional[str] = pydantic.Field(
        None, 
        description = "Must be exactly one of: 'cDNA' (for c. variants) or 'protein' (for p. variants).")

    recommended_term: Optional[str] = pydantic.Field(
        None, 
        description = 'The variant standardized into basic HGVS-like syntax. '
        'Remove all outer parentheticals, remove all spaces, ensure it starts strictly' " with 'c.' or 'p.'. "
        'Examples:\n'
        "- 'p (E1483K)' -> 'p.E1483K'\n"
        "- 'Pro1483Lys' -> 'p.Pro1483Lys'\n"
        "- 'c 2345+1T>G' -> 'c.2345+1T>G'\n" 
        "- 'dup 123' -> 'c.123dup'\n"
        "- 'c123_124delAG' -> 'c.123_124delAG'")



class GenomicList(pydantic.BaseModel):
    variants: list[Genomic] = pydantic.Field(
        description = 'List of extracted elements.')