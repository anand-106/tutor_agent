from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent
import json

class QuizAgent(BaseAgent):
    def __init__(self, api_keys: list, shared_state: Optional[Dict[str, Any]] = None):
        super().__init__(api_keys, shared_state)
        self.logger.info("QuizAgent initialized")
    
    def process(self, text: str, num_questions: int = 5, topic: str = None) -> Dict:
        """Generate quiz questions from text"""
        self.retry_count = 0
        self.logger.info(f"Generating quiz with {num_questions} questions")
        
        # Use topic from shared state if available and not explicitly provided
        if topic is None and self.shared_state is not None:
            topic = self.get_shared_state_value("current_topic")
            if topic:
                self.logger.info(f"Using topic '{topic}' from shared state")
        
        while self.retry_count < self.max_retries:
            try:
                if len(text.strip()) < 100:
                    self.logger.warning("Text too short for meaningful quiz generation")
                    return self._create_basic_quiz("Text too short")

                # If we have topics in shared state, focus the quiz on the current topic
                topic_focus = ""
                if topic:
                    topic_focus = f"Focus the quiz on the topic: {topic}. "
                    self.logger.info(f"Focusing quiz on topic: {topic}")
                
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
                            "explanation": "Brief explanation of the correct answer",
                            "subtopic": "Specific subtopic this question relates to"
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
                   - Include a specific subtopic this question relates to
                3. Questions should test understanding, not just memorization
                4. All content must be based on the provided text
                5. Response must be valid JSON only
                6. Do not include any text before or after the JSON
                {topic_focus}

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
                    # Add subtopic if missing
                    if "subtopic" not in question:
                        question["subtopic"] = quiz_data["topic"]
                
                self.logger.info(f"Successfully generated quiz with {len(quiz_data['questions'])} questions on topic '{quiz_data['topic']}'")
                
                # Update shared state with the quiz topic if available
                if self.shared_state is not None:
                    self.update_shared_state("current_topic", quiz_data["topic"])
                    self.logger.info(f"Updated current_topic in shared state to '{quiz_data['topic']}'")
                    
                    # Initialize progress for this topic if not already present
                    if quiz_data["topic"] not in self.get_shared_state_value("progress", {}):
                        self.logger.info(f"Initializing progress for topic '{quiz_data['topic']}' in shared state")
                        progress = self.get_shared_state_value("progress", {})
                        progress[quiz_data["topic"]] = {
                            "score": 0,
                            "mastery": 0.0
                        }
                        self.update_shared_state("progress", progress)
                
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
    
    def process_answer(self, question_id: int, user_answer: str, quiz_data: Dict) -> Dict:
        """Process a user's answer to a quiz question and update progress"""
        self.logger.info(f"Processing answer for question {question_id}")
        
        if not quiz_data or "questions" not in quiz_data or question_id >= len(quiz_data["questions"]):
            self.logger.warning(f"Invalid question ID: {question_id}")
            return {"correct": False, "message": "Invalid question"}
        
        question = quiz_data["questions"][question_id]
        is_correct = user_answer == question["correct_answer"]
        self.logger.info(f"Answer is {'correct' if is_correct else 'incorrect'}")
        
        # Update shared state with the user's answer and progress
        if self.shared_state is not None:
            # Store the user's input
            self.update_shared_state("user_input", user_answer)
            self.logger.info(f"Updated user_input in shared state")
            
            # Update progress for this topic
            topic = quiz_data["topic"]
            subtopic = question.get("subtopic", topic)
            
            progress = self.get_shared_state_value("progress", {})
            if topic not in progress:
                self.logger.info(f"Initializing progress for topic '{topic}' in shared state")
                progress[topic] = {"score": 0, "mastery": 0.0}
            
            # Update score based on correctness
            current_score = progress[topic]["score"]
            current_mastery = progress[topic]["mastery"]
            
            if is_correct:
                # Increase score and mastery if correct
                new_score = min(current_score + 1, 10)  # Cap at 10
                new_mastery = min(current_mastery + 0.05, 1.0)  # Increase by 5%, cap at 100%
                self.logger.info(f"Increasing score for '{topic}' from {current_score} to {new_score}")
                self.logger.info(f"Increasing mastery for '{topic}' from {current_mastery:.2f} to {new_mastery:.2f}")
            else:
                # Decrease score and mastery if incorrect
                new_score = max(current_score - 1, 0)  # Don't go below 0
                new_mastery = max(current_mastery - 0.03, 0.0)  # Decrease by 3%, don't go below 0
                self.logger.info(f"Decreasing score for '{topic}' from {current_score} to {new_score}")
                self.logger.info(f"Decreasing mastery for '{topic}' from {current_mastery:.2f} to {new_mastery:.2f}")
            
            progress[topic] = {
                "score": new_score,
                "mastery": new_mastery
            }
            
            # Also track subtopic progress if different from main topic
            if subtopic != topic:
                self.logger.info(f"Updating progress for subtopic '{subtopic}'")
                if subtopic not in progress:
                    self.logger.info(f"Initializing progress for subtopic '{subtopic}' in shared state")
                    progress[subtopic] = {"score": 0, "mastery": 0.0}
                
                current_subtopic_score = progress[subtopic]["score"]
                current_subtopic_mastery = progress[subtopic]["mastery"]
                
                if is_correct:
                    new_subtopic_score = min(current_subtopic_score + 1, 10)
                    new_subtopic_mastery = min(current_subtopic_mastery + 0.05, 1.0)
                    self.logger.info(f"Increasing score for subtopic '{subtopic}' from {current_subtopic_score} to {new_subtopic_score}")
                else:
                    new_subtopic_score = max(current_subtopic_score - 1, 0)
                    new_subtopic_mastery = max(current_subtopic_mastery - 0.03, 0.0)
                    self.logger.info(f"Decreasing score for subtopic '{subtopic}' from {current_subtopic_score} to {new_subtopic_score}")
                
                progress[subtopic] = {
                    "score": new_subtopic_score,
                    "mastery": new_subtopic_mastery
                }
            
            # Update the progress in shared state
            self.update_shared_state("progress", progress)
            self.logger.info(f"Updated progress in shared state")
        
        return {
            "correct": is_correct,
            "explanation": question["explanation"],
            "correct_answer": question["correct_answer"]
        }

    def _create_basic_quiz(self, reason: str) -> Dict:
        """Create a basic quiz structure"""
        self.logger.info(f"Creating basic quiz due to: {reason}")
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
                    "explanation": "The quiz generation process encountered an error.",
                    "subtopic": "Error"
                }
            ]
        } 