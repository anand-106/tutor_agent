from typing import Dict, List
from .base_agent import BaseAgent
import json

class QuizAgent(BaseAgent):
    def process(self, text: str, num_questions: int = 5) -> Dict:
        """Generate quiz questions from text"""
        self.retry_count = 0
        
        while self.retry_count < self.max_retries:
            try:
                if len(text.strip()) < 100:
                    self.logger.warning("Text too short for meaningful quiz generation")
                    return self._create_basic_quiz("Text too short")

                prompt = f"""Generate a quiz based on the given text.

                IMPORTANT: Your response must be ONLY valid JSON, with no additional text or explanation.
                
                Required JSON structure:
                {{
                    "topic": "Topic Title",
                    "questions": [
                        {{
                            "question": "Clear, concise question?",
                            "options": ["Option A", "Option B", "Option C", "Option D"],
                            "correct_answer": "Correct option exactly as written above",
                            "explanation": "Brief explanation of the correct answer"
                        }}
                    ]
                }}

                Requirements:
                1. Generate exactly {num_questions} questions
                2. Each question must:
                   - Be clear and concise
                   - Have exactly 4 options
                   - Include the correct answer that matches one option exactly
                   - Include a brief explanation
                3. Questions should test understanding, not just memorization
                4. All content must be based on the provided text
                5. Response must be valid JSON only
                6. Do not include any text before or after the JSON

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
                self.logger.debug(f"Raw response: {response_text[:200]}...")
                
                # Clean up the response text
                # Remove any non-JSON text before the first {
                start = response_text.find('{')
                end = response_text.rindex('}') + 1
                if start == -1 or end == -1:
                    raise ValueError("No valid JSON found in response")
                    
                response_text = response_text[start:end]
                
                # Remove any whitespace and newlines
                response_text = response_text.replace('\n', ' ').replace('\r', ' ')
                self.logger.debug(f"Cleaned response: {response_text[:200]}...")
                
                try:
                    quiz_data = json.loads(response_text)
                except json.JSONDecodeError as e:
                    self.logger.error(f"JSON decode error: {str(e)}")
                    self.logger.debug(f"Problematic JSON: {response_text}")
                    raise ValueError(f"Invalid JSON format: {str(e)}")
                
                # Validate structure
                if not isinstance(quiz_data, dict):
                    raise ValueError("Response is not a dictionary")
                
                required_keys = ["topic", "questions"]
                for key in required_keys:
                    if key not in quiz_data:
                        raise ValueError(f"Missing required key: {key}")
                
                if not isinstance(quiz_data["questions"], list):
                    raise ValueError("Questions is not a list")
                
                for question in quiz_data["questions"]:
                    required_question_keys = ["question", "options", "correct_answer", "explanation"]
                    if not all(k in question for k in required_question_keys):
                        raise ValueError("Question missing required fields")
                    if len(question["options"]) != 4:
                        raise ValueError("Question must have exactly 4 options")
                    if question["correct_answer"] not in question["options"]:
                        raise ValueError("Correct answer must match one of the options exactly")
                
                self.logger.info(f"Successfully generated quiz with {len(quiz_data['questions'])} questions")
                return quiz_data

            except Exception as e:
                if "quota" in str(e).lower():
                    self.retry_count += 1
                    try:
                        self._switch_api_key()
                        continue
                    except Exception:
                        if self.retry_count >= self.max_retries:
                            self.logger.error("All API keys exhausted")
                            return self._create_basic_quiz("API quota exceeded")
                        continue
                else:
                    self.logger.error(f"Error generating quiz: {str(e)}")
                    return self._create_basic_quiz(str(e))

    def _create_basic_quiz(self, reason: str) -> Dict:
        """Create a basic quiz structure"""
        return {
            "topic": "Basic Quiz",
            "questions": [
                {
                    "question": "Could not generate quiz questions. Reason?",
                    "options": [
                        reason,
                        "Invalid input",
                        "Technical error",
                        "Try again later"
                    ],
                    "correct_answer": reason,
                    "explanation": "The quiz generation process encountered an error."
                }
            ]
        } 