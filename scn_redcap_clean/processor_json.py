import json
import math


class ProcessorJSON:
    
    def __init__(self, response_body: dict, field_name: str):
        self.body = response_body
        self.field_name = field_name
        self.is_in_value_zone = False
        self.is_inside_string = False


    def get_extracted_terms_list(self):
        content_str = self.body['message']['content']
        raw_json = json.loads(content_str)

        if isinstance(raw_json, list):
            return raw_json
        else:
            extracted_substances_list = raw_json.get(self.field_name, [])
            return extracted_substances_list



    def get_confidence_percentage(self):
        log_probabilities_list = self.body.get('logprobs')
        if not log_probabilities_list:
            return 0.0
    
        raw_scores = self.get_raw_scores(log_probabilities_list)
        if not raw_scores:
            return 0.0
        
        ave_probability_percent = self.get_average_probability_percentage(raw_scores)

        return ave_probability_percent


    def get_raw_scores(self, log_probabilities_list):
        '''Extracts logprobs for text within JSON string values.'''
        self.is_in_value_zone = False
        self.is_inside_string = False
        scores = []

        for entry in log_probabilities_list:
            token = entry.get('token', '')
            logprob = entry.get('logprob')

            self.update_state(token)
            
            if self.is_logprob(token, logprob):
                scores.append(logprob)
        
        return scores


    
    def get_average_probability_percentage(self, raw_scores):
        probabilities = [math.exp(score) for score in raw_scores]
        average_probability = sum(probabilities) / len(probabilities)
        
        average_probability_percentage = round(average_probability * 100, 2)

        return average_probability_percentage



    def update_state(self, token: str):
        ''' Uses response text markers to update state '''
        
        if ':' in token:
            self.is_in_value_zone = True
            
        elif token in (',', '}', ']'):
            self.is_in_value_zone = False
            self.is_inside_string = False
            
        elif '"' in token and self.is_in_value_zone:
            self.is_inside_string = not self.is_inside_string



    def is_logprob(self, token: str, logprob: float | None):
        ''' Guard condition checking if a token is an extracted term '''
        if not self.is_in_value_zone or not self.is_inside_string:
            return False
        
        if logprob is None or not token.strip():
            return False
        
        return True
