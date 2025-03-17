from abc import ABC, abstractmethod
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from ...data_processing.logger_config import setup_logger

class BaseAgent(ABC):
    def __init__(self, api_keys: List[str], shared_state: Optional[Dict[str, Any]] = None):
        self.logger = setup_logger(self.__class__.__name__.lower())
        self.api_keys = api_keys
        self.current_key_index = 0
        self.retry_count = 0
        self.max_retries = 3
        self.shared_state = shared_state  # Reference to the shared state dictionary
        
        if not self.api_keys:
            raise ValueError("No API keys provided")
            
        try:
            self._initialize_model()
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini model: {str(e)}")
            raise
            
        # Log shared state initialization
        if shared_state is not None:
            self.logger.info(f"{self.__class__.__name__} initialized with shared state")
        else:
            self.logger.info(f"{self.__class__.__name__} initialized without shared state")

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
        
    def get_shared_state_value(self, key: str, default=None) -> Any:
        """Get a value from the shared state with logging"""
        if self.shared_state is None:
            self.logger.warning(f"{self.__class__.__name__} attempted to access shared state but it's None")
            return default
            
        value = self.shared_state.get(key, default)
        self.logger.info(f"{self.__class__.__name__} accessed shared_state['{key}']")
        return value
        
    def update_shared_state(self, key: str, value: Any) -> None:
        """Update a value in the shared state with logging"""
        if self.shared_state is None:
            self.logger.warning(f"{self.__class__.__name__} attempted to update shared state but it's None")
            return
            
        self.shared_state[key] = value
        self.logger.info(f"{self.__class__.__name__} updated shared_state['{key}']")

    @abstractmethod
    def process(self, *args, **kwargs):
        """Main processing method to be implemented by each agent"""
        pass 