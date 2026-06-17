import sys
from pathlib import Path
import pandas as pd

# 1. Dynamically append the project root directory so Python can find your files
project_root = Path('/Users/melissa/Documents/ToyEpCleaning')
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# 2. Use an absolute import instead of a relative one
from scn_redcap_clean import utils

# 3. Load your files and test
v3_path = '/Users/melissa/Documents/ToyEpCleaning/archive/translations_for_review_v003.csv'
v4_path = '/Users/melissa/Documents/ToyEpCleaning/archive/translations_for_review_v004.csv'

last_df = pd.read_csv(v3_path)
current_df = pd.read_csv(v4_path)

# Run your comparison check
is_match = utils.is_df_identical(current_df, last_df)
print(f"\n>>> DO THEY MATCH? {is_match}")
