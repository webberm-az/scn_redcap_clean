import requests
import shutil
import subprocess
import sys

from .processor_json import ProcessorJSON
from . import console

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
        
        base_service_url = self._get_base_service_url()
        self._ensure_ollama_is_running(base_service_url)
        self._ensure_local_ai_model()



    def extract_term(self, prompt: str, text: str) -> tuple[list, float]:
        system_instruction = self._get_ai_system_instruction(prompt)
        ollama_request = self._get_ollama_request(system_instruction, text)
        entities_and_confidence = self._try_get_terms_and_conf_score(ollama_request)
        
        return entities_and_confidence



    def _alert_not_downloaded(self):
        m = 'Ollama not found. Download and install from:\n https://ollama.com/download'
        console.alert(m)



    def _get_base_service_url(self):
        base_service_url = self.url.split('/api')[0]
        if 'localhost' in base_service_url:
            base_service_url = base_service_url.replace('localhost', '127.0.0.1')
        
        return base_service_url



    def _ensure_ollama_is_running(self, base_service_url):
        try:
            requests.get(base_service_url, timeout = 1)
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



    def _try_get_terms_and_conf_score(self, request) -> tuple[list, float]:
        try:
            terms_with_confidence_scores = self._get_terms_with_confidence_scores(request)
            return terms_with_confidence_scores

        except Exception:
            empty_zero_confident = [], 0.0
            return empty_zero_confident



    def _get_terms_with_confidence_scores(self, request):
        body = self._get_reponse_body_json(request)

        processor = ProcessorJSON(body, self.json_field_name)
        extracted_list = processor.get_extracted_terms_list()
        confidence_score = processor.get_confidence_percentage()
        meds_with_confidence_scores = extracted_list, confidence_score

        return meds_with_confidence_scores



    def _get_reponse_body_json(self, request):
        response = requests.post(self.url, json = request, timeout = 30)
        response.raise_for_status()            
        body = response.json()
        
        return body
