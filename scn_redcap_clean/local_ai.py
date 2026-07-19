import requests
import shutil
import subprocess
import sys

from .processor_json import ProcessorJSON
from . import console, config

local_url = 'http://127.0.0.1:11434/api/chat'


class LocalAI:
    ''' Standardizes medications and supplements using local AI Ollama. '''
    
    def __init__(self, schema, field_name, model = 'llama3:latest', url = local_url):

        self.model = model
        self.url = url
        self.response_schema = schema.model_json_schema()
        self.json_field_name = field_name

    def ensure_local_ai(self):
        if shutil.which('ollama') is None:
            self._alert_not_downloaded()
            return
        
        self._get_base_service_url()
        self._ensure_ollama_is_running()
        self._ensure_local_ai_model()

    def extract_term(self, prompt: str, text: str):
        system_instruction = self._get_ai_system_instruction(prompt)
        ollama_request = self._get_ollama_request(system_instruction, text)
        extracted_list, confidence_score, is_timeout = self._try_ollama_results(
            ollama_request)
        
        return extracted_list, confidence_score, is_timeout

    def _alert_not_downloaded(self):
        m = 'Ollama not found. Download and install from:\n https://ollama.com/download'
        console.alert(m)

    def _get_base_service_url(self):
        self.base_service_url = self.url.split('/api')[0]
        if 'localhost' in self.base_service_url:
            self.base_service_url = self.base_service_url.replace(
                'localhost', '127.0.0.1')

    def _ensure_ollama_is_running(self):
        try:
            requests.get(self.base_service_url, timeout = 1)
        except requests.exceptions.ConnectionError:
            self._run_ollama()

    def _run_ollama(self):
        print("Running 'ollama'...")
        
        args = ['ollama', 'serve']
        stderr = subprocess.DEVNULL
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        
        subprocess.Popen(
            args, stdout = None, stderr = stderr, creationflags = creationflags)

    def _ensure_local_ai_model(self):
        print(f"Ensuring local model '{self.model}'...")
        
        process = subprocess.Popen(
            ['ollama', 'pull', self.model], stdout =  None, stderr = subprocess.PIPE)
        
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print(f" Downloading '{self.model}' via Ollama...\n")

    def _get_ai_system_instruction(self, prompt):
        system_instruction = (
            f"{prompt}\n CRITICAL: You must return valid JSON matching the schema. "
            'Write standard JSON format. Do NOT place commas on a new line before a key name.')
        
        return system_instruction

    def _get_ollama_request(self, system_instruction, text):
        static_instructions = {'role': 'system', 'content': system_instruction}
        specific_cell_text = {'role': 'user', 'content': f"Text: '{text}'"}
        
        request_structure = [static_instructions, specific_cell_text]
        is_non_batch_reponse_process = False
        deterministic = {'temperature': 0}
        highest_probability_only = 1
        is_returning_probability_metrics = True
        
        ollama_request = {
            'model': self.model,
            'messages': request_structure,
            'format': self.response_schema, 
            'stream': is_non_batch_reponse_process,
            'options': deterministic,
            'logprobs': is_returning_probability_metrics,
            'top_logprobs': highest_probability_only}

        return ollama_request

    def _try_ollama_results(self, request):
        try:
            extracted_list, confidence_score = self._get_ollama_results(request)
            is_timeout = False
            return extracted_list, confidence_score, is_timeout

        except requests.exceptions.Timeout:
            is_timeout = True
            return [], 0.0, is_timeout

        except Exception:
            is_timeout = False
            return [], 0.0, is_timeout

    def _get_ollama_results(self, request):
        body = self._try_response_body(request)

        processor = ProcessorJSON(body, self.json_field_name)
        extracted_list = processor.get_extracted_terms_list()
        confidence_score = processor.get_confidence_percentage()

        return extracted_list, confidence_score

    def _try_response_body(self, request):
        self._set_timeout()
        try:      
            body = self._get_reponse_body_json(request)
            return body
            
        except requests.exceptions.Timeout:
            console.alert(f"AI term extraction timed out after {self.timeout} seconds.")
            raise

    def _get_reponse_body_json(self, request):
        response = requests.post(self.url, json = request, timeout = self.timeout)
        response.raise_for_status()            
        body = response.json()
        
        return body

    def _set_timeout(self):
        self.timeout = getattr(config, 'ai_extraction_timeout', 30)
        if not self.timeout:
            self.timeout = 30
