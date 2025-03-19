from typing import List, Dict, Any, Optional
from .base_agent import BaseAgent
import json

class QuestionAgent(BaseAgent):
    """
    Question Agent that handles presenting options to the user and processing their selections.
    This agent can generate multiple-choice questions, present topic selections, and process the user's responses.
    """
    
    def __init__(self, api_keys: list, shared_state: Optional[Dict[str, Any]] = None):
        super().__init__(api_keys)
        self.shared_state = shared_state or {}
        self.logger.info("Initialized Question Agent")
    
    def process(self, content: str = "", question_type: str = "general", options: List[Any] = None, **kwargs) -> Dict[str, Any]:
        """
        Generate a question based on the provided content and options.
        
        Args:
            content: The content to generate a question about
            question_type: The type of question (topic_selection, multiple_choice, etc.)
            options: List of options to present to the user
            
        Returns:
            Dict containing the question and options
        """
        self.logger.info(f"Generating {question_type} question")
        
        # Process different types of questions
        if question_type == "topic_selection":
            # Ensure options are properly formatted for topic selection
            if options and isinstance(options, list):
                self.logger.info(f"Processing topic selection with {len(options)} options")
                # Log the first few options for debugging
                for i, option in enumerate(options[:2]):
                    if isinstance(option, dict):
                        opt_text = option.get('text', option.get('title', 'Unknown'))
                        self.logger.info(f"Option {i+1}: {opt_text}")
            return self._generate_topic_selection(options, **kwargs)
        elif question_type == "multiple_choice":
            return self._generate_multiple_choice(content, options, **kwargs)
        elif question_type == "confirmation":
            return self._generate_confirmation(content, **kwargs)
        else:
            return self._generate_general_question(content, **kwargs)
    
    def _generate_topic_selection(self, topics: List[Dict], title: str = "Select a Topic") -> Dict[str, Any]:
        """
        Generate a topic selection question with the given topics as options.
        
        Args:
            topics: List of topic dictionaries with at least 'title' and 'content' keys
            title: The title for the question
            
        Returns:
            Dict containing the question and options
        """
        self.logger.info(f"Generating topic selection with {len(topics)} topics")
        
        # Format the topics for presentation
        formatted_options = []
        for i, topic in enumerate(topics, 1):
            # Get the topic title from either 'text' or 'title' field
            topic_title = topic.get("text", topic.get("title", f"Topic {i}"))
            topic_content = topic.get("description", topic.get("content", ""))
            
            formatted_options.append({
                "id": str(i),
                "text": topic_title,
                "description": topic_content
            })
        
        # Create the question object
        question = {
            "type": "topic_selection",
            "title": title,
            "message": "Which topic would you like to learn about? Please select from the options below:",
            "options": formatted_options,
            "has_options": True,
            "require_response": True
        }
        
        return question
    
    def _generate_multiple_choice(self, content: str, options: List[str], 
                                question_text: str = "", 
                                correct_option: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate a multiple-choice question with the given options.
        
        Args:
            content: The content to generate a question about
            options: List of option strings
            question_text: The specific question text (if empty, will be generated from content)
            correct_option: The index of the correct option (0-based)
            
        Returns:
            Dict containing the question and options
        """
        self.logger.info("Generating multiple choice question")
        
        # Format the options for presentation
        formatted_options = []
        for i, option in enumerate(options, 1):
            formatted_options.append({
                "id": str(i),
                "text": option,
                "is_correct": (correct_option is not None and i-1 == correct_option)
            })
        
        # Use provided question text or generate a simple one
        if not question_text:
            question_text = "Please select one of the following options:"
        
        # Create the question object
        question = {
            "type": "multiple_choice",
            "title": "Question",
            "message": question_text,
            "content": content,
            "options": formatted_options,
            "has_options": True,
            "require_response": True
        }
        
        return question
    
    def _generate_confirmation(self, content: str, title: str = "Confirmation") -> Dict[str, Any]:
        """
        Generate a yes/no confirmation question.
        
        Args:
            content: The content to confirm
            title: The title for the confirmation
            
        Returns:
            Dict containing the question and yes/no options
        """
        self.logger.info("Generating confirmation question")
        
        # Format the options for presentation
        formatted_options = [
            {
                "id": "yes",
                "text": "Yes"
            },
            {
                "id": "no",
                "text": "No"
            }
        ]
        
        # Create the question object
        question = {
            "type": "confirmation",
            "title": title,
            "message": content,
            "options": formatted_options,
            "has_options": True,
            "require_response": True
        }
        
        return question
    
    def _generate_general_question(self, content: str, title: str = "Question") -> Dict[str, Any]:
        """
        Generate a general open-ended question.
        
        Args:
            content: The question content
            title: The title for the question
            
        Returns:
            Dict containing the question
        """
        self.logger.info("Generating general question")
        
        # Create the question object
        question = {
            "type": "general",
            "title": title,
            "message": content,
            "has_options": False,
            "require_response": True
        }
        
        return question
    
    def process_response(self, question: Dict[str, Any], response: str) -> Dict[str, Any]:
        """
        Process the user's response to a question.
        
        Args:
            question: The original question dict
            response: The user's response string
            
        Returns:
            Dict containing the processed response
        """
        self.logger.info(f"Processing response for question type: {question.get('type')}")
        
        question_type = question.get("type", "general")
        
        if question_type == "topic_selection":
            return self._process_topic_selection(question, response)
        elif question_type == "multiple_choice":
            return self._process_multiple_choice(question, response)
        elif question_type == "confirmation":
            return self._process_confirmation(question, response)
        else:
            return {"type": "general_response", "response": response, "processed_value": response}
            
    def _process_topic_selection(self, question: Dict[str, Any], response: str) -> Dict[str, Any]:
        """Process a topic selection response"""
        options = question.get("options", [])
        
        # Try to match the response to an option ID
        selected_option = None
        
        # First try exact ID match
        for option in options:
            if response == option.get("id"):
                selected_option = option
                break
        
        # If no match, try to parse a number from the response
        if not selected_option:
            try:
                option_id = int(response.strip())
                for option in options:
                    if option.get("id") == str(option_id):
                        selected_option = option
                        break
            except ValueError:
                pass
        
        # If still no match, try fuzzy text matching
        if not selected_option:
            response_lower = response.lower()
            for option in options:
                option_text = option.get("text", "").lower()
                if option_text in response_lower or response_lower in option_text:
                    selected_option = option
                    break
        
        # Return the processed response
        if selected_option:
            return {
                "type": "topic_selection_response",
                "selected_option": selected_option,
                "processed_value": selected_option.get("text"),
                "status": "success"
            }
        else:
            return {
                "type": "topic_selection_response",
                "processed_value": response,
                "status": "error",
                "message": "Could not match response to any topic option"
            }
    
    def _process_multiple_choice(self, question: Dict[str, Any], response: str) -> Dict[str, Any]:
        """Process a multiple-choice response"""
        options = question.get("options", [])
        
        # Try to match the response to an option ID
        selected_option = None
        
        # First try exact ID match
        for option in options:
            if response == option.get("id"):
                selected_option = option
                break
        
        # If no match, try to parse a number from the response
        if not selected_option:
            try:
                option_id = int(response.strip())
                for option in options:
                    if option.get("id") == str(option_id):
                        selected_option = option
                        break
            except ValueError:
                pass
        
        # Return the processed response
        if selected_option:
            is_correct = selected_option.get("is_correct", False)
            return {
                "type": "multiple_choice_response",
                "selected_option": selected_option,
                "processed_value": selected_option.get("text"),
                "is_correct": is_correct,
                "status": "success"
            }
        else:
            return {
                "type": "multiple_choice_response",
                "processed_value": response,
                "status": "error",
                "message": "Could not match response to any option"
            }
    
    def _process_confirmation(self, question: Dict[str, Any], response: str) -> Dict[str, Any]:
        """Process a confirmation response"""
        response_lower = response.lower()
        
        # Check for yes responses
        if response_lower in ["yes", "y", "yeah", "1"]:
            return {
                "type": "confirmation_response",
                "processed_value": "yes",
                "confirmed": True,
                "status": "success"
            }
        # Check for no responses
        elif response_lower in ["no", "n", "nope", "2"]:
            return {
                "type": "confirmation_response",
                "processed_value": "no",
                "confirmed": False,
                "status": "success"
            }
        # Couldn't determine yes/no
        else:
            return {
                "type": "confirmation_response",
                "processed_value": response,
                "status": "error",
                "message": "Could not determine if response was yes or no"
            }
            
    def generate_test_questions(self) -> Dict[str, Dict[str, Any]]:
        """Generate sample questions for testing.
        
        Returns:
            A dictionary with sample questions for each type
        """
        self.logger.info("Generating test questions")
        
        # Generate a topic selection question
        topic_question = self._generate_topic_selection(
            content="Select a topic to learn about",
            options=[
                {"id": "1", "text": "Machine Learning Basics", "description": "Introduction to ML concepts"},
                {"id": "2", "text": "Neural Networks", "description": "Deep learning fundamentals"},
                {"id": "3", "text": "Natural Language Processing", "description": "Text processing and understanding"}
            ]
        )
        
        # Generate a multiple choice question
        multiple_choice_question = self._generate_multiple_choice(
            content="What is the primary purpose of a neural network?",
            options=[
                {"id": "a", "text": "Data storage", "description": ""},
                {"id": "b", "text": "Pattern recognition", "description": ""},
                {"id": "c", "text": "Network security", "description": ""}
            ]
        )
        
        # Generate a confirmation question
        confirmation_question = self._generate_confirmation(
            content="Are you ready to continue with the lesson?",
            options=[
                {"id": "yes", "text": "Yes, continue", "description": ""},
                {"id": "no", "text": "No, I need more review", "description": ""}
            ]
        )
        
        # Generate a general question
        general_question = self._generate_general_question(
            content="What would you like to learn about next?"
        )
        
        return {
            "topic_selection": topic_question,
            "multiple_choice": multiple_choice_question,
            "confirmation": confirmation_question,
            "general": general_question
        } 