import json
import math
import subprocess
import shutil
import requests
import time
from pydantic import create_model, Field

from . import console
from . import config


model = 'llama3:latest'
local_url = 'http://127.0.0.1:11434/api/chat'


class LocalAI:
    ''' Standardizes medications and supplements using local AI Ollama. '''
    
    def __init__(self, model = model, url = local_url):

        self.model = model
        self.url = url
        self.response_schema = self._set_ai_response_schema()
        self.ollama_meds_col = 'ollama_meds'
        self.ai_confidence_col = 'ollama_confidence'
        self.id_col = config.merge_on_id_column
        self.base_long_cols = [self.id_col, 'from_column', 'raw_text']


    def ensure_local_ai(self):
        """
        Verifies Ollama is installed, running, and has the required model downloaded.
        """
        if shutil.which("ollama") is None:
            message = "Ollama not found. Download and install from:\n \
                 https://ollama.com/download"
            console.alert(message)
            return
        
        base_service_url = self.url.split('/api')[0]
        if "localhost" in base_service_url:
            base_service_url = base_service_url.replace("localhost", "127.0.0.1")
        
        try:
            requests.get(base_service_url, timeout = 1)
        except requests.exceptions.ConnectionError:
            print("Ollama background service isn't running. Running 'ollama serve'...")
            import sys
            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NO_WINDOW
            
            subprocess.Popen(
                ["ollama", "serve"], 
                stdout = None, 
                stderr = subprocess.DEVNULL,
                creationflags = creation_flags)

        print(f"Ensuring local model '{self.model}'...")
        process = subprocess.Popen(
            ["ollama", "pull", self.model], stdout =  None, stderr = subprocess.PIPE)
        
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print(f" Downloading '{self.model}' via Ollama...\n")




    def analyze_text(self, prompt: str, text: str) -> tuple[list, float]:
        """Sends inference request to Ollama and calculates a token average confidence score."""
        system_instruction = (
            f"{prompt}\n"
            "CRITICAL: You must return valid JSON matching the schema. "
            "Write standard JSON format. Do NOT place commas on a new line before a key name."
        )
        ollama_request = {
            'model': self.model,
            'messages': [ # request type/structure
                {'role': 'system', 'content': system_instruction},
                {'role': 'user', 'content': f"Text: '{text}'"}],
            'format': self.response_schema, 
            'stream': False, # process entire prompt then return entire response
            'options': {'temperature': 0}, # indentical repeats (removes 'creativity')
            'logprobs': True, # certainty metrics for confidence scores
            'top_logprobs': 1 } # just return probability for actual choice (choice 1)

        return self._get_meds_and_confidence_score(ollama_request)



    def _get_meds_and_confidence_score(self, request) -> tuple[list, float]:
        try:
            response = requests.post(self.url, json = request, timeout = 30)
            response.raise_for_status()            
            body = response.json()

            content_str = body['message']['content']
            raw_json = json.loads(content_str)

            if isinstance(raw_json, list):
                extracted_meds_list = raw_json
            else:
                extracted_meds_list = raw_json.get('substances', [])

            confidence_score = self._get_confidence_percentage(body)
            meds_with_confidence_scores = extracted_meds_list, confidence_score

            return meds_with_confidence_scores

        except Exception as e:
            print(f"Extraction pipeline skipped row due to format exception: {e}")
            empty_not_confident = [], 0.0
            return empty_not_confident



    def _get_confidence_percentage(self, body):
        ''' Converts log probabilities average percentage score. '''
        log_probabilities_list = body.get('logprobs')
        print('DEBUG______log_probabilities_list________')
        print(log_probabilities_list)
        # Absolute structural guardrail fallback requested
        if not log_probabilities_list:
            return 0.0

        raw_scores = []
        
        # Ignorable Pydantic JSON template boilerplate keys
        structural_noise = {
            '{', '}', '[', ']', ':', ',', '"', '""', ',\n', '{\n', '[\n', '}\n', ']\n',
            'substances', '"substances"', 'original_term', '"original_term"',
            'standardized_name', '"standardized_name"', 'category', '"category"'
        }

        for entry in log_probabilities_list:
            token_text = entry.get('token', '').strip()
            
            # Filter structural markup noise so score maps strictly to target contents
            if not token_text or token_text in structural_noise or token_text.startswith(('"', ':')):
                continue
                
            if 'logprob' in entry:
                raw_scores.append(entry['logprob'])

        # If remaining evaluation parameters are empty (e.g. empty response list), yield 0.0

        print('DEBUG______raw_scores________')
        print(raw_scores)
        if not raw_scores:
            return 0.0

        # Calculate geometric certainty distribution bounds
        probabilities = [math.exp(score) for score in raw_scores]
        probabilities = [math.exp(score) for score in raw_scores]
        average_probability = sum(probabilities) / len(probabilities)
        confidence_percentage = round(average_probability * 100, 2)
        
        return confidence_percentage



    def _set_ai_response_schema(self):
        unique_suffix = f"_{int(time.time())}"
        
        substance_structure = create_model(
            f'Substance{unique_suffix}',
            __module__=__name__,
            original_term=(str, Field(description='Exact text segment from the original text.')),
            standardized_name=(str, Field(description='The generic English medical name.')),
            category=(str, Field(description="Either 'medication' or 'supplement'")),
        )
        wrapper_model = create_model(
            f'SubstanceCollection{unique_suffix}',
            __module__=__name__,
            substances=(list[substance_structure], Field(description='List of extracted substances.')) # type: ignore
        )
        return wrapper_model.model_json_schema()
