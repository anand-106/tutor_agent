from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent
import json
import re

class FlashcardAgent(BaseAgent):
    def __init__(self, api_keys: list, shared_state: Optional[Dict[str, Any]] = None):
        super().__init__(api_keys, shared_state)
        
    def process(self, text, num_cards=5):
        """
        Process the text and generate flashcards.
        
        Args:
            text (str): The text to generate flashcards from.
            num_cards (int, optional): The number of flashcards to generate. Defaults to 5.
            
        Returns:
            dict: A dictionary containing the flashcards and related information.
        """
        if len(text) < 100:
            self.logger.warning("Input text is too short for meaningful flashcard generation")
            return {"flashcards": [], "topic": "Insufficient Content", "description": "The provided text is too short to generate meaningful flashcards."}
        
        self.logger.info(f"Generating {num_cards} flashcards from text of length {len(text)}")
        
        # Extract the main topic from the current_topic in shared state if available
        topic = self.shared_state.get("current_topic", "Study Topic")
        self.logger.info(f"Using topic: {topic}")
        
        # Create a JSON prompt for structured flashcard generation
        prompt = f"""
        Create {num_cards} educational flashcards based on the following text. 
        The flashcards should cover the most important concepts and be structured as follows:
        
        ```json
        {{
            "topic": "{topic}",
            "description": "Brief overview of the content covered in these flashcards",
            "flashcards": [
                {{
                    "id": "1",
                    "topic": "Specific subtopic or concept",
                    "front": {{
                        "title": "Clear, concise question or concept",
                        "points": ["Optional bullet points to clarify the question"]
                    }},
                    "back": {{
                        "explanation": "Comprehensive but concise explanation",
                        "points": ["Key points", "Important details", "Relevant examples"],
                        "additional_resources": "Optional references or further reading"
                    }},
                    "is_pinned": false
                }}
            ]
        }}
        ```
        
        Guidelines:
        1. Focus on key concepts, definitions, and relationships
        2. Front side should be clear and concise
        3. Back side should be comprehensive but not verbose
        4. Ensure accuracy and balance difficulty across cards
        5. Make sure each flashcard has a unique ID
        6. Include relevant examples where appropriate
        7. Cover different aspects of the topic to ensure comprehensive learning
        
        Text to process:
        {text}
        
        Return only the JSON. No prose or explanation.
        """
        
        try:
            # Generate flashcards using the gemini model
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Extract the JSON part
            try:
                # First try to find JSON between backticks
                json_pattern = r"```json\s*([\s\S]*?)\s*```"
                json_match = re.search(json_pattern, response_text)
                
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # If no JSON with backticks, try to find standalone JSON
                    json_str = response_text.strip()
                
                flashcard_data = json.loads(json_str)
                
                # Validate the flashcard data
                if not isinstance(flashcard_data, dict):
                    raise ValueError("Flashcard data is not a dictionary")
                    
                if "flashcards" not in flashcard_data:
                    raise ValueError("No flashcards found in the response")
                    
                if not isinstance(flashcard_data["flashcards"], list):
                    raise ValueError("Flashcards is not a list")
                
                # Ensure all flashcards have required fields
                for i, card in enumerate(flashcard_data["flashcards"]):
                    if "id" not in card:
                        card["id"] = str(i+1)
                    if "is_pinned" not in card:
                        card["is_pinned"] = False
                
                self.logger.info(f"Successfully generated {len(flashcard_data['flashcards'])} flashcards")
                return flashcard_data
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON from response: {e}")
                return {"flashcards": [], "topic": topic, "description": "Failed to generate flashcards due to JSON parsing error."}
            except ValueError as e:
                self.logger.error(f"Invalid flashcard data: {e}")
                return {"flashcards": [], "topic": topic, "description": f"Failed to generate flashcards: {str(e)}"}
                
        except Exception as e:
            self.logger.error(f"Error generating flashcards: {e}")
            return {"flashcards": [], "topic": topic, "description": "Failed to generate flashcards due to an unexpected error."}

    def _create_basic_flashcards(self, reason: str) -> Dict:
        """Create a basic flashcards structure"""
        return {
            "topic": "Basic Flashcards",
            "description": f"Could not generate flashcards: {reason}",
            "flashcards": [
                {
                    "id": "1",
                    "front": {
                        "title": "Why couldn't the flashcards be generated?",
                        "points": [reason]
                    },
                    "back": {
                        "title": "Error Details",
                        "points": ["Please try again with more detailed input"]
                    },
                    "category": "Error",
                    "importance": "N/A",
                    "is_pinned": false
                }
            ]
        } 