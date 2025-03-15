from abc import ABC, abstractmethod
import google.generativeai as genai
from typing import List, Dict, Any
from ...data_processing.logger_config import setup_logger

class BaseAgent(ABC):
    def __init__(self, api_keys: List[str]):
        self.logger = setup_logger(self.__class__.__name__.lower())
        self.api_keys = api_keys
        self.current_key_index = 0
        self.retry_count = 0
        self.max_retries = 3
        
        if not self.api_keys:
            raise ValueError("No API keys provided")
            
        try:
            self._initialize_model()
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini model: {str(e)}")
            raise

    def _initialize_model(self):
        """Initialize model with current API key"""
        if not self.api_keys:
            raise ValueError("No API keys available")
            
        genai.configure(api_key=self.api_keys[self.current_key_index])
        self.model = genai.GenerativeModel('gemini-1.5-pro')

    def _switch_api_key(self):
        """Switch to next available API key"""
        original_index = self.current_key_index
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        
        if self.current_key_index == original_index:
            raise Exception("All API keys have been tried")
            
        self._initialize_model()
        self.logger.info(f"Switched to API key {self.current_key_index + 1}")

    @abstractmethod
    def process(self, *args, **kwargs):
        """Main processing method to be implemented by each agent"""
        pass 