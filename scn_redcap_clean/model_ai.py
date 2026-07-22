from enum import Enum

class Model_AI(Enum):
    lightweight = 'llama3.2' # for ~8GB RAM (3B model)
    standard = 'llama3:latest' # for 16GB+ RAM (8B model)