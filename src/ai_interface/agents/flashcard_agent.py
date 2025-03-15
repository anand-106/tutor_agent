from typing import Dict, List
from .base_agent import BaseAgent
import json

class FlashcardAgent(BaseAgent):
    def process(self, text: str, num_cards: int = 3) -> Dict:
        """Generate focused study flashcards with memorizable bullet points"""
        self.retry_count = 0
        
        while self.retry_count < self.max_retries:
            try:
                if len(text.strip()) < 50:
                    self.logger.warning("Text too short for meaningful flashcard generation")
                    return self._create_basic_flashcards("Text too short")

                prompt = f"""Create focused study flashcards that help memorize key points for exam preparation.

                IMPORTANT: Your response must be ONLY valid JSON, with no additional text or explanation.
                
                Required JSON structure:
                {{
                    "topic": "Main Topic",
                    "description": "Core concept to memorize",
                    "flashcards": [
                        {{
                            "id": "unique_number",
                            "front": {{
                                "title": "Key concept or definition to memorize",
                                "points": [
                                    "Concise bullet point 1",
                                    "Concise bullet point 2",
                                    "Concise bullet point 3",
                                    "... more points as needed"
                                ]
                            }},
                            "back": {{
                                "title": "Detailed explanation",
                                "points": [
                                    "Expanded explanation of point 1",
                                    "Expanded explanation of point 2",
                                    "Expanded explanation of point 3",
                                    "Additional important details"
                                ]
                            }},
                            "category": "Definition/Formula/Key Concept/Important Date/Fact",
                            "importance": "Critical/Important/Good to Know",
                            "is_pinned": false
                        }}
                    ]
                }}

                Requirements:
                1. Generate {num_cards} essential flashcards focusing on content that must be memorized
                2. Each flashcard must:
                   - Focus on ONE key concept that needs memorization
                   - Have front content with ALL important points to memorize
                   - Keep each point short and concise (3-8 words each)
                   - Have back content with detailed explanations of each point
                   - Be categorized by type of memorizable content
                   - Be rated by importance for exam preparation
                3. Front points should be:
                   - Very concise (3-8 words each)
                   - Easy to recall during exams
                   - Focus on key facts, formulas, or definitions
                   - Include ALL important points (no limit on number of points)
                   - Each point should be a standalone fact or concept
                4. Back points should:
                   - Expand on each front point
                   - Provide context and examples
                   - Include additional relevant details
                5. All content must be based on the provided text
                6. Response must be valid JSON only

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
                        
                        # Validate point lengths for front side
                        if side == "front":
                            for i, point in enumerate(card[side]["points"]):
                                words = point.split()
                                if len(words) > 8:
                                    self.logger.warning(f"Front point too long: {point}")
                                    # Split into multiple points if too long
                                    if len(words) <= 16:  # If it can be split into two reasonable points
                                        mid = len(words) // 2
                                        card[side]["points"][i] = " ".join(words[:mid])
                                        card[side]["points"].insert(i + 1, " ".join(words[mid:]))
                                    else:
                                        # If too long to split nicely, truncate
                                        card[side]["points"][i] = " ".join(words[:8]) + "..."
                
                self.logger.info(f"Successfully generated {len(flashcards_data['flashcards'])} memorization flashcards")
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