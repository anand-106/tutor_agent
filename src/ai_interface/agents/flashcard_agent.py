from typing import Dict, List
from .base_agent import BaseAgent
import json

class FlashcardAgent(BaseAgent):
    def process(self, text: str, num_cards: int = 3) -> Dict:
        """Generate focused study flashcards from text"""
        self.retry_count = 0
        
        while self.retry_count < self.max_retries:
            try:
                if len(text.strip()) < 50:
                    self.logger.warning("Text too short for meaningful flashcard generation")
                    return self._create_basic_flashcards("Text too short")

                prompt = f"""Create focused study flashcards that help remember the main points of the text.

                IMPORTANT: Your response must be ONLY valid JSON, with no additional text or explanation.
                
                Required JSON structure:
                {{
                    "topic": "Main Topic",
                    "description": "Core concept to remember",
                    "flashcards": [
                        {{
                            "id": "unique_number",
                            "front": {{
                                "title": "Key concept or main point",
                                "points": ["Point 1", "Point 2", "Point 3"]
                            }},
                            "back": {{
                                "title": "Main explanation",
                                "points": ["Detail 1", "Detail 2", "Detail 3"]
                            }},
                            "category": "Main Point/Core Concept/Key Term",
                            "importance": "Critical/Important/Good to Know",
                            "is_pinned": false
                        }}
                    ]
                }}

                Requirements:
                1. Generate {num_cards} essential flashcards that capture the most important points
                2. Each flashcard must:
                   - Focus on ONE key concept or main point
                   - Have front content with a title and 2-3 key points
                   - Have back content with a title and 2-4 detailed points
                   - Be categorized by type of information
                   - Be rated by importance for prioritized study
                3. Points should be:
                   - Clear and concise
                   - Related to the main concept
                   - Easy to understand
                   - Listed in logical order
                4. All content must be based on the provided text
                5. Response must be valid JSON only

                Text to analyze:
                {text[:10000]}"""

                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.2,
                        "max_output_tokens": 2000,
                        "top_p": 0.95,
                        "top_k": 40
                    }
                )

                response_text = response.text.strip()
                
                # Clean up the response text
                start = response_text.find('{')
                end = response_text.rindex('}') + 1
                if start == -1 or end == -1:
                    raise ValueError("No valid JSON found in response")
                    
                response_text = response_text[start:end]
                
                try:
                    flashcards_data = json.loads(response_text)
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON decode error: {str(e)}")
                    self.logger.debug(f"Problematic JSON: {response_text}")
                    raise ValueError(f"Invalid JSON format: {str(e)}")
                
                # Validate structure
                if not isinstance(flashcards_data, dict):
                    raise ValueError("Response is not a dictionary")
                
                required_keys = ["topic", "description", "flashcards"]
                for key in required_keys:
                    if key not in flashcards_data:
                        raise ValueError(f"Missing required key: {key}")
                
                if not isinstance(flashcards_data["flashcards"], list):
                    raise ValueError("Flashcards is not a list")
                
                for card in flashcards_data["flashcards"]:
                    required_card_keys = ["id", "front", "back", "category", "importance", "is_pinned"]
                    if not all(k in card for k in required_card_keys):
                        raise ValueError("Flashcard missing required fields")
                    
                    # Validate front and back structure
                    for side in ["front", "back"]:
                        if not isinstance(card[side], dict):
                            raise ValueError(f"Card {side} must be a dictionary")
                        if not all(k in card[side] for k in ["title", "points"]):
                            raise ValueError(f"Card {side} missing title or points")
                        if not isinstance(card[side]["points"], list):
                            raise ValueError(f"Card {side} points must be a list")
                
                self.logger.info(f"Successfully generated {len(flashcards_data['flashcards'])} focused flashcards")
                return flashcards_data

            except Exception as e:
                if "quota" in str(e).lower():
                    self.retry_count += 1
                    try:
                        self._switch_api_key()
                        continue
                    except Exception:
                        if self.retry_count >= self.max_retries:
                            self.logger.error("All API keys exhausted")
                            return self._create_basic_flashcards("API quota exceeded")
                        continue
                else:
                    self.logger.error(f"Error generating flashcards: {str(e)}")
                    return self._create_basic_flashcards(str(e))

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