from typing import List, Dict, Any, Optional
from .base_agent import BaseAgent
from .topic_agent import TopicAgent
from .quiz_agent import QuizAgent
from .diagram_agent import DiagramAgent
from .explainer_agent import ExplainerAgent
from .flashcard_agent import FlashcardAgent
from .knowledge_tracking_agent import KnowledgeTrackingAgent
from .lesson_plan_agent import LessonPlanAgent
from .question_agent import QuestionAgent
import json
import re
import logging
import datetime
import time
import traceback

class TutorAgent(BaseAgent):
    """
    Main Tutor Agent that coordinates all other specialized agents.
    Acts as a natural teacher, maintaining conversation flow and selecting
    appropriate agents based on the context and learning needs.
    """
    
    def __init__(self, api_keys: List[str]):
        """
        Initialize the TutorAgent with all specialized agents.
        
        Args:
            api_keys: List of API keys to use for agent communication
        """
        super().__init__(api_keys)
        
        # Initialize shared state dictionary that all agents can access
        self.shared_state = {
            "topics": [],  # List of topics and subtopics identified by the Topic Extractor Agent
            "lesson_plan": None,  # Ordered list of topics to be taught, created by the Lesson Planner Agent
            "current_topic": "",  # The topic currently being taught to the user
            "progress": {},  # Dictionary where each key is a topic, and the value is another dictionary containing the user's score and mastery level
            "user_input": None,  # The most recent input from the user (e.g., answers to quiz questions or responses to flashcards)
            "rag_content": None,  # The text content of the PDF or document being used for teaching
            "current_question": None,  # The current question being asked to the user
            "teaching_mode": "exploratory",  # The current teaching mode
            "knowledge_level": 50,  # The user's knowledge level (0-100)
        }
        self.logger.info("Initialized shared state dictionary")
        
        # Initialize specialized agents
        self.logger.info("Initializing specialized agents...")
        self.topic_agent = TopicAgent(api_keys, self.shared_state)
        self.quiz_agent = QuizAgent(api_keys, self.shared_state)
        self.diagram_agent = DiagramAgent(api_keys, self.shared_state)
        self.explainer_agent = ExplainerAgent(api_keys, self.shared_state)
        self.flashcard_agent = FlashcardAgent(api_keys, self.shared_state)
        self.knowledge_tracking_agent = KnowledgeTrackingAgent(api_keys, self.shared_state)
        self.lesson_plan_agent = LessonPlanAgent(api_keys, self.shared_state)
        self.question_agent = QuestionAgent(api_keys, self.shared_state)
        
        # Initialize teaching state variables
        self.teaching_mode = "exploratory"
        self.current_topic = ""
        self.current_question = None
        self.waiting_for_question_response = False
        self.waiting_for_topic_selection = False
        self.presented_topics = []
        self.conversation_history = []
        
        # Lesson plan teaching state
        self.is_teaching_lesson_plan = False
        self.current_lesson_plan = None
        self.current_activity_index = 0
        
        # Teaching flow state
        self.is_teaching_flow = False
        self.current_flow_position = 0
        self.flow_items = []
        
        self.logger.info("Initialized Tutor Agent with all specialized agents and shared state")
    
    def process(self, query: str, context: str = "", user_id: str = "user") -> Dict[str, Any]:
        """
        Process a query and return a teaching response

        Args:
            query: The query to process
            context: Optional context/document content
            user_id: The user's ID

        Returns:
            Dict containing the teaching response and metadata
        """
        # Start timing for metrics
        start_time = time.time()
        
        self.logger.info(f"Processing query: {query}")
        
        # Check if we're in a teaching flow
        if self.is_teaching_flow:
            try:
                self.logger.info("Currently in teaching flow, processing flow interaction")
                return self._process_flow_interaction(query, context, user_id)
            except Exception as e:
                self.logger.error(f"Error in teaching flow: {str(e)}")
                traceback.print_exc()
                return self._create_fallback_response(
                    "I encountered an issue while processing your response in our learning flow. "
                    "Would you like to continue with a different approach?"
                )
                
        # Check if we're teaching a lesson plan
        if self.is_teaching_lesson_plan:
            try:
                # Check if we're in adaptive lesson mode
                if self.shared_state.get("teaching_mode") == "adaptive_lesson":
                    self.logger.info("Currently in adaptive lesson teaching mode")
                    return self._process_adaptive_lesson_interaction(query, context, user_id)
                else:
                    self.logger.info("Currently teaching lesson plan, processing lesson plan interaction")
                    return self._process_lesson_plan_interaction(query, user_id)
            except Exception as e:
                self.logger.error(f"Error in lesson plan: {str(e)}")
                traceback.print_exc()
                return self._create_fallback_response(
                    "I encountered an issue while processing your response in our lesson plan. "
                    "Would you like to continue with a different approach?"
                )
            
        # Check if we're waiting for a topic selection
        if self.waiting_for_topic_selection:
            self.logger.info("Currently waiting for topic selection")
            topic_selection_response = self._process_topic_selection(query, context, user_id)
            if topic_selection_response:
                return topic_selection_response
                
        # Check if we're waiting for a learning option selection
        if self.shared_state.get("waiting_for_learning_option", False):
            self.logger.info("Currently waiting for learning option selection")
            return self._process_learning_option(query, context, user_id)
                
        # If we reach here, we're in standard teaching mode
        
        # Check for "start flow" command specifically
        if query.lower().strip() == "start flow":
            self.logger.info("Detected 'start flow' command, starting interactive teaching flow")
            # Make sure we have topics
            topics = self.shared_state.get("topics", [])
            if not topics or len(topics) == 0:
                self.logger.warning("No topics found in shared state for teaching flow")
                return self._create_fallback_response(
                    "I don't have any topics to teach. Please upload a document or tell me what you'd like to learn about."
                )
            # Start the teaching flow
            self._track_interaction(user_id, "start_flow_command", query, {"flow_type": "all_topics"})
            return self._teach_topic_flow(user_id)
        
        # First, check if the user is asking to exit the tutor
        exit_patterns = [
            r"(?i)(?:exit|quit|leave|end|stop) (?:tutor|tutoring|teaching|lesson|conversation)",
            r"(?i)^(?:exit|quit|leave|bye|goodbye)$",
            r"(?i)i(?:'m| am) done",
            r"(?i)that(?:'s| is) all"
        ]
        
        for pattern in exit_patterns:
            if re.search(pattern, query):
                self.logger.info("User requested to exit tutoring session")
                # Reset teaching state
                self._reset_teaching_state()
                self._track_interaction(user_id, "exit", query, {})
                
                return {
                    "response": "Thank you for learning with me today! Feel free to come back anytime you have more questions or want to learn something new.",
                    "teaching_mode": "farewell"
                }
        
        # Then check if the user wants to start a new topic/lesson
        new_topic_patterns = [
            r"(?i)(?:teach|learn|tell) (?:me|us) about ([^?.,!]+)",
            r"(?i)(?:i want to|i'd like to|i would like to) learn about ([^?.,!]+)",
            r"(?i)(?:explain|describe|what is|what are|who is|who are) ([^?.,!]+)",
            r"(?i)can you (?:teach|explain|describe|tell me about) ([^?.,!]+)"
        ]
        
        for pattern in new_topic_patterns:
            match = re.search(pattern, query)
            if match:
                topic = match.group(1).strip()
                self.logger.info(f"User requested to learn about a new topic: {topic}")
                self._track_interaction(user_id, "new_topic_request", query, {"requested_topic": topic})
                
                # Return a list of relevant topics
                return self._get_topic_options(topic, context, user_id)
        
        # Next, check if the user wants to list available topics
        list_topics_patterns = [
            r"(?i)(?:what|which) topics",
            r"(?i)(?:list|show) (?:all |available |possible )?topics",
            r"(?i)what can (?:i|you|we) (?:learn|study|talk) about",
            r"(?i)what (?:do you know|can you teach)",
            r"(?i)help me choose a topic"
        ]
        
        for pattern in list_topics_patterns:
            if re.search(pattern, query):
                self.logger.info("User requested to list available topics")
                self._track_interaction(user_id, "list_topics", query, {})
                
                # Return a list of popular/available topics
                return self._get_topic_options("", context, user_id)
        
        # Check if the user wants to practice with questions
        practice_patterns = [
            r"(?i)(?:give|ask) me (?:some |a |more )?(?:practice |quiz )?questions",
            r"(?i)(?:i want to|i'd like to|i would like to|can i|could i|let me) practice",
            r"(?i)(?:quiz|test) me",
            r"(?i)let's practice"
        ]
        
        for pattern in practice_patterns:
            if re.search(pattern, query):
                self.logger.info("User requested practice questions")
                current_topic = self.shared_state.get("current_topic", "")
                
                if not current_topic:
                    # If we don't have a current topic, ask user to specify one
                    self._track_interaction(user_id, "practice_without_topic", query, {})
                    return {
                        "response": "I'd be happy to give you some practice questions. What topic would you like to practice?",
                        "teaching_mode": "topic_request"
                    }
                else:
                    # Generate practice questions for the current topic
                    self._track_interaction(user_id, "practice_request", query, {"topic": current_topic})
                    return self._generate_practice_questions(current_topic, user_id)
        
        # Analyze intent to determine how to respond to the query
        intent_result = self._analyze_query_intent(query)
        intent = intent_result.get("intent", "general_question")
        
        self.logger.info(f"Detected query intent: {intent}")
        self._track_interaction(user_id, intent, query, intent_result)
        
        if intent == "topic_request":
            # User wants to learn about a specific topic
            requested_topic = intent_result.get("topic", "")
            return self._get_topic_options(requested_topic, context, user_id)
            
        elif intent == "concept_explanation":
            # User wants an explanation of a concept
            concept = intent_result.get("concept", "")
            
            try:
                # Use the explainer agent to generate an explanation
                explanation_result = self.explainer_agent.process(
                    text=context, 
                    query=f"Explain {concept} clearly and concisely"
                )
                
                if isinstance(explanation_result, dict) and "explanation" in explanation_result:
                    explanation = explanation_result["explanation"]
                else:
                    explanation = str(explanation_result)
                
                # Check if we should generate a diagram for this concept
                has_diagram = False
                diagram_data = None
                
                if self._should_generate_diagram_for_topic(concept):
                    try:
                        self.logger.info(f"Generating diagram for {concept}")
                        diagram = self.diagram_agent.process(
                            text=explanation,
                            diagram_type="auto"
                        )
                        
                        if isinstance(diagram, dict) and "mermaid_code" in diagram:
                            has_diagram = True
                            diagram_data = diagram
                    except Exception as diagram_error:
                        self.logger.error(f"Error generating diagram: {str(diagram_error)}")
                
                # Create comprehension question
                has_question = False
                question_data = None
                
                try:
                    self.logger.info(f"Generating comprehension question for {concept}")
                    question = self.question_agent.process(
                        content=explanation,
                        question_type="comprehension"
                    )
                    
                    if question and isinstance(question, dict):
                        has_question = True
                        question_data = question
                except Exception as question_error:
                    self.logger.error(f"Error generating question: {str(question_error)}")
                
                # Create the response
                response = {
                    "response": f"# {concept}\n\n{explanation}",
                    "teaching_mode": "concept_explanation"
                }
                
                if has_diagram:
                    response["has_diagram"] = True
                    response["mermaid_code"] = diagram_data.get("mermaid_code")
                    response["diagram_type"] = diagram_data.get("diagram_type", "flowchart")
                
                if has_question:
                    response["has_question"] = True
                    response["question"] = question_data
                
                return response
                
            except Exception as e:
                self.logger.error(f"Error explaining concept {concept}: {str(e)}")
                return self._create_fallback_response(
                    f"I'm having trouble explaining {concept} at the moment. "
                    f"Could you ask in a different way or choose another topic?"
                )
                
        elif intent == "comparison_request":
            # User wants to compare concepts
            concepts = intent_result.get("concepts", [])
            if len(concepts) < 2:
                return {
                    "response": "I'd be happy to draw a comparison. Could you specify which concepts you'd like me to compare?",
                    "teaching_mode": "comparison_request"
                }
            
            concepts_str = " and ".join(concepts)
            
            try:
                # Use the explainer agent to generate a comparison
                comparison_result = self.explainer_agent.process(
                    text=context,
                    query=f"Compare and contrast {concepts_str} clearly, highlighting key similarities and differences"
                )
                
                if isinstance(comparison_result, dict) and "explanation" in comparison_result:
                    comparison = comparison_result["explanation"]
                else:
                    comparison = str(comparison_result)
                
                # Try to generate a comparison diagram
                has_diagram = False
                diagram_data = None
                
                try:
                    self.logger.info(f"Generating comparison diagram for {concepts_str}")
                    diagram = self.diagram_agent.process(
                        text=comparison,
                        diagram_type="comparison",
                        title=f"Comparison of {concepts_str}"
                    )
                    
                    if isinstance(diagram, dict) and "mermaid_code" in diagram:
                        has_diagram = True
                        diagram_data = diagram
                except Exception as diagram_error:
                    self.logger.error(f"Error generating comparison diagram: {str(diagram_error)}")
                
                # Create the response
                response = {
                    "response": f"# Comparison: {concepts_str}\n\n{comparison}",
                    "teaching_mode": "comparison"
                }
                
                if has_diagram:
                    response["has_diagram"] = True
                    response["mermaid_code"] = diagram_data.get("mermaid_code")
                    response["diagram_type"] = diagram_data.get("diagram_type", "comparison")
                
                return response
                
            except Exception as e:
                self.logger.error(f"Error comparing concepts {concepts_str}: {str(e)}")
                return self._create_fallback_response(
                    f"I'm having trouble comparing {concepts_str} at the moment. "
                    f"Could you ask in a different way or choose other concepts to compare?"
                )
        
        elif intent == "knowledge_assessment":
            # User is asking to assess their knowledge or wants a quiz
            topic = intent_result.get("topic", self.current_topic)
            
            if not topic:
                return {
                    "response": "I'd be happy to assess your knowledge with some questions. What topic would you like to focus on?",
                    "teaching_mode": "topic_request"
                }
                
            return self._generate_quiz(topic, user_id)
        
        elif intent == "example_request":
            # User wants examples of a concept
            concept = intent_result.get("concept", "")
            
            try:
                # Use the explainer agent to generate examples
                examples_result = self.explainer_agent.process(
                    text=context,
                    query=f"Provide clear, practical examples of {concept} with explanations"
                )
                
                if isinstance(examples_result, dict) and "explanation" in examples_result:
                    examples = examples_result["explanation"]
                else:
                    examples = str(examples_result)
                
                return {
                    "response": f"# Examples of {concept}\n\n{examples}",
                    "teaching_mode": "examples"
                }
                
            except Exception as e:
                self.logger.error(f"Error generating examples for {concept}: {str(e)}")
                return self._create_fallback_response(
                    f"I'm having trouble coming up with examples for {concept} at the moment. "
                    f"Could you ask in a different way or choose another topic?"
                )
                
        else:  # Default: general_question or anything else
            # Process as a general teaching question
            try:
                # If we have a current topic, use it to guide the response
                current_topic = self.shared_state.get("current_topic", "")
                
                if current_topic:
                    # Format query to reference the current topic
                    contextualized_query = f"In the context of {current_topic}, {query}"
                else:
                    contextualized_query = query
                
                # Use the explainer agent to answer the question
                answer_result = self.explainer_agent.process(
                    text=context,
                    query=contextualized_query
                )
                
                if isinstance(answer_result, dict) and "explanation" in answer_result:
                    answer = answer_result["explanation"]
                else:
                    answer = str(answer_result)
                
                # Record processing time
                processing_time = time.time() - start_time
                self.logger.info(f"Query processed in {processing_time:.2f} seconds")
                
                return {
                    "response": answer,
                    "teaching_mode": "general_question"
                }
                
            except Exception as e:
                self.logger.error(f"Error processing general question: {str(e)}")
                return self._create_fallback_response(
                    "I'm having trouble answering that question. Could you rephrase it or ask something else?"
                )
    
    def _present_topics_as_question(self) -> Dict[str, Any]:
        """
        Present the available topics as an interactive question for selection.
        
        Returns:
            Dict containing the question object with topic options
        """
        self.waiting_for_question_response = True
        self.waiting_for_topic_selection = True
        self.presented_topics = []
        
        # Get topics from shared state
        topics = self.shared_state["topics"]
        self.logger.info(f"Raw topics from shared state: {topics}")
        
        # If topics is a dictionary with a 'topics' key, extract the inner list
        if isinstance(topics, dict) and "topics" in topics:
            topics = topics["topics"]
            self.logger.info(f"Extracted topics from dictionary: {len(topics)} topics")
        
        # Ensure we have topics to present
        if not topics or len(topics) == 0:
            self.waiting_for_question_response = False
            self.waiting_for_topic_selection = False
            self.logger.warning("No topics found in shared state")
            return self._create_fallback_response(
                "I don't have any topics to present. What would you like to learn about?"
            )
            
        # Format topics for the question agent
        formatted_topics = []
        for i, topic in enumerate(topics, 1):
            # Handle different possible topic structures
            if isinstance(topic, dict):
                topic_title = topic.get("title", f"Topic {i}")
                topic_content = topic.get("content", "")
                subtopics = topic.get("subtopics", [])
                self.logger.info(f"Topic {i}: {topic_title} with {len(subtopics)} subtopics")
            else:
                # If topic is just a string
                topic_title = str(topic)
                topic_content = ""
                subtopics = []
                self.logger.info(f"Topic {i}: {topic_title} (string format)")
            
            # Store the topic in presented_topics for later reference
            self.presented_topics.append({
                "index": i,
                "title": topic_title,
                "content": topic_content,
                "subtopics": subtopics
            })
            
            # Create a concise description for the compact UI
            description = topic_content
            if len(description) > 100:
                # Truncate to 100 chars and add ellipsis
                description = description[:97] + "..."
            
            # Get first subtopic if available, for additional context
            subtopic_hint = ""
            if subtopics and len(subtopics) > 0:
                first_subtopic = subtopics[0]
                if isinstance(first_subtopic, dict) and "title" in first_subtopic:
                    subtopic_hint = f"Includes: {first_subtopic['title']}"
                elif isinstance(first_subtopic, str):
                    subtopic_hint = f"Includes: {first_subtopic}"
            
            # If no content but we have subtopics, use the subtopic hint
            if not description and subtopic_hint:
                description = subtopic_hint
            
            # Add the formatted topic to the options list
            formatted_topics.append({
                "id": str(i),
                "text": topic_title,
                "description": description
            })
        
        # Generate a topic selection question using the question agent
        self.logger.info(f"Generating question with {len(formatted_topics)} formatted topics")
        
        # Log the first few formatted topics for debugging
        for i, topic in enumerate(formatted_topics[:3]):
            self.logger.info(f"Formatted topic {i+1}: id={topic['id']}, text={topic['text']}, desc={topic['description'][:30]}...")
        
        question = self.question_agent.process(
            content=f"I have extracted {len(formatted_topics)} topics from your document. Please select one to explore.",
            question_type="topic_selection",
            options=formatted_topics,
            title="Document Topics"
        )
        
        # Save the current question
        self.current_question = question
        self.update_shared_state("current_question", question)
        
        # Log the presented topics
        self.logger.info(f"Presented {len(self.presented_topics)} topics as interactive question")
        
        # Log the question being generated
        self.logger.info(f"Generated topic selection question with type={question.get('type')}")
        
        # Return the response with the question
        intro_text = "I've analyzed the document and identified several topics. Which one would you like to learn about?"
        
        return {
            "response": intro_text,
            "question": question,
            "has_question": True,
            "teaching_mode": "topic_selection"
        }
    
    def _process_question_response(self, query: str, context: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Process a response to a previously asked question.
        
        Args:
            query: The user's response
            context: Document context
            user_id: The user's ID
            
        Returns:
            Dict containing the processed response, or None if processing should continue
        """
        if not self.current_question:
            self.waiting_for_question_response = False
            self.waiting_for_topic_selection = False
            return None
            
        # Process the response using the question agent
        processed_response = self.question_agent.process_response(self.current_question, query)
        self.logger.info(f"Processed question response: {processed_response}")
        
        # Get the question type
        question_type = self.current_question.get("type", "general")
        self.logger.info(f"Question type was: {question_type}")
        
        # Reset the question state
        self.waiting_for_question_response = False
        
        if question_type == "topic_selection":
            # For topic selection questions, keep the topic selection state active
            # until we find a valid topic
            
            # First try to get the selected option directly from the process_response result
            selected_option = processed_response.get("selected_option") 
            
            if selected_option:
                self.logger.info(f"Selected option: {selected_option}")
                selected_topic_text = selected_option.get("text", "")
                
                # Find the corresponding topic in presented_topics
                selected_topic = None
                for topic in self.presented_topics:
                    if topic["title"] == selected_topic_text:
                        selected_topic = topic
                        break
                    
                if selected_topic:
                    # Update the current topic
                    self.current_topic = selected_topic["title"]
                    self.update_shared_state("current_topic", selected_topic["title"])
                    
                    # Reset topic selection state
                    self.waiting_for_topic_selection = False
                    self.current_question = None
                    self.update_shared_state("current_question", None)
                    
                    # Generate a lesson plan for the selected topic from topic selection UI
                    lesson_plan_response = self._generate_lesson_plan_for_topic(selected_topic, user_id)
                    
                    # Add a flag to indicate this response includes a lesson plan
                    lesson_plan_response["has_lesson_plan"] = True
                    lesson_plan_response["is_from_topic_selection"] = True
                    
                    # Add a message prompting the user to access the lesson plan
                    lesson_plan_response["response"] = f"I've created a lesson plan for '{selected_topic['title']}'. You can access it by clicking the lesson plan icon, or we can start discussing this topic right away. What would you like to know about {selected_topic['title']}?"
                    
                    return lesson_plan_response
            
            # If we couldn't find the topic by option text, try by ID/index
            try:
                topic_id = query.strip()
                # Check if the ID is a number
                if topic_id.isdigit():
                    topic_index = int(topic_id) - 1
                    
                    # Check if the index is valid
                    if 0 <= topic_index < len(self.presented_topics):
                        selected_topic = self.presented_topics[topic_index]
                        
                        # Update the current topic
                        self.current_topic = selected_topic["title"]
                        self.update_shared_state("current_topic", selected_topic["title"])
                        
                        # Reset topic selection state
                        self.waiting_for_topic_selection = False
                        self.current_question = None
                        self.update_shared_state("current_question", None)
                        
                        # Generate a lesson plan for the selected topic
                        lesson_plan_response = self._generate_lesson_plan_for_topic(selected_topic, user_id)
                        
                        # Add a flag to indicate this response includes a lesson plan
                        lesson_plan_response["has_lesson_plan"] = True
                        lesson_plan_response["is_from_topic_selection"] = True
                        
                        # Add a message prompting the user to access the lesson plan
                        lesson_plan_response["response"] = f"I've created a lesson plan for '{selected_topic['title']}'. You can access it by clicking the lesson plan icon, or we can start discussing this topic right away. What would you like to know about {selected_topic['title']}?"
                        
                        return lesson_plan_response
            except Exception as e:
                self.logger.error(f"Error processing topic selection by ID: {e}")
            
            # If we get here, we couldn't find a topic by name or ID
            # Keep the topic selection state active
            self.waiting_for_question_response = True
            self.waiting_for_topic_selection = True
            
            return {
                "response": "I couldn't identify which topic you want to learn about. Please select a topic by number or name from the list above.",
                "has_question": True,
                "question": self.current_question,
                "teaching_mode": "topic_selection"
            }
        elif question_type == "multiple_choice":
            # Process multiple choice response
            pass  # Existing code
        elif question_type == "confirmation":
            # Process confirmation response
            pass  # Existing code
        
        # For other question types, reset the question state completely
        self.current_question = None
        self.update_shared_state("current_question", None)
        
        return None
    
    def _generate_lesson_plan_for_topic(self, topic: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Generate a simple lesson plan for the selected topic with just the flow of topics and subtopics.
        
        Args:
            topic: The selected topic dictionary
            user_id: The user's ID
            
        Returns:
            Dict containing the response with the simplified lesson plan
        """
        topic_title = topic["title"]
        self.logger.info(f"Generating simplified lesson plan for topic: {topic_title}")
        
        try:
            # Extract subtopics from the selected topic
            subtopics = topic.get("subtopics", [])
            
            # Create a simplified lesson plan with just topic names in flow
            simplified_lesson_plan = {
                "title": f"Lesson Plan: {topic_title}",
                "description": f"Topic flow for learning {topic_title}",
                "main_topic": topic_title,
                "topic_flow": [
                    {
                        "name": subtopic.get("title", "Untitled Subtopic"),
                        "order": idx + 1
                    } for idx, subtopic in enumerate(subtopics)
                ],
                "generated_at": datetime.datetime.now().isoformat(),
                "user_id": user_id,
                "topic": topic_title
            }
            
            # Set the generated lesson plan
            self.current_lesson_plan = simplified_lesson_plan
            self.update_shared_state("lesson_plan", simplified_lesson_plan)
            self.is_teaching_lesson_plan = True
            self.current_activity_index = 0
            
            # Create response for the user
            intro_text = f"I've created a simple learning path for {topic_title}. "
            if simplified_lesson_plan["topic_flow"]:
                intro_text += f"We'll cover {len(simplified_lesson_plan['topic_flow'])} subtopics in sequence."
            else:
                intro_text += "This topic doesn't have any subtopics defined yet."
                
            return {
                "response": intro_text,
                "has_lesson_plan": True,
                "lesson_plan": simplified_lesson_plan,
                "is_from_topic_selection": True
            }
            
        except Exception as e:
            self.logger.error(f"Error generating simplified lesson plan: {str(e)}")
            return self._create_fallback_response(
                f"I'm having trouble creating a topic flow for {topic_title}. Would you like to try another topic?"
            )
    
    def _process_topic_selection(self, query: str, context: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Process the user's selection of a topic from a list of options.
        
        Args:
            query: The user's query (selected topic)
            context: Document context
            user_id: The user's ID
            
        Returns:
            Dict containing the response with lesson plan or None if no match
        """
        # If we don't have any presented topics, there's nothing to select from
        if not hasattr(self, 'presented_topics') or not self.presented_topics:
            self.logger.warning("No presented topics available for selection")
            return None
        
        self.logger.info(f"Processing topic selection from {len(self.presented_topics)} topics")
        
        # Try to find a match for the selected topic
        selected_topic = None
        selection_number = None
        
        # Check if the selection is a number
        try:
            selection_number = int(query.strip())
            # Check if it's a valid index (1-based)
            if 1 <= selection_number <= len(self.presented_topics):
                selected_topic = self.presented_topics[selection_number - 1]
                self.logger.info(f"Selected topic by number: {selection_number}")
        except (ValueError, TypeError):
            # Not a number, try to match the text
            query_lower = query.lower().strip()
            for i, topic in enumerate(self.presented_topics):
                topic_title = topic.get("title", "")
                if topic_title.lower() in query_lower or query_lower in topic_title.lower():
                    selected_topic = topic
                    selection_number = i + 1  # 1-based index
                    self.logger.info(f"Selected topic by text: {topic_title}")
                    break
        
        if not selected_topic:
            self.logger.warning(f"No topic match found for selection: {query}")
            return None
        
        # Update the current topic
        self.current_topic = selected_topic.get("title", "Selected Topic")
        self.update_shared_state("current_topic", self.current_topic)
        
        # Offer learning options for the selected topic
        topic_title = selected_topic.get("title", "this topic")
        topic_content = selected_topic.get("content", "")
        
        # Create a prompt for learning options
        options_prompt = (
            f"I can help you learn about {topic_title} in different ways:\n\n"
            f"1. **Comprehensive Lesson Plan** - A structured learning experience with explanations, diagrams, quizzes, and activities\n"
            f"2. **Interactive Learning Flow** - A guided tutorial with interactive questions and explanations\n"
            f"3. **Quick Overview** - Just the key points without additional activities\n"
            f"4. **Personalized Adaptive Learning** - A tailored lesson that adapts to your knowledge level and asks questions to gauge understanding\n\n"
            f"How would you like to learn about {topic_title}?"
        )
        
        # Create multiple choice options
        learning_options = [
            "Comprehensive Lesson Plan",
            "Interactive Learning Flow",
            "Quick Overview",
            "Personalized Adaptive Learning"
        ]
        
        # Generate the question
        options_question = self.question_agent.process(
            content=options_prompt,
            question_type="multiple_choice",
            options=learning_options,
            title=f"Learning Options for {topic_title}"
        )
        
        # Create the learning options response
        self.update_shared_state("selected_topic", selected_topic)
        self.update_shared_state("waiting_for_learning_option", True)
        
        return {
            "response": f"Great choice! {topic_title} is an interesting topic. {topic_content}\n\nLet's determine how you'd like to learn about it.",
            "teaching_mode": "topic_selection",
            "has_question": True,
            "question": options_question,
            "is_from_topic_selection": True
        }
        
    def _process_learning_option(self, query: str, context: str, user_id: str) -> Dict[str, Any]:
        """
        Process the user's selection of a learning option after selecting a topic.
        
        Args:
            query: The user's query (selected learning option)
            context: Document context
            user_id: The user's ID
            
        Returns:
            Dict containing the response with the chosen learning approach
        """
        # Get the selected topic from shared state
        selected_topic = self.shared_state.get("selected_topic", None)
        
        if not selected_topic:
            self.logger.warning("No selected topic found in shared state")
            return self._create_fallback_response(
                "I couldn't find the topic you selected. Could you please select a topic again?"
            )
        
        # Reset the waiting flag
        self.update_shared_state("waiting_for_learning_option", False)
        
        # Determine which learning option was selected
        query_lower = query.lower().strip()
        
        if "comprehensive" in query_lower or "lesson plan" in query_lower or "1" in query_lower:
            # Generate comprehensive lesson plan
            self.logger.info(f"Generating comprehensive lesson plan for {selected_topic.get('title', 'unknown topic')}")
            return self._generate_integrated_lesson_plan(selected_topic, user_id)
            
        elif "adaptive" in query_lower or "personalized" in query_lower or "4" in query_lower:
            # Start adaptive lesson plan
            self.logger.info(f"Starting adaptive learning for {selected_topic.get('title', 'unknown topic')}")
            
            # Get user's current knowledge level
            try:
                user_knowledge = self.knowledge_tracking_agent.get_user_knowledge_summary(user_id)
                knowledge_level = user_knowledge.get("average_level", 50)
            except Exception as e:
                self.logger.error(f"Error getting user knowledge: {str(e)}")
                knowledge_level = 50  # Default to intermediate
                
            topic_title = selected_topic.get("title", "Selected Topic")
            topic_content = selected_topic.get("content", "")
            
            # Generate a lesson plan for this topic
            try:
                self.logger.info(f"Generating lesson plan for topic: {topic_title}")
                lesson_plan = self.lesson_plan_agent.process(
                    user_id=user_id, 
                    topic=topic_title,
                    knowledge_level=knowledge_level,
                    subtopics=selected_topic.get("subtopics", []),
                    time_available=60  # Default to 1 hour
                )
                
                # Set the generated lesson plan
                self.current_lesson_plan = lesson_plan
                self.update_shared_state("lesson_plan", lesson_plan)
                self.update_shared_state("current_topic", topic_title)
                
                # Start adaptive teaching
                return self._teach_adaptive_lesson_plan(user_id)
                
            except Exception as e:
                self.logger.error(f"Error generating adaptive lesson plan: {str(e)}")
                return self._create_fallback_response(
                    f"I'm having trouble creating an adaptive lesson plan for {topic_title}. Would you like to try a different approach?"
                )
            
        elif "interactive" in query_lower or "flow" in query_lower or "2" in query_lower:
            # Start interactive learning flow
            self.logger.info(f"Starting interactive learning flow for {selected_topic.get('title', 'unknown topic')}")
            # Store this single topic in the flow
            flow_topics = [selected_topic]
            self.update_shared_state("topics", flow_topics)
            return self._teach_topic_flow(user_id)
            
        elif "quick" in query_lower or "overview" in query_lower or "3" in query_lower:
            # Generate a quick overview with the explainer agent
            topic_title = selected_topic.get("title", "this topic")
            topic_content = selected_topic.get("content", "")
            
            try:
                quick_explanation = self.explainer_agent.process(
                    text=topic_content,
                    query=f"Provide a concise overview of {topic_title} highlighting just the key points"
                )
                
                if isinstance(quick_explanation, dict) and "explanation" in quick_explanation:
                    overview_content = quick_explanation["explanation"]
                else:
                    overview_content = str(quick_explanation)
                
                # Create diagram if suitable
                has_diagram = False
                diagram_data = None
                
                if self._should_generate_diagram_for_topic(topic_title):
                    try:
                        diagram = self.diagram_agent.process(text=topic_content, diagram_type="auto")
                        if isinstance(diagram, dict) and "mermaid_code" in diagram:
                            has_diagram = True
                            diagram_data = diagram
                    except Exception as e:
                        self.logger.error(f"Error generating diagram for overview: {str(e)}")
                
                # Track this interaction
                self._track_interaction(
                    user_id=user_id, 
                    intent="topic_overview",
                    query=query,
                    response={"topic": topic_title}
                )
                
                response = {
                    "response": f"# {topic_title} - Key Points\n\n{overview_content}\n\nWould you like to explore this topic in more depth with an interactive lesson?",
                    "teaching_mode": "exploratory"
                }
                
                if has_diagram:
                    response["has_diagram"] = True
                    response["mermaid_code"] = diagram_data.get("mermaid_code")
                    response["diagram_type"] = diagram_data.get("diagram_type", "flowchart")
                
                return response
                
            except Exception as e:
                self.logger.error(f"Error generating quick overview: {str(e)}")
                return self._create_fallback_response(
                    f"I encountered an issue creating a quick overview of {topic_title}. Would you like me to try a different approach?"
                )
        else:
            # Default to interactive learning flow if option is unclear
            self.logger.info(f"Unrecognized learning option, defaulting to interactive flow for {selected_topic.get('title', 'unknown topic')}")
            # Store this single topic in the flow
            flow_topics = [selected_topic]
            self.update_shared_state("topics", flow_topics)
            return self._teach_topic_flow(user_id)
    
    def set_lesson_plan(self, lesson_plan: Dict[str, Any]) -> None:
        """
        Set the current lesson plan for teaching.
        
        Args:
            lesson_plan: The lesson plan to teach
        """
        self.current_lesson_plan = lesson_plan
        self.update_shared_state("lesson_plan", lesson_plan)
        self.current_activity_index = 0
        self.logger.info(f"Set lesson plan: {lesson_plan.get('title', 'Untitled')}")
    
    def set_topics(self, topics: List[Dict]) -> None:
        """
        Set the available topics.
        
        Args:
            topics: List of topic dictionaries
        """
        self.update_shared_state("topics", topics)
        self.logger.info(f"Set {len(topics)} topics in shared state")
        
        # Reset any existing lesson plan
        self.current_lesson_plan = None
        self.is_teaching_lesson_plan = False
        self.waiting_for_topic_selection = False
        self.presented_topics = []
    
    def get_shared_state(self) -> Dict[str, Any]:
        """
        Get the shared state dictionary.
        
        Returns:
            The shared state dictionary
        """
        return self.shared_state
        
    def update_shared_state(self, key: str, value: Any) -> None:
        """
        Update a value in the shared state dictionary.
        
        Args:
            key: The key to update
            value: The new value
        """
        self.shared_state[key] = value
        self.logger.info(f"Updated {key} in shared state")
    
    def _start_lesson_plan_teaching(self, user_id: str) -> Dict[str, Any]:
        """
        Start teaching the current lesson plan.
        
        Returns:
            Dict containing the introduction to the lesson plan
        """
        if not self.current_lesson_plan:
            return self._create_fallback_response("I don't have a lesson plan to teach yet. Would you like me to create one?")
        
        # Get user knowledge from the knowledge tracking agent
        try:
            user_knowledge = self.knowledge_tracking_agent.get_user_knowledge_summary(user_id)
            knowledge_level = user_knowledge.get("average_level", 50)
            
            # Update the student knowledge level
            if knowledge_level < 30:
                self.student_knowledge_level = "beginner"
            elif knowledge_level < 70:
                self.student_knowledge_level = "intermediate"
            else:
                self.student_knowledge_level = "advanced"
                
            self.logger.info(f"User knowledge level: {self.student_knowledge_level} ({knowledge_level})")
        except Exception as e:
            self.logger.error(f"Error getting user knowledge: {str(e)}")
            # Default to intermediate if there's an error
            self.student_knowledge_level = "intermediate"
        
        # Create an introduction to the lesson plan
        lesson_plan = self.current_lesson_plan
        title = lesson_plan.get("title", "Untitled Lesson")
        description = lesson_plan.get("description", "")
        objectives = lesson_plan.get("learning_objectives", [])
        duration = lesson_plan.get("duration_minutes", 60)
        
        # Format the objectives as a bulleted list
        objectives_text = "\n".join([f"• {obj}" for obj in objectives])
        
        # Create the introduction
        introduction = f"# {title}\n\n{description}\n\n"
        introduction += f"This lesson is designed for your current knowledge level ({self.student_knowledge_level}) and will take approximately {duration} minutes.\n\n"
        introduction += "## Learning Objectives\nBy the end of this lesson, you will be able to:\n" + objectives_text + "\n\n"
        introduction += "Let's begin with the first activity. Say 'next' when you're ready to proceed, or ask questions at any time."
        
        # Track this as a study session
        self._track_interaction(user_id, "study_session", "start lesson plan", {
            "response": introduction,
            "lesson_plan": lesson_plan
        })
        
        return {
            "response": introduction,
            "lesson_plan": lesson_plan,
            "teaching_mode": "lesson_plan_introduction"
        }
    
    def _process_lesson_plan_interaction(self, query: str, context: str, user_id: str) -> Dict[str, Any]:
        """
        Process student interaction during lesson plan teaching.
        
        Args:
            query: The student's question or statement
            context: The document context
            user_id: The student's ID
            
        Returns:
            Dict containing the response
        """
        query_lower = query.lower()
        
        # Check for navigation commands
        if query_lower in ["next", "continue", "proceed", "go on"]:
            return self._move_to_next_activity(user_id)
        elif query_lower in ["previous", "back", "go back"]:
            return self._move_to_previous_activity(user_id)
        elif query_lower in ["repeat", "again"]:
            return self._repeat_current_activity(user_id)
        elif query_lower in ["stop", "exit", "end lesson", "quit"]:
            self.is_teaching_lesson_plan = False
            return {
                "response": "We've paused the lesson plan. Would you like to continue later or explore something else?",
                "teaching_mode": "exploratory"
            }
        
        # If it's a question or comment, handle it in the context of the current activity
        return self._handle_question_during_lesson(query, context, user_id)
    
    def _move_to_next_activity(self, user_id: str) -> Dict[str, Any]:
        """
        Move to the next activity in the lesson plan.
        
        Returns:
            Dict containing the next activity
        """
        if not self.current_lesson_plan or "activities" not in self.current_lesson_plan:
            self.is_teaching_lesson_plan = False
            return self._create_fallback_response("I don't have a valid lesson plan to teach. Let's talk about something else.")
        
        activities = self.current_lesson_plan.get("activities", [])
        
        # Increment the activity index
        self.current_activity_index += 1
        
        # Check if we've reached the end of the activities
        if self.current_activity_index >= len(activities):
            # We've completed all activities, move to assessment
            return self._present_lesson_assessment(user_id)
        
        # Get the current activity
        activity = activities[self.current_activity_index]
        
        # Format the activity
        activity_title = activity.get("title", f"Activity {self.current_activity_index + 1}")
        activity_type = activity.get("type", "")
        activity_description = activity.get("description", "")
        activity_duration = activity.get("duration_minutes", 10)
        
        # Format resources as a list
        resources = activity.get("resources", [])
        resources_text = ""
        if resources:
            resources_text = "\n\n## Resources\n"
            for resource in resources:
                resource_title = resource.get("title", "")
                resource_type = resource.get("type", "")
                resource_description = resource.get("description", "")
                resources_text += f"• **{resource_title}** ({resource_type}): {resource_description}\n"
        
        # Create the activity presentation
        activity_text = f"## {activity_title} ({activity_type})\n\n"
        activity_text += f"*Estimated time: {activity_duration} minutes*\n\n"
        activity_text += f"{activity_description}{resources_text}\n\n"
        
        # Add appropriate follow-up based on activity type
        if activity_type.lower() in ["quiz", "assessment", "test"]:
            # Generate a quiz related to this activity
            try:
                quiz = self.quiz_agent.process(activity_description)
                activity_text += "Let's test your understanding with a few questions:\n\n"
                return {
                    "response": activity_text,
                    "quiz": quiz,
                    "teaching_mode": "lesson_plan_quiz"
                }
            except Exception as e:
                self.logger.error(f"Error generating quiz: {str(e)}")
                activity_text += "Think about what you've learned so far. When you're ready, say 'next' to continue."
        
        elif activity_type.lower() in ["reading", "study"]:
            # For reading activities, offer to explain concepts
            activity_text += "Take your time to read through this material. If you have any questions or need clarification on any concepts, feel free to ask. Say 'next' when you're ready to continue."
        
        elif activity_type.lower() in ["exercise", "practice", "application"]:
            # For practice activities, offer guidance
            activity_text += "Try working through this exercise. If you need hints or guidance, just ask. Say 'next' when you've completed the activity."
        
        elif activity_type.lower() in ["discussion", "reflection"]:
            # For discussion activities, prompt thinking
            activity_text += "Take a moment to reflect on these points. Share your thoughts or questions when you're ready. Say 'next' to continue to the next activity when you're done."
        
        else:
            # Default prompt
            activity_text += "When you're ready to move on, say 'next'."
        
        # Track this as a study session
        self._track_interaction(user_id, "study_session", f"activity {self.current_activity_index}", {
            "response": activity_text,
            "activity": activity
        })
        
        return {
            "response": activity_text,
            "teaching_mode": "lesson_plan_activity"
        }
    
    def _move_to_previous_activity(self, user_id: str) -> Dict[str, Any]:
        """
        Move to the previous activity in the lesson plan.
        
        Returns:
            Dict containing the previous activity
        """
        if not self.current_lesson_plan or "activities" not in self.current_lesson_plan:
            self.is_teaching_lesson_plan = False
            return self._create_fallback_response("I don't have a valid lesson plan to teach. Let's talk about something else.")
        
        # Decrement the activity index, but don't go below 0
        self.current_activity_index = max(0, self.current_activity_index - 1)
        
        # Get the current activity
        activities = self.current_lesson_plan.get("activities", [])
        activity = activities[self.current_activity_index]
        
        # Format the activity (similar to _move_to_next_activity)
        activity_title = activity.get("title", f"Activity {self.current_activity_index + 1}")
        activity_type = activity.get("type", "")
        activity_description = activity.get("description", "")
        activity_duration = activity.get("duration_minutes", 10)
        
        # Format resources as a list
        resources = activity.get("resources", [])
        resources_text = ""
        if resources:
            resources_text = "\n\n## Resources\n"
            for resource in resources:
                resource_title = resource.get("title", "")
                resource_type = resource.get("type", "")
                resource_description = resource.get("description", "")
                resources_text += f"• **{resource_title}** ({resource_type}): {resource_description}\n"
        
        # Create the activity presentation
        activity_text = f"Let's go back to a previous activity.\n\n## {activity_title} ({activity_type})\n\n"
        activity_text += f"*Estimated time: {activity_duration} minutes*\n\n"
        activity_text += f"{activity_description}{resources_text}\n\n"
        activity_text += "When you're ready to move forward again, say 'next'."
        
        return {
            "response": activity_text,
            "teaching_mode": "lesson_plan_activity"
        }
    
    def _repeat_current_activity(self, user_id: str) -> Dict[str, Any]:
        """
        Repeat the current activity in the lesson plan.
        
        Returns:
            Dict containing the current activity
        """
        if not self.current_lesson_plan or "activities" not in self.current_lesson_plan:
            self.is_teaching_lesson_plan = False
            return self._create_fallback_response("I don't have a valid lesson plan to teach. Let's talk about something else.")
        
        # Get the current activity
        activities = self.current_lesson_plan.get("activities", [])
        
        # Check if we're at a valid index
        if self.current_activity_index < 0 or self.current_activity_index >= len(activities):
            self.current_activity_index = 0
        
        activity = activities[self.current_activity_index]
        
        # Format the activity (similar to _move_to_next_activity)
        activity_title = activity.get("title", f"Activity {self.current_activity_index + 1}")
        activity_type = activity.get("type", "")
        activity_description = activity.get("description", "")
        activity_duration = activity.get("duration_minutes", 10)
        
        # Format resources as a list
        resources = activity.get("resources", [])
        resources_text = ""
        if resources:
            resources_text = "\n\n## Resources\n"
            for resource in resources:
                resource_title = resource.get("title", "")
                resource_type = resource.get("type", "")
                resource_description = resource.get("description", "")
                resources_text += f"• **{resource_title}** ({resource_type}): {resource_description}\n"
        
        # Create the activity presentation
        activity_text = f"Let's review this activity again.\n\n## {activity_title} ({activity_type})\n\n"
        activity_text += f"*Estimated time: {activity_duration} minutes*\n\n"
        activity_text += f"{activity_description}{resources_text}\n\n"
        activity_text += "When you're ready to move on, say 'next'."
        
        return {
            "response": activity_text,
            "teaching_mode": "lesson_plan_activity"
        }
    
    def _present_lesson_assessment(self, user_id: str) -> Dict[str, Any]:
        """
        Present the final assessment for the lesson plan.
        
        Returns:
            Dict containing the assessment
        """
        if not self.current_lesson_plan or "assessment" not in self.current_lesson_plan:
            # No assessment in the lesson plan, wrap up the lesson
            return self._complete_lesson_plan(user_id)
        
        assessment = self.current_lesson_plan.get("assessment", {})
        assessment_type = assessment.get("type", "")
        assessment_description = assessment.get("description", "")
        assessment_criteria = assessment.get("criteria", [])
        
        # Format criteria as a list
        criteria_text = ""
        if assessment_criteria:
            criteria_text = "\n\n## Assessment Criteria\n"
            for criterion in assessment_criteria:
                criteria_text += f"• {criterion}\n"
        
        # Create the assessment presentation
        assessment_text = f"## Final Assessment ({assessment_type})\n\n"
        assessment_text += f"{assessment_description}{criteria_text}\n\n"
        
        # Generate appropriate assessment based on type
        if assessment_type.lower() in ["quiz", "test", "questions"]:
            # Generate a comprehensive quiz
            try:
                # Get the lesson content to generate a quiz
                lesson_content = self.current_lesson_plan.get("description", "")
                for activity in self.current_lesson_plan.get("activities", []):
                    lesson_content += " " + activity.get("description", "")
                
                quiz = self.quiz_agent.process(lesson_content, num_questions=5)
                assessment_text += "Let's assess your understanding with a quiz:\n\n"
                
                # Track this as a quiz
                self._track_interaction(user_id, "quiz_result", "lesson plan assessment", {
                    "response": assessment_text,
                    "quiz": quiz
                })
                
                return {
                    "response": assessment_text,
                    "quiz": quiz,
                    "teaching_mode": "lesson_plan_assessment"
                }
            except Exception as e:
                self.logger.error(f"Error generating quiz: {str(e)}")
                assessment_text += "Take some time to reflect on what you've learned in this lesson. When you're ready, say 'complete' to finish the lesson."
        
        elif assessment_type.lower() in ["project", "assignment", "task"]:
            assessment_text += "Complete this assignment to apply what you've learned. When you're done, say 'complete' to finish the lesson."
        
        elif assessment_type.lower() in ["discussion", "reflection", "review"]:
            assessment_text += "Take some time to reflect on what you've learned. Share your thoughts or any remaining questions. Say 'complete' when you're ready to finish the lesson."
        
        else:
            assessment_text += "When you've completed this assessment, say 'complete' to finish the lesson."
        
        return {
            "response": assessment_text,
            "teaching_mode": "lesson_plan_assessment"
        }
    
    def _complete_lesson_plan(self, user_id: str) -> Dict[str, Any]:
        """
        Complete the lesson plan and provide next steps.
        
        Returns:
            Dict containing the lesson completion message
        """
        if not self.current_lesson_plan:
            self.is_teaching_lesson_plan = False
            return self._create_fallback_response("I don't have a valid lesson plan to complete. Let's talk about something else.")
        
        # Get the next steps from the lesson plan
        next_steps = self.current_lesson_plan.get("next_steps", [])
        
        # Format next steps as a list
        next_steps_text = ""
        if next_steps:
            next_steps_text = "\n\n## Next Steps\nTo continue your learning journey:\n"
            for step in next_steps:
                next_steps_text += f"• {step}\n"
        
        # Create the completion message
        title = self.current_lesson_plan.get("title", "Untitled Lesson")
        completion_text = f"## Congratulations!\n\nYou've completed the lesson on '{title}'.\n\n"
        completion_text += "I hope you found this lesson valuable and informative. You've made great progress in understanding this topic."
        completion_text += next_steps_text + "\n\n"
        completion_text += "Would you like to explore another topic or have any questions about what we've covered?"
        
        # Reset the lesson plan state
        self.is_teaching_lesson_plan = False
        
        # Track this as a completed study session
        self._track_interaction(user_id, "study_session", "complete lesson plan", {
            "response": completion_text,
            "lesson_plan": self.current_lesson_plan
        })
        
        return {
            "response": completion_text,
            "teaching_mode": "exploratory"
        }
    
    def _handle_question_during_lesson(self, query: str, context: str, user_id: str) -> Dict[str, Any]:
        """
        Handle a question or comment during the lesson.
        
        Args:
            query: The student's question or statement
            context: The document context
            user_id: The student's ID
            
        Returns:
            Dict containing the response
        """
        # Analyze the query to determine intent and required agents
        intent, required_agents = self._analyze_query(query, context)
        
        # Get the current activity context
        activity_context = ""
        if self.current_lesson_plan and "activities" in self.current_lesson_plan:
            activities = self.current_lesson_plan.get("activities", [])
            if 0 <= self.current_activity_index < len(activities):
                activity = activities[self.current_activity_index]
                activity_title = activity.get("title", "")
                activity_description = activity.get("description", "")
                activity_context = f"{activity_title}: {activity_description}"
        
        # Combine the document context with the activity context
        combined_context = context
        if activity_context:
            combined_context = activity_context + "\n\n" + context
        
        # Generate a response based on the intent and required agents
        response = self._generate_response(intent, required_agents, combined_context, query, user_id)
        
        # Add a reminder about the lesson plan
        response["response"] += "\n\nTo continue with the lesson, say 'next' when you're ready."
        
        return response
    
    def _analyze_query(self, query, context=None):
        """
        Analyze the query to determine the intent.
        
        Args:
            query (str): The user's query.
            context (str, optional): The context for the query, such as previous messages. Defaults to None.
            
        Returns:
            tuple: A tuple containing the intent and required agents.
        """
        # Intent patterns
        intent_patterns = {
            "greeting": r"(?i)^(hello|hi|hey|greetings|howdy)[\s\.\,\!\?]*$",
            "how_are_you": r"(?i)^(how are you|how('s| is) it going|how('s| are) you doing|how do you do|what('s| is) up)[\s\.\,\!\?]*$",
            "gratitude": r"(?i)^(thank you|thanks|thank)[\s\.\,\!\?]*$",
            "request_quiz": r"(?i)(quiz|test|assessment|evaluate|examination|check|verify).*?(knowledge|learning|understanding|concepts?|comprehension|retention)",
            "request_flashcards": r"(?i)(create|make|prepare|generate|give me|provide|show|display|get|give|i want|can you|could you).*?(flashcards?|flash cards?|study cards?|memory cards?|review cards?|learning cards?)",
            "request_diagram": r"(?i)(create|make|draw|show|visualize|illustrate|diagram|graph|chart|map|sketch|plot).*?(diagram|flowchart|chart|graph|visualization|illustration|map|plot|sketch)",
            "explain_concept": r"(?i)(explain|clarify|tell me about|describe|elaborate on|what is|define|expound upon|elucidate|summarize|break down|simplify)",
            "feedback": r"(?i)(good|great|excellent|awesome|amazing|fantastic|wonderful|perfect|nice|well done|bad|terrible|awful|poor|horrible|wrong|incorrect|mistake|error|not right|could be better)",
            "refocus": r"(?i)(refocus|let's refocus|focus on|back to|return to|let's get back to|continue with|let's continue|proceed with|move on to)",
            "goodbye": r"(?i)^(goodbye|bye|see you|farewell|later|so long|au revoir)[\s\.\,\!\?]*$",
            "thanks_and_goodbye": r"(?i)(thank you|thanks).*?(goodbye|bye|see you|farewell|later)",
            "check_progress": r"(?i)(progress|how am i doing|status|standing|performance|advancement|development|improvement|growth)",
        }
        
        # Check the intent
        intent = "general_question"  # Default intent
        for intent_name, pattern in intent_patterns.items():
            if re.search(pattern, query):
                intent = intent_name
                self.logger.info(f"Intent detected: {intent}")
                break
        
        # If no specific intent was found, check if it's a flashcard request outside standard patterns
        if intent == "general_question":
            if any(keyword in query.lower() for keyword in ["flashcard", "flash card", "study card", "memory card", "review card"]):
                intent = "request_flashcards"
                self.logger.info(f"Intent updated to: {intent} based on flashcard keywords")
        
        # Determine required agents based on intent
        required_agents = []
        
        if intent == "request_quiz":
            required_agents = ["quiz"]
        elif intent == "request_flashcards":
            required_agents = ["flashcard"]
        elif intent == "request_diagram":
            required_agents = ["diagram"]
        elif intent == "explain_concept":
            required_agents = ["explainer"]
        elif intent == "check_progress":
            required_agents = ["knowledge_tracking"]
        elif intent in ["greeting", "how_are_you", "gratitude", "goodbye", "feedback", "refocus", "thanks_and_goodbye"]:
            # No additional agents required for these intents
            required_agents = []
        else:
            # For general questions, use the explainer
            required_agents = ["explainer"]
            
            # Check for specific words that might indicate a diagram would be helpful
            diagram_keywords = ["visualize", "diagram", "sketch", "draw", "illustration", "chart", "graph", "flow", "map", "picture", "visual"]
            if any(keyword in query.lower() for keyword in diagram_keywords) and "flashcard" not in query.lower():
                # Only add diagram if flashcard is not mentioned, prioritizing flashcard over diagram
                required_agents.append("diagram")
        
        return intent, required_agents
    
    def _update_teaching_mode(self, intent: str):
        """Update the teaching mode based on the detected intent"""
        if intent in ["request_quiz", "request_flashcards"]:
            self.teaching_mode = "assessment"
        elif intent in ["request_explanation", "question", "request_example"]:
            self.teaching_mode = "focused"
        elif intent in ["request_summary", "request_lesson_plan", "topic_change"]:
            self.teaching_mode = "exploratory"
    
    def _generate_response(self, intent: str, required_agents: List[str], 
                          context: str, query: str, user_id: str) -> Dict[str, Any]:
        """
        Generate a comprehensive response using the required agents.
        
        Returns:
            Dict containing the response and any additional data
        """
        response_parts = []
        additional_data = {}
        
        # Handle greeting intent
        if intent == "greeting":
            greeting_response = self._generate_greeting()
            response_parts.append(greeting_response)
            
            # If we have context, add a topic introduction
            if len(context.strip()) > 100:
                topics = self.topic_agent.process(context)
                if isinstance(topics, dict) and "topics" in topics and len(topics["topics"]) > 0:
                    self.current_topic = topics["title"]
                    self.update_shared_state("current_topic", topics["title"])
                    self.update_shared_state("topics", topics["topics"])
                    intro = f"We're currently looking at {topics['title']}. Would you like me to explain any specific part of it?"
                    response_parts.append(intro)
            
        # Handle feedback intent
        elif intent == "feedback":
            feedback_response = self._generate_feedback_response(query)
            response_parts.append(feedback_response)
            
        # Process each required agent
        for agent in required_agents:
            if agent == "explainer":
                try:
                    explanation = self.explainer_agent.process(
                        text=context,
                        query=query
                    )
                    if isinstance(explanation, dict):
                        response_text = self._format_explanation(explanation, self.teaching_mode)
                        response_parts.append(response_text)
                    else:
                        response_parts.append(str(explanation))
                except Exception as e:
                    self.logger.error(f"Error using explainer agent: {str(e)}")
                    response_parts.append("I'm having trouble generating an explanation right now.")
            elif agent == "quiz":
                try:
                    quiz = self.quiz_agent.process(context)
                    if isinstance(quiz, dict):
                        # Add a natural introduction to the quiz
                        quiz_intro = f"Let's test your understanding of {quiz.get('topic', 'this topic')} with a few questions:"
                        response_parts.append(quiz_intro)
                        additional_data["quiz"] = quiz
                    else:
                        response_parts.append(str(quiz))
                except Exception as e:
                    self.logger.error(f"Error using quiz agent: {str(e)}")
                    response_parts.append("I'm having trouble generating a quiz right now.")
            elif agent == "flashcard":
                try:
                    flashcards = self.flashcard_agent.process(context)
                    if isinstance(flashcards, dict):
                        # Add a natural introduction to the flashcards
                        flashcard_intro = f"I've created some flashcards to help you memorize key points about {flashcards.get('topic', 'this topic')}:"
                        response_parts.append(flashcard_intro)
                        additional_data["flashcards"] = flashcards
                    else:
                        response_parts.append(str(flashcards))
                except Exception as e:
                    self.logger.error(f"Error using flashcard agent: {str(e)}")
                    response_parts.append("I'm having trouble generating flashcards right now.")
            elif agent == "diagram":
                try:
                    # Determine the most appropriate diagram type
                    diagram_type = self._determine_diagram_type(query, context)
                    diagram = self.diagram_agent.process(text=context, diagram_type=diagram_type)
                    if isinstance(diagram, dict):
                        # Add a natural introduction to the diagram
                        diagram_intro = f"Here's a visual representation to help you understand better:"
                        response_parts.append(diagram_intro)
                        additional_data["diagram"] = diagram
                        additional_data["has_diagram"] = True
                        additional_data["mermaid_code"] = diagram.get("mermaid_code", "")
                        additional_data["diagram_type"] = diagram.get("diagram_type", "flowchart")
                    else:
                        response_parts.append(str(diagram))
                except Exception as e:
                    self.logger.error(f"Error using diagram agent: {str(e)}")
                    response_parts.append("I'm having trouble generating a diagram right now.")
                
        # If no response parts were generated, create a fallback response
        if not response_parts:
            response_parts.append("I understand you're asking about this topic. Could you please be more specific about what you'd like to learn?")
        
        # Combine all response parts into a cohesive response
        combined_response = " ".join(response_parts)
        
        # Create the final response object
        response_obj = {
            "response": combined_response,
            **additional_data
        }
        
        return response_obj
        
    def _should_generate_diagram_for_topic(self, topic_name: str) -> bool:
        """
        Determine if a diagram would be helpful for a given topic.
        
        Args:
            topic_name: The name of the topic
            
        Returns:
            Boolean indicating whether a diagram should be generated
        """
        # Topics that are often well-represented with diagrams
        diagram_friendly_topics = [
            "architecture", "flow", "process", "cycle", "system", "network",
            "hierarchy", "structure", "relationship", "model", "framework",
            "design", "algorithm", "data structure", "workflow", "neural",
            "circuit", "machine learning", "deep learning", "classification",
            "neural network", "decision tree", "clustering", "sequence",
            "pipeline", "architecture", "stack", "layer", "protocol"
        ]
        
        # Check if the topic matches any of the diagram-friendly keywords
        topic_lower = topic_name.lower()
        for keyword in diagram_friendly_topics:
            if keyword in topic_lower:
                return True
                
        return False

    def _teach_topic_flow(self, user_id: str) -> Dict[str, Any]:
        """
        Start an interactive teaching session that covers all topics in sequence.
        
        This creates a structured flow through topics and subtopics, allowing
        the user to navigate with commands like 'next', 'previous', and 'list topics'.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dict containing the introduction to the teaching flow
        """
        try:
            self.logger.info("Starting interactive teaching flow")
            
            # Get available topics
            topics = self.shared_state.get("topics", [])
            
            if not topics or len(topics) == 0:
                self.logger.warning("No topics found in shared state for teaching flow")
                return self._create_fallback_response(
                    "I don't have any topics to teach. Please upload a document or tell me what you'd like to learn about."
                )
                
            # Set up current topic and flow position
            self.current_topic = topics[0].get("title", "Topic 1") if isinstance(topics[0], dict) else str(topics[0])
            self.update_shared_state("current_topic", self.current_topic)
            self.update_shared_state("teaching_mode", "dynamic_flow")
            self.update_shared_state("waiting_for_flow_input", True)
            self.update_shared_state("flow_position", 0)
            
            # Create a flow structure with all topics and their subtopics
            flow_items = []
            for i, topic in enumerate(topics):
                if isinstance(topic, dict):
                    # Add the main topic as a flow item
                    flow_items.append({
                        "id": f"topic_{i}",
                        "type": "topic",
                        "title": topic.get("title", f"Topic {i+1}"),
                        "content": topic.get("content", ""),
                        "parent_id": None,
                        "order": i
                    })
                    
                    # Add all subtopics
                    subtopics = topic.get("subtopics", [])
                    for j, subtopic in enumerate(subtopics):
                        if isinstance(subtopic, dict):
                            flow_items.append({
                                "id": f"topic_{i}_subtopic_{j}",
                                "type": "subtopic",
                                "title": subtopic.get("title", f"Subtopic {j+1}"),
                                "content": subtopic.get("content", ""),
                                "parent_id": f"topic_{i}",
                                "order": j
                            })
                        else:
                            # Handle string subtopics
                            flow_items.append({
                                "id": f"topic_{i}_subtopic_{j}",
                                "type": "subtopic",
                                "title": str(subtopic),
                                "content": "",
                                "parent_id": f"topic_{i}",
                                "order": j
                            })
                else:
                    # Handle string topics
                    flow_items.append({
                        "id": f"topic_{i}",
                        "type": "topic",
                        "title": str(topic),
                        "content": "",
                        "parent_id": None,
                        "order": i
                    })
            
            # Store the flow in shared state
            self.update_shared_state("flow_items", flow_items)
            
            # Generate introduction content
            intro_text = (
                "Starting an interactive learning flow covering all topics. "
                "You can use \"next\", \"previous\", or \"list topics\" commands to navigate. "
                "Ask questions at any time, and I'll provide detailed explanations. "
                "Let's begin with the first topic."
            )
            
            # Generate content for the first flow item
            if flow_items:
                first_item = flow_items[0]
                
                try:
                    content_response = self._generate_flow_content(first_item, user_id)
                    
                    # Track this interaction
                    self._track_interaction(
                        user_id=user_id,
                        intent="flow_start",
                        query="start flow",
                        response={"flow": True, "topic": first_item.get("title", "")}
                    )
                    
                    # Properly merge the content response with our flow response
                    response = {
                        "teaching_mode": "dynamic_flow",
                        "flow_structure": {
                            "items": flow_items,
                            "current_position": 0
                        },
                        "waiting_for_flow_input": True
                    }
                    
                    # Add intro text to the content response
                    if isinstance(content_response, dict):
                        # Check if content_response has valid response text or contains error/JSON
                        content_text = content_response.get("response", "")
                        
                        # Check if the content text is a JSON string or contains JSON error markers
                        if (isinstance(content_text, str) and 
                            (content_text.strip().startswith('{') and content_text.strip().endswith('}')) or
                            "{'title':" in content_text or '{"title":' in content_text):
                            
                            self.logger.warning("Detected JSON in content response, using fallback text")
                            # Use a fallback message instead of the raw JSON
                            content_response["response"] = f"Let's explore {first_item.get('title', 'this topic')}. What specific aspects would you like to learn about?"
                        
                        # Prepend the intro text to the response text
                        content_response["response"] = intro_text + "\n\n" + content_response.get("response", "")
                        
                        # Merge other fields from content_response into the response
                        for key, value in content_response.items():
                            response[key] = value
                    else:
                        # Fallback in case content_response is not a dict
                        response["response"] = intro_text + "\n\nLet's explore " + first_item.get("title", "the topic") + "."
                    
                    return response
                    
                except Exception as e:
                    self.logger.error(f"Error in _teach_topic_flow while generating content: {str(e)}")
                    traceback.print_exc()
                    
                    # Provide a graceful recovery response
                    return {
                        "response": f"{intro_text}\n\nI'm preparing content about {first_item.get('title', 'this topic')}. What specific aspects would you like to learn about?",
                        "teaching_mode": "dynamic_flow",
                        "flow_structure": {
                            "items": flow_items,
                            "current_position": 0
                        },
                        "waiting_for_flow_input": True
                    }
            else:
                return self._create_fallback_response(
                    "I've prepared a learning flow, but there seems to be an issue with the content. Let's start with a specific question instead."
                )
                
        except Exception as e:
            self.logger.error(f"Error in _teach_topic_flow: {str(e)}")
            traceback.print_exc()
            return self._create_fallback_response(
                "I encountered an issue while preparing the learning flow. Let's try a different approach - what would you like to learn about specifically?"
            )
    
    def _process_flow_interaction(self, query: str, context: str, user_id: str) -> Dict[str, Any]:
        """
        Process user interaction during the teaching flow, integrating all agents dynamically.
        
        Args:
            query: The user's query or command
            context: Document context
            user_id: The user's ID
            
        Returns:
            Dict containing the response
        """
        query_lower = query.lower().strip()
        flow_items = self.shared_state.get("flow_items", [])
        current_position = self.shared_state.get("flow_position", 0)
        current_item = flow_items[current_position] if flow_items and current_position < len(flow_items) else None
        
        # Check if we're in quiz mode
        quiz_mode = self.shared_state.get("quiz_mode", False)
        current_quiz = self.shared_state.get("current_quiz", None)
        
        # Check if this is a response to a question
        current_question = self.shared_state.get("current_question", None)
        
        # If in quiz mode and have a current question, process quiz response
        if quiz_mode and current_question and current_quiz:
            self.logger.info(f"Processing quiz response for question {current_quiz.get('current_question_index', 0) + 1}/{current_quiz.get('total_questions', 0)}")
            
            try:
                # Process the response using the question agent
                processed_response = self.question_agent.process_response(current_question, query)
                
                # Get quiz info
                question_index = current_quiz.get("current_question_index", 0)
                total_questions = current_quiz.get("total_questions", 0)
                topic = current_quiz.get("topic", current_item.get("title", "this topic") if current_item else "this topic")
                questions = current_quiz.get("questions", [])
                
                # Check if response is correct
                is_correct = False
                explanation = ""
                
                if processed_response.get("is_correct") is not None:
                    is_correct = processed_response.get("is_correct")
                    
                    if is_correct:
                        current_quiz["correct_answers"] = current_quiz.get("correct_answers", 0) + 1
                
                if question_index < len(questions):
                    explanation = questions[question_index].get("explanation", "")
                
                # Track the quiz interaction
                self._track_interaction(
                    user_id=user_id,
                    intent="quiz_answer",
                    query=query,
                    response={
                        "topic": topic,
                        "question_index": question_index,
                        "is_correct": is_correct,
                        "total_correct": current_quiz.get("correct_answers", 0)
                    }
                )
                
                # Update quiz state
                current_quiz["current_question_index"] = question_index + 1
                self.update_shared_state("current_quiz", current_quiz)
                
                # Check if we've completed the quiz
                if question_index + 1 >= total_questions:
                    # Quiz complete - prepare summary
                    correct_answers = current_quiz.get("correct_answers", 0)
                    score = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
                    
                    # Get feedback from explainer agent based on score
                    try:
                        feedback_prompt = f"Provide feedback for a student who scored {score:.0f}% on a quiz about {topic} (got {correct_answers} out of {total_questions} questions correct)."
                        feedback = self.explainer_agent.process(text=feedback_prompt, query=feedback_prompt)
                        
                        if isinstance(feedback, dict) and "explanation" in feedback:
                            feedback_text = feedback["explanation"]
                        else:
                            feedback_text = str(feedback)
                    except Exception as e:
                        self.logger.error(f"Error getting quiz feedback: {str(e)}")
                        feedback_text = f"You answered {correct_answers} out of {total_questions} questions correctly."
                    
                    # Clear quiz mode
                    self.update_shared_state("quiz_mode", False)
                    self.update_shared_state("current_question", None)
                    
                    # Provide response with result and options to continue
                    result_text = (
                        f"## Quiz Results: {topic}\n\n"
                        f"You scored {score:.0f}% ({correct_answers}/{total_questions} correct)\n\n"
                        f"{feedback_text}\n\n"
                    )
                    
                    # Create follow-up options
                    options = [
                        "Continue to the next topic",
                        "Review this topic again",
                        "Get a deeper explanation of this topic",
                        "See a diagram of key concepts"
                    ]
                    
                    follow_up_question = self.question_agent.process(
                        content="Choose what to do next",
                        question_type="multiple_choice",
                        options=options
                    )
                    
                    # Set the question in shared state
                    self.update_shared_state("current_question", follow_up_question)
                    
                    return {
                        "response": result_text,
                        "has_question": True,
                        "question": follow_up_question,
                        "teaching_mode": "dynamic_flow",
                        "flow_structure": {
                            "items": flow_items,
                            "current_position": current_position
                        },
                        "quiz_result": {
                            "score": score,
                            "correct": correct_answers,
                            "total": total_questions,
                            "topic": topic
                        },
                        "waiting_for_flow_input": True
                    }
                else:
                    # Move to next question
                    next_question = questions[question_index + 1] if question_index + 1 < len(questions) else None
                    
                    # Prepare response with feedback on current answer
                    answer_feedback = ""
                    if is_correct:
                        answer_feedback = f"Correct! {explanation}"
                    else:
                        answer_feedback = f"The answer is not quite right. {explanation}"
                    
                    # Set next question in shared state
                    if next_question:
                        self.update_shared_state("current_question", next_question)
                        
                        return {
                            "response": answer_feedback,
                            "has_question": True,
                            "question": next_question,
                            "teaching_mode": "dynamic_flow",
                            "quiz_mode": True,
                            "quiz_info": {
                                "topic": topic,
                                "current_question": question_index + 2,  # 1-indexed for display
                                "total_questions": total_questions
                            },
                            "flow_structure": {
                                "items": flow_items,
                                "current_position": current_position
                            },
                            "waiting_for_flow_input": True
                        }
                
            except Exception as e:
                self.logger.error(f"Error processing quiz response: {str(e)}")
                # Clear quiz mode on error
                self.update_shared_state("quiz_mode", False)
                self.update_shared_state("current_question", None)
                
                return {
                    "response": f"I encountered an issue processing your quiz response. Let's continue with our exploration of {current_item.get('title', 'the topic') if current_item else 'the topic'}.",
                    "teaching_mode": "dynamic_flow",
                    "flow_structure": {
                        "items": flow_items,
                        "current_position": current_position
                    },
                    "waiting_for_flow_input": True
                }
        
        # Process other question responses (non-quiz)
        elif current_question:
            self.logger.info(f"Processing response to question with type: {current_question.get('type', 'unknown')}")
            
            # Process the response using the question agent
            try:
                processed_response = self.question_agent.process_response(current_question, query)
                self.logger.info(f"Processed question response: {processed_response}")
                
                # Get the question type
                question_type = current_question.get("type", "general")
                
                # Handle comprehension question response
                if question_type == "multiple_choice" and "selected_option" in processed_response:
                    selected_option = processed_response.get("selected_option", {})
                    selection_text = selected_option.get("text", "")
                    
                    # Log the student's comprehension level for knowledge tracking
                    self.logger.info(f"Student comprehension for {self.current_topic}: {selection_text}")
                    
                    # Track this interaction
                    self._track_interaction(
                        user_id=user_id,
                        intent="comprehension_check",
                        query=query,
                        response={"comprehension_level": selection_text, "topic": self.current_topic}
                    )
                    
                    # Provide an appropriate response based on their comprehension level
                    if "completely" in selection_text.lower():
                        response_text = f"Great! I'm glad you've understood {self.current_topic} so well. Let's build on this knowledge."
                    elif "most" in selection_text.lower():
                        response_text = f"Good progress! For any parts of {self.current_topic} you're still unsure about, feel free to ask specific questions."
                    elif "confused" in selection_text.lower():
                        response_text = f"Thank you for sharing that. Let me help clarify the key points of {self.current_topic} in a different way."
                        # Get a simpler explanation from the explainer agent
                        try:
                            simple_explanation = self.explainer_agent.process(
                                text=context,
                                query=f"Explain {self.current_topic} in simpler terms"
                            )
                            if isinstance(simple_explanation, dict) and "explanation" in simple_explanation:
                                response_text += "\n\n" + simple_explanation["explanation"]
                        except Exception as e:
                            self.logger.error(f"Error getting simpler explanation: {str(e)}")
                    elif "simpler" in selection_text.lower():
                        response_text = f"I'll give you a more straightforward explanation of {self.current_topic}."
                        # Get a much simpler explanation from the explainer agent
                        try:
                            simple_explanation = self.explainer_agent.process(
                                text=context,
                                query=f"Explain {self.current_topic} in very simple terms as if to a beginner"
                            )
                            if isinstance(simple_explanation, dict) and "explanation" in simple_explanation:
                                response_text += "\n\n" + simple_explanation["explanation"]
                        except Exception as e:
                            self.logger.error(f"Error getting simpler explanation: {str(e)}")
                    else:
                        response_text = f"Thank you for your feedback on understanding {self.current_topic}. Let's continue our exploration."
                    
                    # Clear the current question
                    self.update_shared_state("current_question", None)
                    
                    # Provide follow-up actions
                    response_text += "\n\nWould you like to:\n\n"
                    response_text += "1. Continue to the next topic\n"
                    response_text += "2. Review this topic with some practice questions\n"
                    response_text += "3. See a different explanation of this concept"
                    
                    # Create interactive question for the follow-up
                    follow_up_options = [
                        "Continue to next topic",
                        "Practice with quiz questions",
                        "Show a different explanation",
                        "Show related diagrams or visuals"
                    ]
                    
                    follow_up_question = self.question_agent.process(
                        content="Choose your next action",
                        question_type="multiple_choice",
                        options=follow_up_options
                    )
                    
                    # Update the current question
                    self.update_shared_state("current_question", follow_up_question)
                    
                    return {
                        "response": response_text,
                        "teaching_mode": "dynamic_flow",
                        "has_question": True,
                        "question": follow_up_question,
                        "flow_structure": {
                            "items": flow_items,
                            "current_position": current_position
                        },
                        "waiting_for_flow_input": True
                    }
                
                # Handle follow-up question response
                if question_type == "multiple_choice" and "selected_option" in processed_response:
                    selected_option = processed_response.get("selected_option", {})
                    selection_text = selected_option.get("text", "")
                    
                    # Clear the current question
                    self.update_shared_state("current_question", None)
                    
                    if "next topic" in selection_text.lower():
                        # Move to the next flow item
                        return self._move_to_next_flow_item(user_id, current_position, flow_items)
                    elif "quiz" in selection_text.lower() or "practice" in selection_text.lower():
                        # Generate practice questions
                        return self._generate_practice_questions(user_id, current_position, flow_items)
                    elif "explanation" in selection_text.lower() or "different" in selection_text.lower():
                        # Generate alternative explanation
                        return self._generate_alternative_explanation(user_id, current_position, flow_items)
                    elif "diagram" in selection_text.lower() or "visual" in selection_text.lower():
                        # Generate or show diagrams
                        return self._generate_visual_content(user_id, current_position, flow_items)
                    else:
                        # Default to continuing with the flow
                        return self._move_to_next_flow_item(user_id, current_position, flow_items)
                
            except Exception as e:
                self.logger.error(f"Error processing question response: {str(e)}")
                # Clear the current question to avoid getting stuck
                self.update_shared_state("current_question", None)
        
        # Handle standard navigation commands
        if query_lower in ["next", "continue", "forward", "go on", "proceed"]:
            # Move to the next flow item
            return self._move_to_next_flow_item(user_id, current_position, flow_items)
                
        elif query_lower in ["previous", "back", "backward", "go back"]:
            # Move to the previous flow item
            if current_position > 0:
                current_position -= 1
                self.update_shared_state("flow_position", current_position)
                current_item = flow_items[current_position]
                
                # Generate content for the current item
                content = self._generate_flow_content(current_item, user_id)
                
                return content
            else:
                # We're already at the beginning
                return {
                    "response": "We're at the beginning of the learning flow. You can explore this topic further or move forward to the next one.",
                    "teaching_mode": "dynamic_flow",
                    "flow_structure": {
                        "items": flow_items,
                        "current_position": current_position
                    },
                    "waiting_for_flow_input": True
                }
                
        elif query_lower in ["list topics", "show topics", "topics", "list", "overview"]:
            # List all main topics
            topic_list = ""
            current_item = flow_items[current_position]
            
            for i, item in enumerate(flow_items):
                if item["type"] == "topic":
                    marker = "→ " if i == current_position else "  "
                    topic_list += f"{marker}{item['title']}\n"
            
            return {
                "response": f"Here are all the topics in this learning flow:\n\n{topic_list}\nWe are currently on: {current_item['title']}",
                "teaching_mode": "dynamic_flow",
                "flow_structure": {
                    "items": flow_items,
                    "current_position": current_position
                },
                "waiting_for_flow_input": True
            }
        
        elif query_lower in ["quiz me", "test my knowledge", "practice questions", "ask me questions", "quiz"]:
            # Generate practice questions for the current topic
            # Set quiz mode flag
            self.update_shared_state("quiz_mode", True)
            return self._generate_practice_questions(user_id, current_position, flow_items)
            
        elif query_lower in ["show flashcards", "flashcards", "review key points", "cards"]:
            # Generate flashcards for the current topic
            return self._generate_flashcards(user_id, current_position, flow_items)
            
        elif query_lower in ["explain", "explain more", "more detail", "tell me more", "elaborate"]:
            # Get a more detailed explanation using the explainer agent
            if current_item:
                try:
                    detailed_explanation = self.explainer_agent.process(
                        text=current_item.get("content", current_item.get("title", "")),
                        query=f"Provide a more detailed explanation of {current_item.get('title', 'this topic')}"
                    )
                    
                    if isinstance(detailed_explanation, dict) and "explanation" in detailed_explanation:
                        explanation_text = detailed_explanation["explanation"]
                    else:
                        explanation_text = str(detailed_explanation)
                        
                    return {
                        "response": f"## More About {current_item.get('title', 'This Topic')}\n\n{explanation_text}",
                        "teaching_mode": "dynamic_flow",
                        "flow_structure": {
                            "items": flow_items,
                            "current_position": current_position
                        },
                        "waiting_for_flow_input": True
                    }
                except Exception as e:
                    self.logger.error(f"Error getting detailed explanation: {str(e)}")
            
        elif query_lower in ["show diagram", "diagram", "visualize", "visual"]:
            # Generate a diagram using the diagram agent
            return self._generate_visual_content(user_id, current_position, flow_items)
            
        elif query_lower in ["exit flow", "stop flow", "end flow", "quit flow", "exit", "stop", "quit"]:
            # Exit the flow
            self.update_shared_state("teaching_mode", "exploratory")
            self.update_shared_state("waiting_for_flow_input", False)
            
            return {
                "response": "We've exited the learning flow. Feel free to ask me any questions or start a new discussion.",
                "teaching_mode": "exploratory"
            }
            
        else:
            # Handle a regular question in the context of the current flow item
            current_item = flow_items[current_position]
            
            # Analyze the query to determine intent and required agents
            intent, required_agents = self._analyze_query(query, context)
            
            # Generate response based on intent and required agents
            response = self._generate_response(intent, required_agents, context, query, user_id)
            
            # Add a hint about interactive features
            hint = "You can continue exploring this topic, ask specific questions, request a quiz, or move to the next topic."
            response["response"] += f"\n\n{hint}"
            
            # Keep the flow active
            response["teaching_mode"] = "dynamic_flow"
            response["flow_structure"] = {
                "items": flow_items,
                "current_position": current_position
            }
            response["waiting_for_flow_input"] = True
            
            return response
    
    def _move_to_next_flow_item(self, user_id: str, current_position: int, flow_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Move to the next flow item and generate its content.
        
        Args:
            user_id: The user's ID
            current_position: The current position in the flow
            flow_items: The list of flow items
            
        Returns:
            Dict containing the content for the next flow item
        """
        # Move to the next flow item if not at the end
        if current_position < len(flow_items) - 1:
            current_position += 1
            self.update_shared_state("flow_position", current_position)
            current_item = flow_items[current_position]
            
            # Generate content for the current item
            content = self._generate_flow_content(current_item, user_id)
            
            return content
        else:
            # We've reached the end of the flow
            return {
                "response": "We've reached the end of all topics. Would you like to review any specific topic or start a discussion about something we covered?",
                "teaching_mode": "dynamic_flow",
                "flow_structure": {
                    "items": flow_items,
                    "current_position": current_position
                },
                "waiting_for_flow_input": True
            }
    
    def _generate_practice_questions(self, user_id: str, current_position: int, flow_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate practice questions for the current topic using the quiz agent.
        
        Args:
            user_id: The user's ID
            current_position: The current position in the flow
            flow_items: The list of flow items
            
        Returns:
            Dict containing the practice questions
        """
        current_item = flow_items[current_position]
        item_title = current_item["title"]
        item_content = current_item.get("content", "")
        
        self.logger.info(f"Generating interactive quiz for topic: {item_title}")
        
        try:
            # Generate comprehensive quiz questions using the quiz agent
            # Use both the title and content to get better quality questions
            context = f"{item_title}. {item_content}"
            quiz = self.quiz_agent.process(context, num_questions=3, 
                                          difficulty="adaptive", 
                                          include_explanations=True)
            
            if isinstance(quiz, dict) and "questions" in quiz and len(quiz["questions"]) > 0:
                # Format the questions for the UI
                formatted_questions = []
                
                for i, q in enumerate(quiz["questions"]):
                    question_text = q.get("question", f"Question about {item_title}")
                    options = q.get("options", [])
                    explanation = q.get("explanation", "")
                    correct_answer = q.get("correct_answer_index", 0)
                    
                    # Create a multiple choice question using the question agent
                    try:
                        question_obj = self.question_agent.process(
                            content=question_text,
                            question_type="multiple_choice",
                            options=options,
                            correct_option=correct_answer,
                            explanation=explanation
                        )
                        
                        # Add question metadata
                        question_obj["topic"] = item_title
                        question_obj["difficulty"] = q.get("difficulty", "medium")
                        question_obj["explanation"] = explanation
                        
                        formatted_questions.append(question_obj)
                    except Exception as e:
                        self.logger.error(f"Error formatting quiz question {i+1}: {str(e)}")
                
                # Store quiz in shared state for later reference
                self.update_shared_state("current_quiz", {
                    "topic": item_title,
                    "questions": formatted_questions,
                    "current_question_index": 0,
                    "correct_answers": 0,
                    "total_questions": len(formatted_questions)
                })
                
                # Prepare introduction text for the quiz
                response_text = (
                    f"## Quiz: {item_title}\n\n"
                    f"Let's test your understanding of {item_title} with these questions. "
                    f"Answer each question to assess your knowledge of key concepts.\n\n"
                )
                
                # Present the first question if we have questions
                if formatted_questions:
                    first_question = formatted_questions[0]
                    
                    # Track this quiz start
                    self._track_interaction(
                        user_id=user_id,
                        intent="quiz_start",
                        query=f"quiz on {item_title}",
                        response={"topic": item_title, "num_questions": len(formatted_questions)}
                    )
                    
                    return {
                        "response": response_text,
                        "has_question": True,
                        "question": first_question,
                        "teaching_mode": "dynamic_flow",
                        "quiz_mode": True,
                        "quiz_info": {
                            "topic": item_title,
                            "current_question": 1,
                            "total_questions": len(formatted_questions)
                        },
                        "flow_structure": {
                            "items": flow_items,
                            "current_position": current_position
                        },
                        "waiting_for_flow_input": True
                    }
                else:
                    return {
                        "response": f"I prepared some quiz questions for {item_title}, but encountered an issue formatting them. Let's try a different approach to assess your understanding.",
                        "teaching_mode": "dynamic_flow",
                        "flow_structure": {
                            "items": flow_items,
                            "current_position": current_position
                        },
                        "waiting_for_flow_input": True
                    }
            else:
                # If quiz generation failed, use the explainer agent to create a reflection prompt
                try:
                    reflection_prompt = self.explainer_agent.process(
                        text=item_title,
                        query=f"Generate 2-3 reflection questions about {item_title} to test understanding"
                    )
                    
                    if isinstance(reflection_prompt, dict) and "explanation" in reflection_prompt:
                        reflection_text = reflection_prompt["explanation"]
                    else:
                        reflection_text = str(reflection_prompt)
                    
                    return {
                        "response": f"Instead of a formal quiz, let's reflect on {item_title}:\n\n{reflection_text}\n\nThink about these questions and feel free to share your thoughts.",
                        "teaching_mode": "dynamic_flow",
                        "flow_structure": {
                            "items": flow_items,
                            "current_position": current_position
                        },
                        "waiting_for_flow_input": True
                    }
                    
                except Exception as e:
                    self.logger.error(f"Error generating reflection questions: {str(e)}")
                    return {
                        "response": f"I wasn't able to generate quiz questions for {item_title}. Let's continue with the flow and explore the topic through discussion instead.",
                        "teaching_mode": "dynamic_flow",
                        "flow_structure": {
                            "items": flow_items,
                            "current_position": current_position
                        },
                        "waiting_for_flow_input": True
                    }
        except Exception as e:
            self.logger.error(f"Error generating practice questions: {str(e)}")
            # Use diagram agent as fallback to provide visual learning instead
            try:
                diagram = self.diagram_agent.process(text=item_title, diagram_type="concept_map")
                if isinstance(diagram, dict) and "mermaid_code" in diagram:
                    return {
                        "response": f"Instead of a quiz, I've created a visual representation of {item_title} to help consolidate your understanding:",
                        "has_diagram": True,
                        "mermaid_code": diagram.get("mermaid_code"),
                        "diagram_type": diagram.get("diagram_type", "flowchart"),
                        "teaching_mode": "dynamic_flow",
                        "flow_structure": {
                            "items": flow_items,
                            "current_position": current_position
                        },
                        "waiting_for_flow_input": True
                    }
            except Exception as diagram_error:
                self.logger.error(f"Error generating fallback diagram: {str(diagram_error)}")
                
            return {
                "response": f"I encountered an issue creating quiz questions for {item_title}. Let's continue exploring the concepts through discussion instead. What specific aspects of {item_title} would you like to know more about?",
                "teaching_mode": "dynamic_flow",
                "flow_structure": {
                    "items": flow_items,
                    "current_position": current_position
                },
                "waiting_for_flow_input": True
            }
    
    def _generate_flashcards(self, user_id: str, current_position: int, flow_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate flashcards for the current topic.
        
        Args:
            user_id: The user's ID
            current_position: The current position in the flow
            flow_items: The list of flow items
            
        Returns:
            Dict containing the flashcards
        """
        current_item = flow_items[current_position]
        item_title = current_item["title"]
        
        try:
            # Generate flashcards using the flashcard agent
            flashcards = self.flashcard_agent.process(item_title)
            
            if isinstance(flashcards, dict) and "cards" in flashcards:
                response_text = f"Here are some flashcards to help you review key concepts in {item_title}:"
                
                return {
                    "response": response_text,
                    "flashcards": flashcards,
                    "has_flashcards": True,
                    "teaching_mode": "dynamic_flow",
                    "flow_structure": {
                        "items": flow_items,
                        "current_position": current_position
                    },
                    "waiting_for_flow_input": True
                }
            else:
                return {
                    "response": f"I wasn't able to generate flashcards for {item_title}. Let's continue with the flow.",
                    "teaching_mode": "dynamic_flow",
                    "flow_structure": {
                        "items": flow_items,
                        "current_position": current_position
                    },
                    "waiting_for_flow_input": True
                }
        except Exception as e:
            self.logger.error(f"Error generating flashcards: {str(e)}")
            return {
                "response": f"I encountered an issue creating flashcards for {item_title}. Let's continue with our discussion instead.",
                "teaching_mode": "dynamic_flow",
                "flow_structure": {
                    "items": flow_items,
                    "current_position": current_position
                },
                "waiting_for_flow_input": True
            }
    
    def _generate_alternative_explanation(self, user_id: str, current_position: int, flow_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate an alternative explanation for the current topic.
        
        Args:
            user_id: The user's ID
            current_position: The current position in the flow
            flow_items: The list of flow items
            
        Returns:
            Dict containing the alternative explanation
        """
        current_item = flow_items[current_position]
        item_title = current_item["title"]
        
        try:
            # Generate an alternative explanation using the explainer agent
            explanation = self.explainer_agent.process(
                text=item_title,
                query=f"Explain {item_title} using a different approach or analogy"
            )
            
            if isinstance(explanation, dict) and "explanation" in explanation:
                response_text = f"Here's another way to understand {item_title}:\n\n{explanation['explanation']}"
                
                # Generate a comprehension question
                options = [
                    "This explanation is clearer",
                    "I understand it better now",
                    "I still need more clarification",
                    "I'd like to see examples"
                ]
                
                comprehension_question = self.question_agent.process(
                    content=explanation['explanation'],
                    question_type="multiple_choice",
                    question_text=f"Did this alternative explanation help?",
                    options=options
                )
                
                # Update the current question
                self.update_shared_state("current_question", comprehension_question)
                
                return {
                    "response": response_text,
                    "has_question": True,
                    "question": comprehension_question,
                    "teaching_mode": "dynamic_flow",
                    "flow_structure": {
                        "items": flow_items,
                        "current_position": current_position
                    },
                    "waiting_for_flow_input": True
                }
            else:
                return {
                    "response": f"I wasn't able to generate an alternative explanation for {item_title}. Let's try a different approach.",
                    "teaching_mode": "dynamic_flow",
                    "flow_structure": {
                        "items": flow_items,
                        "current_position": current_position
                    },
                    "waiting_for_flow_input": True
                }
        except Exception as e:
            self.logger.error(f"Error generating alternative explanation: {str(e)}")
            return {
                "response": f"I encountered an issue creating an alternative explanation for {item_title}. Let's continue with our discussion.",
                "teaching_mode": "dynamic_flow",
                "flow_structure": {
                    "items": flow_items,
                    "current_position": current_position
                },
                "waiting_for_flow_input": True
            }
    
    def _generate_visual_content(self, user_id: str, current_position: int, flow_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate visual content for the current topic.
        
        Args:
            user_id: The user's ID
            current_position: The current position in the flow
            flow_items: The list of flow items
            
        Returns:
            Dict containing the visual content
        """
        current_item = flow_items[current_position]
        item_title = current_item["title"]
        
        try:
            # Generate a diagram using the diagram agent
            diagram = self.diagram_agent.process(text=item_title, diagram_type="auto")
            
            if isinstance(diagram, dict) and "mermaid_code" in diagram:
                response_text = f"Here's a visual representation of {item_title} to help you understand:"
                
                return {
                    "response": response_text,
                    "has_diagram": True,
                    "diagram": diagram,
                    "mermaid_code": diagram.get("mermaid_code"),
                    "diagram_type": diagram.get("diagram_type", "flowchart"),
                    "teaching_mode": "dynamic_flow",
                    "flow_structure": {
                        "items": flow_items,
                        "current_position": current_position
                    },
                    "waiting_for_flow_input": True
                }
            else:
                return {
                    "response": f"I wasn't able to generate a visual representation for {item_title}. Let's explore the topic through discussion instead.",
                    "teaching_mode": "dynamic_flow",
                    "flow_structure": {
                        "items": flow_items,
                        "current_position": current_position
                    },
                    "waiting_for_flow_input": True
                }
        except Exception as e:
            self.logger.error(f"Error generating visual content: {str(e)}")
            return {
                "response": f"I encountered an issue creating a visual representation for {item_title}. Let's continue with our written exploration.",
                "teaching_mode": "dynamic_flow",
                "flow_structure": {
                    "items": flow_items,
                    "current_position": current_position
                },
                "waiting_for_flow_input": True
            }
    
    def _track_interaction(self, user_id: str, intent: str, query: str, response: Dict[str, Any] = None) -> None:
        """
        Track user interaction for knowledge modeling.
        
        Args:
            user_id: The user's ID
            intent: The detected intent of the interaction
            query: The user's query or action
            response: Optional response data
        """
        try:
            self.logger.info(f"Tracking interaction for user {user_id}: {intent}")
            # If we have a knowledge tracking agent, use it to track the interaction
            if hasattr(self, 'knowledge_tracking_agent'):
                interaction_data = {
                    "intent": intent,
                    "query": query,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "response": response or {}
                }
                self.knowledge_tracking_agent.process(user_id, interaction_data)
        except Exception as e:
            # Log but don't fail if tracking fails
            self.logger.error(f"Error tracking interaction: {str(e)}")
            
    def _create_fallback_response(self, message: str) -> Dict[str, Any]:
        """
        Create a fallback response when an error occurs or no appropriate response is available.
        
        Args:
            message: The fallback message to send
            
        Returns:
            Dict containing the fallback response
        """
        self.logger.info(f"Creating fallback response: {message}")
        return {
            "response": message,
            "teaching_mode": "exploratory"
        }
    
    def _generate_flow_content(self, flow_item: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Generate content for a flow item with interactive questions to assess student knowledge.
        
        Args:
            flow_item: The flow item to generate content for
            user_id: The user's ID
            
        Returns:
            Dict containing the generated content and interactive elements
        """
        item_type = flow_item["type"]
        item_title = flow_item["title"]
        item_content = flow_item["content"]
        
        # Update current topic
        self.current_topic = item_title
        self.update_shared_state("current_topic", item_title)
        
        # Prepare initial content
        if item_type == "topic":
            intro_text = f"# {item_title}\n\n"
        else:
            intro_text = f"## {item_title}\n\n"
            
        # Use explainer agent to generate detailed content
        try:
            # If we have content from the topic extraction, use it as context
            context = item_content
            
            # If context is too short, use a generic prompt
            if len(context.strip()) < 50:
                self.logger.warning(f"Content for {item_title} is too short, using generic prompt")
                context = f"Generate a comprehensive explanation about {item_title} with key concepts, examples, and applications."
                
            # Get explanation from explainer agent
            explanation = self.explainer_agent.process(
                text=context,
                query=f"Explain {item_title} in detail"
            )
            
            content = ""
            if isinstance(explanation, dict):
                if "explanation" in explanation:
                    content = explanation["explanation"]
                elif "title" in explanation and "detailed_explanation" in explanation:
                    # Handle error or formatted response case
                    if "error" in explanation.get("additional_notes", "").lower() or "too short" in explanation.get("summary", "").lower():
                        self.logger.warning(f"Explainer agent returned error for {item_title}: {explanation.get('summary', 'Unknown error')}")
                        # Generate a simpler explanation without depending on the original content
                        content = f"{item_title} is an important concept to understand. While I don't have extensive details on this specific topic, I can help you explore the key aspects of {item_title} through some guided learning activities and questions. Let's start with what you already know about this topic and build from there."
                    else:
                        # It's a structured explanation - format it nicely
                        content = f"{explanation.get('summary', '')}\n\n"
                        
                        if explanation.get('key_points'):
                            content += "**Key Points:**\n"
                            for point in explanation.get('key_points', []):
                                content += f"- {point}\n"
                            content += "\n"
                        
                        content += explanation.get('detailed_explanation', '')
                        
                        if explanation.get('examples'):
                            content += "\n\n**Examples:**\n"
                            for example in explanation.get('examples', []):
                                content += f"- {example}\n"
                else:
                    # Use string representation as fallback
                    content = str(explanation)
            else:
                content = str(explanation)
            
            # If content is still problematic (too short, JSON string, etc.)
            if len(content.strip()) < 100 or (content.strip().startswith('{') and content.strip().endswith('}')):
                self.logger.warning(f"Generated content for {item_title} is inadequate, using fallback text")
                content = f"The topic of {item_title} encompasses various important concepts and applications. While we explore this topic, feel free to ask specific questions about any aspect you'd like to understand better. I'm here to guide your learning journey on {item_title}."
            
            # Create the response object
            response = {
                "response": intro_text + content,
                "teaching_mode": "dynamic_flow",
                "item_title": item_title,
                "item_type": item_type
            }
                
            # Generate diagram if appropriate
            if self._should_generate_diagram_for_topic(item_title):
                try:
                    diagram = self.diagram_agent.process(text=content, diagram_type="auto")
                    if isinstance(diagram, dict) and "mermaid_code" in diagram:
                        diagram_content = f"\n\nHere's a visual representation to help you understand:\n\n"
                        response["response"] += diagram_content
                        response["has_diagram"] = True
                        response["diagram"] = diagram
                        response["mermaid_code"] = diagram.get("mermaid_code")
                except Exception as e:
                    self.logger.error(f"Error generating diagram for flow item: {str(e)}")
            
            # Generate a comprehension question to assess understanding
            try:
                # Generate a multiple-choice question about this topic
                options = [
                    "I understand this concept completely",
                    "I understand most of it but have some questions",
                    "I'm still confused about some key points",
                    "I need a simpler explanation"
                ]
                
                comprehension_question = self.question_agent.process(
                    content=content,
                    question_type="multiple_choice",
                    question_text=f"How well do you understand {item_title}?",
                    options=options
                )
                
                response["has_question"] = True
                response["question"] = comprehension_question
                
                # Save the current question to shared state
                self.update_shared_state("current_question", comprehension_question)
                
            except Exception as e:
                self.logger.error(f"Error generating comprehension question: {str(e)}")
            
            # Try to generate quiz questions for this topic
            try:
                quiz = self.quiz_agent.process(content, num_questions=2)
                if isinstance(quiz, dict) and "questions" in quiz and len(quiz["questions"]) > 0:
                    response["has_quiz"] = True
                    response["quiz"] = quiz
                    response["response"] += "\n\nI've prepared some quiz questions to test your understanding of this topic."
            except Exception as e:
                self.logger.error(f"Error generating quiz for flow item: {str(e)}")
            
            # Try to generate flashcards for key points
            try:
                flashcards = self.flashcard_agent.process(content)
                if isinstance(flashcards, dict) and "cards" in flashcards and len(flashcards["cards"]) > 0:
                    response["has_flashcards"] = True
                    response["flashcards"] = flashcards
                    response["response"] += "\n\nI've created flashcards to help you review key concepts in this topic."
            except Exception as e:
                self.logger.error(f"Error generating flashcards for flow item: {str(e)}")
            
            # Add navigation hints
            navigation_text = "\n\nNavigate through this learning flow using the buttons below or ask questions about any aspect that interests you."
            response["response"] += navigation_text
            
            # Track this interaction
            self.logger.info(f"Tracking flow item view for user {user_id}: {item_title}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error generating flow content: {str(e)}")
            traceback.print_exc()
            
            # Enhanced fallback content with more educational value
            fallback_response = {
                "response": f"{intro_text}Let's explore {item_title}. While I'm preparing comprehensive material on this topic, I'd like to know what aspects of {item_title} you're most interested in learning about. What specific questions do you have about {item_title}?\n\nYou can also navigate to other topics using the commands below, or ask me to generate a practice quiz on this topic.",
                "teaching_mode": "dynamic_flow",
                "item_title": item_title,
                "item_type": item_type
            }
            
            return fallback_response
    
    def _generate_integrated_lesson_plan(self, topic: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Generate a comprehensive lesson plan that integrates all available agents.
        
        This creates a structured learning path that includes explanations, diagrams, 
        quizzes, flashcards, and assessments, utilizing all the specialized agents.
        
        Args:
            topic: Dict containing the topic information
            user_id: The user's ID
            
        Returns:
            Dict containing the integrated lesson plan
        """
        self.logger.info(f"Generating integrated lesson plan for topic: {topic.get('title', 'Unknown Topic')}")
        
        topic_title = topic.get("title", "Unknown Topic")
        topic_content = topic.get("content", "")
        
        # Initialize the lesson plan structure
        integrated_plan = {
            "title": f"Comprehensive Lesson: {topic_title}",
            "topic": topic_title,
            "description": f"An interactive learning plan covering all aspects of {topic_title}",
            "activities": [],
            "generated_at": datetime.datetime.now().isoformat(),
            "user_id": user_id
        }
        
        try:
            # 1. Get a structured lesson plan from the lesson plan agent
            knowledge_level = 50  # Default to intermediate level
            time_available = 60   # Default to 60 minutes
            
            # Check if we have progress data for this topic
            progress = self.shared_state.get("progress", {})
            if topic_title in progress:
                topic_progress = progress[topic_title]
                if "knowledge_level" in topic_progress:
                    knowledge_level = topic_progress["knowledge_level"]
            
            # Get lesson plan
            try:
                base_plan = self.lesson_plan_agent.process(
                    user_id=user_id,
                    topic=topic_title,
                    knowledge_level=knowledge_level,
                    time_available=time_available
                )
                
                if base_plan and "activities" in base_plan:
                    # Add the learning objectives
                    integrated_plan["learning_objectives"] = base_plan.get("learning_objectives", [])
                    integrated_plan["knowledge_level"] = base_plan.get("knowledge_level", "intermediate")
                    integrated_plan["duration_minutes"] = base_plan.get("duration_minutes", 60)
                    
                    # Add assessment criteria
                    if "assessment" in base_plan:
                        integrated_plan["assessment"] = base_plan["assessment"]
            except Exception as e:
                self.logger.error(f"Error generating base lesson plan: {str(e)}")
                # Continue with other agents even if lesson plan generation fails
        
            # 2. Add an introduction activity with explainer content
            try:
                intro_explanation = self.explainer_agent.process(
                    text=topic_content,
                    query=f"Provide a comprehensive introduction to {topic_title}"
                )
                
                if isinstance(intro_explanation, dict) and "explanation" in intro_explanation:
                    intro_content = intro_explanation["explanation"]
                else:
                    intro_content = str(intro_explanation)
                
                intro_activity = {
                    "id": "introduction",
                    "title": f"Introduction to {topic_title}",
                    "type": "reading",
                    "content": intro_content,
                    "duration_minutes": 10,
                    "requires_response": False,
                    "completion_status": "not_started"
                }
                
                integrated_plan["activities"].append(intro_activity)
            except Exception as e:
                self.logger.error(f"Error generating introduction: {str(e)}")
        
            # 3. Add a visual learning activity with diagrams
            try:
                diagram = self.diagram_agent.process(
                    text=topic_content, 
                    diagram_type="concept_map"
                )
                
                if isinstance(diagram, dict) and "mermaid_code" in diagram:
                    diagram_activity = {
                        "id": "visual_learning",
                        "title": f"Visual Representation of {topic_title}",
                        "type": "diagram",
                        "diagram_code": diagram.get("mermaid_code", ""),
                        "diagram_type": diagram.get("diagram_type", "flowchart"),
                        "description": f"This diagram illustrates the key concepts and relationships within {topic_title}.",
                        "duration_minutes": 5,
                        "requires_response": False,
                        "completion_status": "not_started"
                    }
                    
                    integrated_plan["activities"].append(diagram_activity)
            except Exception as e:
                self.logger.error(f"Error generating diagram: {str(e)}")
        
            # 4. Add interactive quiz questions
            try:
                quiz = self.quiz_agent.process(
                    topic_content, 
                    num_questions=5,
                    difficulty="adaptive",
                    include_explanations=True
                )
                
                if isinstance(quiz, dict) and "questions" in quiz and len(quiz["questions"]) > 0:
                    # Format questions
                    formatted_questions = []
                    for i, q in enumerate(quiz["questions"]):
                        question_text = q.get("question", f"Question about {topic_title}")
                        options = q.get("options", [])
                        explanation = q.get("explanation", "")
                        correct_answer = q.get("correct_answer_index", 0)
                        
                        # Create a multiple choice question
                        try:
                            question_obj = self.question_agent.process(
                                content=question_text,
                                question_type="multiple_choice",
                                options=options,
                                correct_option=correct_answer,
                                explanation=explanation
                            )
                            
                            # Add question metadata
                            question_obj["topic"] = topic_title
                            question_obj["difficulty"] = q.get("difficulty", "medium")
                            question_obj["explanation"] = explanation
                            
                            formatted_questions.append(question_obj)
                        except Exception as e:
                            self.logger.error(f"Error formatting quiz question {i+1}: {str(e)}")
                    
                    quiz_activity = {
                        "id": "knowledge_check",
                        "title": f"Test Your Understanding of {topic_title}",
                        "type": "quiz",
                        "questions": formatted_questions,
                        "description": "Answer these questions to test your understanding of the key concepts.",
                        "duration_minutes": 15,
                        "requires_response": True,
                        "completion_status": "not_started"
                    }
                    
                    integrated_plan["activities"].append(quiz_activity)
            except Exception as e:
                self.logger.error(f"Error generating quiz: {str(e)}")
        
            # 5. Add flashcards for key concepts
            try:
                flashcards = self.flashcard_agent.process(topic_content)
                
                if isinstance(flashcards, dict) and "cards" in flashcards and len(flashcards["cards"]) > 0:
                    flashcard_activity = {
                        "id": "flashcards",
                        "title": f"Key Concepts in {topic_title}",
                        "type": "flashcards",
                        "cards": flashcards["cards"],
                        "description": "Review these flashcards to reinforce your memory of important concepts.",
                        "duration_minutes": 10,
                        "requires_response": False,
                        "completion_status": "not_started"
                    }
                    
                    integrated_plan["activities"].append(flashcard_activity)
            except Exception as e:
                self.logger.error(f"Error generating flashcards: {str(e)}")
        
            # 6. Add a reflective learning activity
            try:
                reflection_questions = self.explainer_agent.process(
                    text=topic_content,
                    query=f"Generate 3 reflection questions about {topic_title} to deepen understanding"
                )
                
                if isinstance(reflection_questions, dict) and "explanation" in reflection_questions:
                    reflection_content = reflection_questions["explanation"]
                else:
                    reflection_content = str(reflection_questions)
                
                reflection_activity = {
                    "id": "reflection",
                    "title": "Reflect on Your Learning",
                    "type": "reflection",
                    "content": reflection_content,
                    "description": "Take time to reflect on what you've learned and how you might apply it.",
                    "duration_minutes": 10,
                    "requires_response": True,
                    "completion_status": "not_started"
                }
                
                integrated_plan["activities"].append(reflection_activity)
            except Exception as e:
                self.logger.error(f"Error generating reflection questions: {str(e)}")
        
            # 7. Add a practical application exercise
            try:
                practice_exercise = self.explainer_agent.process(
                    text=topic_content,
                    query=f"Create a practical exercise or real-world application scenario for {topic_title}"
                )
                
                if isinstance(practice_exercise, dict) and "explanation" in practice_exercise:
                    practice_content = practice_exercise["explanation"]
                else:
                    practice_content = str(practice_exercise)
                
                practice_activity = {
                    "id": "application",
                    "title": "Apply What You've Learned",
                    "type": "exercise",
                    "content": practice_content,
                    "description": "Apply the concepts you've learned to a practical scenario.",
                    "duration_minutes": 15,
                    "requires_response": True,
                    "completion_status": "not_started"
                }
                
                integrated_plan["activities"].append(practice_activity)
            except Exception as e:
                self.logger.error(f"Error generating practice exercise: {str(e)}")
                
            # Calculate total duration
            total_duration = sum(activity.get("duration_minutes", 0) for activity in integrated_plan["activities"])
            integrated_plan["duration_minutes"] = total_duration
            
            # Add navigation structure
            integrated_plan["current_activity_index"] = 0
            integrated_plan["total_activities"] = len(integrated_plan["activities"])
            
            return {
                "lesson_plan": integrated_plan,
                "has_lesson_plan": True,
                "response": f"I've created a comprehensive lesson plan for {topic_title} that includes explanations, visual diagrams, quizzes, flashcards, and practical exercises. Would you like to start learning now?",
                "teaching_mode": "lesson_plan"
            }
            
        except Exception as e:
            self.logger.error(f"Error generating integrated lesson plan: {str(e)}")
            return {
                "response": f"I attempted to create a lesson plan for {topic_title} but encountered an issue. Would you like me to explain this topic conversationally instead?",
                "teaching_mode": "exploratory"
            }
    
    def _teach_adaptive_lesson_plan(self, user_id: str) -> Dict[str, Any]:
        """
        Teach a lesson plan adaptively by integrating multiple agents, tracking user knowledge,
        and adjusting the lesson content based on user responses and feedback.
        
        Args:
            user_id: The user's ID
            
        Returns:
            Dict containing the adaptive lesson response
        """
        self.logger.info(f"Starting adaptive lesson teaching for user {user_id}")
        
        # Get the current lesson plan
        lesson_plan = self.shared_state.get("lesson_plan", None)
        if not lesson_plan:
            self.logger.warning("No lesson plan found in shared state")
            return self._create_fallback_response(
                "I don't have a lesson plan to teach. Would you like me to create one for a specific topic?"
            )
        
        # Get current topic and user knowledge level
        current_topic = self.shared_state.get("current_topic", "")
        
        # Check user's current knowledge of the topic
        try:
            user_knowledge = self.knowledge_tracking_agent.get_user_knowledge_summary(user_id)
            knowledge_level = user_knowledge.get("average_level", 50)
            
            # Get topic-specific knowledge if available
            topic_progress = self.knowledge_tracking_agent.get_topic_progress(user_id, current_topic)
            if topic_progress and "level" in topic_progress:
                knowledge_level = topic_progress["level"]
                
            self.logger.info(f"User knowledge level for {current_topic}: {knowledge_level}")
        except Exception as e:
            self.logger.error(f"Error getting user knowledge: {str(e)}")
            knowledge_level = 50  # Default to intermediate if there's an error
            
        # Set up the adaptive teaching state
        self.is_teaching_lesson_plan = True
        self.current_activity_index = 0
        self.update_shared_state("teaching_mode", "adaptive_lesson")
        self.update_shared_state("current_activity_index", 0)
        self.update_shared_state("knowledge_level", knowledge_level)
        
        # Adapt the lesson plan based on knowledge level if needed
        if knowledge_level < 30:
            # For beginners, simplify and add more explanations
            self._adapt_lesson_for_beginners(lesson_plan)
        elif knowledge_level > 70:
            # For advanced users, add more depth and challenge
            self._adapt_lesson_for_advanced(lesson_plan)
            
        # Generate introduction to the lesson
        plan_title = lesson_plan.get("title", f"Lesson on {current_topic}")
        
        # Create the introduction with the explainer agent
        try:
            introduction_prompt = f"Create an engaging introduction for a lesson on {current_topic} for a student with {knowledge_level}% knowledge of the topic."
            introduction_result = self.explainer_agent.process(
                text="", 
                query=introduction_prompt
            )
            
            if isinstance(introduction_result, dict) and "explanation" in introduction_result:
                introduction = introduction_result["explanation"]
            else:
                introduction = str(introduction_result)
                
        except Exception as e:
            self.logger.error(f"Error generating introduction: {str(e)}")
            introduction = f"Welcome to your personalized lesson on {current_topic}. I've designed this lesson specifically for your current knowledge level."
        
        # Add lesson overview
        objectives = lesson_plan.get("learning_objectives", [])
        objectives_text = "\n".join([f"- {obj}" for obj in objectives])
        
        activities = lesson_plan.get("activities", [])
        activity_overview = "\n".join([f"- {act.get('title', 'Activity')}" for act in activities])
        
        overview = f"""
# {plan_title}

{introduction}

## Learning Objectives
{objectives_text}

## What We'll Cover
{activity_overview}

Let's begin with the first activity. I'll guide you through each step and ask questions to check your understanding along the way.
"""
        
        # Generate a comprehension question to start
        try:
            # Create a question about prior knowledge to calibrate
            question_content = f"What do you already know about {current_topic}? This will help me tailor the lesson to your needs."
            question = self.question_agent.process(
                content=question_content,
                question_type="general",
                title="Prior Knowledge Assessment"
            )
            
            self.current_question = question
            self.waiting_for_question_response = True
            self.update_shared_state("current_question", question)
            self.update_shared_state("waiting_for_question_response", True)
            
            has_question = True
        except Exception as e:
            self.logger.error(f"Error generating initial question: {str(e)}")
            has_question = False
        
        # Track the start of the lesson
        self._track_interaction(
            user_id=user_id,
            intent="lesson_start",
            query="",
            response={
                "topic": current_topic,
                "knowledge_level": knowledge_level,
                "lesson_plan_id": lesson_plan.get("id", "")
            }
        )
        
        # Create the response
        response = {
            "response": overview,
            "teaching_mode": "adaptive_lesson",
            "current_topic": current_topic,
            "knowledge_level": knowledge_level,
            "lesson_plan": lesson_plan
        }
        
        if has_question:
            response["has_question"] = True
            response["question"] = question
        
        # Check if we should add a diagram to illustrate the topic
        if self._should_generate_diagram_for_topic(current_topic):
            try:
                diagram = self.diagram_agent.process(
                    text=current_topic, 
                    diagram_type="concept_map"
                )
                
                if isinstance(diagram, dict) and "mermaid_code" in diagram:
                    response["has_diagram"] = True
                    response["mermaid_code"] = diagram["mermaid_code"]
                    response["diagram_type"] = diagram.get("diagram_type", "concept_map")
            except Exception as e:
                self.logger.error(f"Error generating diagram: {str(e)}")
        
        return response
        
    def _adapt_lesson_for_beginners(self, lesson_plan: Dict[str, Any]) -> None:
        """
        Adapt the lesson plan for beginners by simplifying content and adding more explanations.
        
        Args:
            lesson_plan: The lesson plan to adapt
        """
        self.logger.info("Adapting lesson plan for beginner level")
        
        # Modify the activities to be more beginner-friendly
        activities = lesson_plan.get("activities", [])
        for activity in activities:
            # Add "beginner" to the activity title if not already there
            if "beginner" not in activity.get("title", "").lower():
                activity["title"] = f"Beginner: {activity['title']}"
                
            # Add more time for beginners
            activity["duration_minutes"] = int(activity.get("duration_minutes", 15) * 1.5)
            
            # Tag resources as beginner-friendly
            for resource in activity.get("resources", []):
                if "beginner" not in resource.get("title", "").lower():
                    resource["title"] = f"Beginner-friendly: {resource['title']}"
    
    def _adapt_lesson_for_advanced(self, lesson_plan: Dict[str, Any]) -> None:
        """
        Adapt the lesson plan for advanced users by adding more depth and challenge.
        
        Args:
            lesson_plan: The lesson plan to adapt
        """
        self.logger.info("Adapting lesson plan for advanced level")
        
        # Modify the activities to be more challenging
        activities = lesson_plan.get("activities", [])
        for activity in activities:
            # Add "advanced" to the activity title if not already there
            if "advanced" not in activity.get("title", "").lower():
                activity["title"] = f"Advanced: {activity['title']}"
                
            # Reduce time for advanced users who may progress faster
            activity["duration_minutes"] = max(5, int(activity.get("duration_minutes", 15) * 0.8))
            
            # Tag resources as advanced
            for resource in activity.get("resources", []):
                if "advanced" not in resource.get("title", "").lower():
                    resource["title"] = f"Advanced: {resource['title']}"
    
    def _process_adaptive_lesson_interaction(self, query: str, context: str, user_id: str) -> Dict[str, Any]:
        """
        Process user interactions during the adaptive lesson, including responses to questions,
        feedback, and advancing through activities.
        
        Args:
            query: The user's query
            context: Document context
            user_id: The user's ID
            
        Returns:
            Dict containing the response
        """
        self.logger.info(f"Processing adaptive lesson interaction for user {user_id}: {query}")
        
        # Get the current lesson plan and activity
        lesson_plan = self.shared_state.get("lesson_plan", {})
        current_activity_index = self.shared_state.get("current_activity_index", 0)
        activities = lesson_plan.get("activities", [])
        
        # Check if we have a valid lesson plan with activities
        if not lesson_plan or not activities:
            self.logger.warning("No valid lesson plan or activities found")
            return self._create_fallback_response(
                "I'm having trouble with the lesson plan. Would you like to start over with a new topic?"
            )
        
        # Check if we're waiting for a response to a question
        if self.waiting_for_question_response and self.current_question:
            self.logger.info("Processing response to question")
            
            # Process the response using the question agent
            try:
                question_response = self.question_agent.process_response(
                    question=self.current_question,
                    response=query
                )
                
                # Track this interaction for knowledge modeling
                self._track_interaction(
                    user_id=user_id,
                    intent="question_response",
                    query=query,
                    response={
                        "question_type": self.current_question.get("question_type", "unknown"),
                        "topic": self.shared_state.get("current_topic", ""),
                        "is_correct": question_response.get("is_correct", None),
                        "confidence": question_response.get("confidence", 0)
                    }
                )
                
                # Reset the question state
                self.current_question = None
                self.waiting_for_question_response = False
                self.update_shared_state("current_question", None)
                self.update_shared_state("waiting_for_question_response", False)
                
                # Determine appropriate feedback based on the response
                if "is_correct" in question_response and question_response["is_correct"]:
                    feedback = question_response.get("feedback", "Great answer!") 
                else:
                    feedback = question_response.get("feedback", "Let's explore this further.")
                
                # If this was a prior knowledge assessment
                if current_activity_index == 0:
                    # Use the explainer agent to analyze the response for knowledge level
                    try:
                        knowledge_analysis_prompt = f"Analyze this response about prior knowledge of {self.shared_state.get('current_topic', 'the topic')}: '{query}'. What knowledge level does it suggest (beginner/intermediate/advanced)? Give a percentage estimate (0-100)."
                        
                        analysis_result = self.explainer_agent.process(
                            text="",
                            query=knowledge_analysis_prompt
                        )
                        
                        # Extract knowledge level from analysis
                        if isinstance(analysis_result, dict) and "explanation" in analysis_result:
                            analysis = analysis_result["explanation"]
                        else:
                            analysis = str(analysis_result)
                            
                        # Find a percentage in the analysis
                        import re
                        percentage_match = re.search(r'(\d{1,3})%|(\d{1,3}) ?percent', analysis.lower())
                        if percentage_match:
                            knowledge_level = int(percentage_match.group(1) or percentage_match.group(2))
                            knowledge_level = max(0, min(100, knowledge_level))  # Constrain between 0-100
                            
                            # Update the knowledge level in shared state
                            self.update_shared_state("knowledge_level", knowledge_level)
                            
                            # Re-adapt the lesson plan if knowledge level changed significantly
                            current_level = self.shared_state.get("knowledge_level", 50)
                            if abs(knowledge_level - current_level) > 20:
                                if knowledge_level < 30:
                                    self._adapt_lesson_for_beginners(lesson_plan)
                                elif knowledge_level > 70:
                                    self._adapt_lesson_for_advanced(lesson_plan)
                                    
                            self.logger.info(f"Updated knowledge level based on response: {knowledge_level}%")
                    except Exception as e:
                        self.logger.error(f"Error analyzing knowledge level from response: {str(e)}")
                    
                    # Continue to the first activity
                    self.current_activity_index = 1
                    self.update_shared_state("current_activity_index", 1)
                    
                    # Get the first real activity
                    if len(activities) > 0:
                        return self._present_activity(activities[0], user_id, feedback)
                    else:
                        # No activities, go to assessment
                        return self._present_lesson_assessment(user_id)
            except Exception as e:
                self.logger.error(f"Error processing question response: {str(e)}")
                # Reset question state to avoid getting stuck
                self.current_question = None
                self.waiting_for_question_response = False
                self.update_shared_state("current_question", None)
                self.update_shared_state("waiting_for_question_response", False)
        
        # Check for activity navigation commands
        if query.lower() in ["next", "continue", "next activity", "move on"]:
            # Move to the next activity
            self.logger.info("User requested to move to next activity")
            
            if current_activity_index < len(activities):
                self.current_activity_index = current_activity_index + 1
                self.update_shared_state("current_activity_index", self.current_activity_index)
                
                # Present the next activity or assessment if we've reached the end
                if self.current_activity_index < len(activities):
                    return self._present_activity(activities[self.current_activity_index], user_id)
                else:
                    return self._present_lesson_assessment(user_id)
            else:
                # We've reached the end, present the assessment
                return self._present_lesson_assessment(user_id)
                
        elif query.lower() in ["previous", "back", "go back", "previous activity"]:
            # Move to the previous activity
            self.logger.info("User requested to move to previous activity") 
            
            if current_activity_index > 1:  # Don't go back to the intro
                self.current_activity_index = current_activity_index - 1
                self.update_shared_state("current_activity_index", self.current_activity_index)
                return self._present_activity(activities[self.current_activity_index - 1], user_id)
            else:
                # Already at the first activity
                return self._create_fallback_response(
                    "We're already at the first activity. Would you like me to repeat it or shall we continue?"
                )
                
        elif query.lower() in ["repeat", "again", "repeat activity"]:
            # Repeat the current activity
            self.logger.info("User requested to repeat the current activity")
            
            if 0 < current_activity_index <= len(activities):
                return self._present_activity(activities[current_activity_index - 1], user_id)
            else:
                # No current activity to repeat
                return self._create_fallback_response(
                    "I'm not sure which activity to repeat. Would you like to continue with the lesson?"
                )
        
        # Check for quiz/practice requests
        elif any(keyword in query.lower() for keyword in ["quiz", "test", "practice", "exercise", "question"]):
            self.logger.info("User requested practice questions")
            
            # Get the current topic
            current_topic = self.shared_state.get("current_topic", "")
            
            if not current_topic:
                return self._create_fallback_response(
                    "I need to know which topic you'd like to practice. Let's continue with the lesson first."
                )
            
            # Generate practice questions based on the current activity or topic
            if 0 < current_activity_index <= len(activities):
                activity = activities[current_activity_index - 1]
                activity_title = activity.get("title", "this activity")
                activity_content = activity.get("description", "")
                
                # Generate questions using the quiz agent
                try:
                    quiz_result = self.quiz_agent.process(
                        content=activity_content,
                        topic=activity_title,
                        num_questions=3,
                        difficulty="adaptive",
                        question_types=["multiple_choice", "true_false"]
                    )
                    
                    if isinstance(quiz_result, dict) and "questions" in quiz_result:
                        questions = quiz_result["questions"]
                        
                        # Format the first question
                        if questions and len(questions) > 0:
                            first_question = questions[0]
                            
                            # Use question agent to format it properly for the UI
                            formatted_question = self.question_agent.process(
                                content=first_question.get("question", ""),
                                question_type="multiple_choice" if "options" in first_question else "true_false",
                                options=first_question.get("options", []),
                                correct_answer=first_question.get("correct_answer", None),
                                explanation=first_question.get("explanation", ""),
                                title=f"Practice Question: {activity_title}"
                            )
                            
                            # Set up the question state
                            self.current_question = formatted_question
                            self.waiting_for_question_response = True
                            self.update_shared_state("current_question", formatted_question)
                            self.update_shared_state("waiting_for_question_response", True)
                            self.update_shared_state("remaining_questions", questions[1:] if len(questions) > 1 else [])
                            self.update_shared_state("in_quiz_mode", True)
                            
                            # Return the question
                            return {
                                "response": f"Let's practice what you've learned about {activity_title}. Here's a question:",
                                "has_question": True, 
                                "question": formatted_question,
                                "teaching_mode": "adaptive_lesson"
                            }
                    else:
                        return self._create_fallback_response(
                            f"I'm having trouble generating practice questions for {activity_title}. Let's continue with the lesson."
                        )
                except Exception as e:
                    self.logger.error(f"Error generating practice questions: {str(e)}")
                    return self._create_fallback_response(
                        "I encountered an issue creating practice questions. Let's continue with the lesson instead."
                    )
            else:
                return self._create_fallback_response(
                    "I'm not sure which topic to generate practice questions for. Let's continue with the lesson."
                )
        
        # Check for flashcard requests
        elif any(keyword in query.lower() for keyword in ["flashcard", "flash card", "review card"]):
            self.logger.info("User requested flashcards")
            
            # Get the current topic
            current_topic = self.shared_state.get("current_topic", "")
            
            if not current_topic:
                return self._create_fallback_response(
                    "I need to know which topic you'd like flashcards for. Let's continue with the lesson first."
                )
            
            # Generate flashcards based on the current activity or topic
            if 0 < current_activity_index <= len(activities):
                activity = activities[current_activity_index - 1]
                activity_title = activity.get("title", "this activity")
                activity_content = activity.get("description", "")
                
                # Generate flashcards using the flashcard agent
                try:
                    flashcards_result = self.flashcard_agent.process(
                        content=activity_content,
                        num_cards=5,
                        topic=activity_title
                    )
                    
                    if isinstance(flashcards_result, dict) and "flashcards" in flashcards_result:
                        flashcards = flashcards_result["flashcards"]
                        flashcard_text = "Here are some flashcards to help you review:\n\n"
                        
                        for i, card in enumerate(flashcards, 1):
                            front = card.get("front", "")
                            back = card.get("back", "")
                            flashcard_text += f"**Card {i}:**\n- **Front:** {front}\n- **Back:** {back}\n\n"
                        
                        return {
                            "response": flashcard_text,
                            "teaching_mode": "adaptive_lesson",
                            "has_flashcards": True,
                            "flashcards": flashcards
                        }
                    else:
                        return self._create_fallback_response(
                            f"I'm having trouble generating flashcards for {activity_title}. Let's continue with the lesson."
                        )
                except Exception as e:
                    self.logger.error(f"Error generating flashcards: {str(e)}")
                    return self._create_fallback_response(
                        "I encountered an issue creating flashcards. Let's continue with the lesson instead."
                    )
            else:
                return self._create_fallback_response(
                    "I'm not sure which topic to generate flashcards for. Let's continue with the lesson."
                )
        
        # Check for diagram requests
        elif any(keyword in query.lower() for keyword in ["diagram", "visual", "picture", "illustration"]):
            self.logger.info("User requested a diagram")
            
            # Get the current topic
            current_topic = self.shared_state.get("current_topic", "")
            
            if not current_topic:
                return self._create_fallback_response(
                    "I need to know which topic you'd like a diagram for. Let's continue with the lesson first."
                )
            
            # Generate a diagram based on the current activity or topic
            if 0 < current_activity_index <= len(activities):
                activity = activities[current_activity_index - 1]
                activity_title = activity.get("title", "this activity")
                activity_content = activity.get("description", "")
                
                # Generate diagram using the diagram agent
                try:
                    diagram_result = self.diagram_agent.process(
                        text=activity_content,
                        diagram_type="auto"
                    )
                    
                    if isinstance(diagram_result, dict) and "mermaid_code" in diagram_result:
                        # Create explanation of the diagram
                        explanation_prompt = f"Explain the key components and relationships shown in a diagram about {activity_title}."
                        explanation = self.explainer_agent.process(
                            text="", 
                            query=explanation_prompt
                        )
                        
                        if isinstance(explanation, dict) and "explanation" in explanation:
                            diagram_explanation = explanation["explanation"]
                        else:
                            diagram_explanation = str(explanation)
                        
                        return {
                            "response": f"Here's a visual representation of {activity_title}:\n\n{diagram_explanation}",
                            "teaching_mode": "adaptive_lesson",
                            "has_diagram": True,
                            "mermaid_code": diagram_result["mermaid_code"],
                            "diagram_type": diagram_result.get("diagram_type", "auto")
                        }
                    else:
                        return self._create_fallback_response(
                            f"I'm having trouble generating a diagram for {activity_title}. Let's continue with the lesson."
                        )
                except Exception as e:
                    self.logger.error(f"Error generating diagram: {str(e)}")
                    return self._create_fallback_response(
                        "I encountered an issue creating a diagram. Let's continue with the lesson instead."
                    )
            else:
                return self._create_fallback_response(
                    "I'm not sure which topic to generate a diagram for. Let's continue with the lesson."
                )
        
        # If the user has a question about the current topic
        else:
            self.logger.info("Processing user query in adaptive lesson")
            
            # Get the current topic
            current_topic = self.shared_state.get("current_topic", "")
            
            # Use the explainer agent to answer the question
            try:
                answer_result = self.explainer_agent.process(
                    text=context,
                    query=f"In the context of {current_topic}, {query}"
                )
                
                if isinstance(answer_result, dict) and "explanation" in answer_result:
                    answer = answer_result["explanation"]
                else:
                    answer = str(answer_result)
                
                # After answering, generate a follow-up comprehension question
                try:
                    # Create a question to check understanding
                    question_prompt = f"Based on the explanation about {current_topic}: {answer[:300]}..."
                    question = self.question_agent.process(
                        content=question_prompt,
                        question_type="comprehension",
                        title=f"Check Your Understanding: {current_topic}"
                    )
                    
                    self.current_question = question
                    self.waiting_for_question_response = True
                    self.update_shared_state("current_question", question)
                    self.update_shared_state("waiting_for_question_response", True)
                    
                    return {
                        "response": answer,
                        "teaching_mode": "adaptive_lesson",
                        "has_question": True,
                        "question": question
                    }
                except Exception as e:
                    self.logger.error(f"Error generating follow-up question: {str(e)}")
                    
                    # If we can't generate a question, just return the answer
                    return {
                        "response": answer,
                        "teaching_mode": "adaptive_lesson"
                    }
            except Exception as e:
                self.logger.error(f"Error answering question: {str(e)}")
                return self._create_fallback_response(
                    "I'm having trouble answering that question. Let's continue with the lesson."
                )
        
    def _present_activity(self, activity: Dict[str, Any], user_id: str, feedback: str = "") -> Dict[str, Any]:
        """
        Present a lesson activity to the user with integrated content and questions.
        
        Args:
            activity: The activity to present
            user_id: The user's ID
            feedback: Optional feedback to include
            
        Returns:
            Dict containing the activity response
        """
        self.logger.info(f"Presenting activity: {activity.get('title', 'Unknown')}")
        
        # Get activity details
        activity_title = activity.get("title", "Activity")
        activity_type = activity.get("type", "reading")
        activity_duration = activity.get("duration_minutes", 15)
        activity_description = activity.get("description", "")
        activity_resources = activity.get("resources", [])
        
        # Track the activity start
        self._track_interaction(
            user_id=user_id,
            intent="activity_start",
            query="",
            response={
                "activity_title": activity_title,
                "activity_type": activity_type
            }
        )
        
        # Generate enhanced content with the explainer agent
        try:
            content_prompt = f"Create engaging educational content for a {activity_type} activity on {activity_title}. Include clear explanations, examples, and key points. Base it on this description: {activity_description}"
            
            content_result = self.explainer_agent.process(
                text="",
                query=content_prompt
            )
            
            if isinstance(content_result, dict) and "explanation" in content_result:
                enhanced_content = content_result["explanation"]
            else:
                enhanced_content = str(content_result)
        except Exception as e:
            self.logger.error(f"Error generating enhanced content: {str(e)}")
            enhanced_content = activity_description
        
        # Format resources section
        resources_text = ""
        if activity_resources:
            resources_text = "\n\n## Resources\n"
            for resource in activity_resources:
                resource_title = resource.get("title", "Resource")
                resource_type = resource.get("type", "article")
                resource_description = resource.get("description", "")
                resources_text += f"- **{resource_title}** ({resource_type}): {resource_description}\n"
        
        # Generate a comprehension question
        has_question = False
        question_data = None
        
        try:
            # Create a question to check understanding of the activity
            question = self.question_agent.process(
                content=enhanced_content,
                question_type="comprehension",
                title=f"Check Your Understanding: {activity_title}"
            )
            
            self.current_question = question
            self.waiting_for_question_response = True
            self.update_shared_state("current_question", question)
            self.update_shared_state("waiting_for_question_response", True)
            
            has_question = True
            question_data = question
        except Exception as e:
            self.logger.error(f"Error generating comprehension question: {str(e)}")
        
        # Create the complete activity content
        if feedback:
            feedback = f"{feedback}\n\n"
        
        activity_content = f"""
# {activity_title}
*{activity_type.capitalize()} Activity - Estimated time: {activity_duration} minutes*

{feedback}{enhanced_content}
{resources_text}

When you're ready to continue, just let me know.
"""
        
        # Check if we should add a diagram
        has_diagram = False
        diagram_data = None
        
        if self._should_generate_diagram_for_topic(activity_title):
            try:
                diagram = self.diagram_agent.process(
                    text=enhanced_content,
                    diagram_type="auto"
                )
                
                if isinstance(diagram, dict) and "mermaid_code" in diagram:
                    has_diagram = True
                    diagram_data = diagram
            except Exception as e:
                self.logger.error(f"Error generating diagram: {str(e)}")
        
        # Create the response
        response = {
            "response": activity_content,
            "teaching_mode": "adaptive_lesson",
            "activity_title": activity_title,
            "activity_type": activity_type
        }
        
        if has_question:
            response["has_question"] = True
            response["question"] = question_data
        
        if has_diagram:
            response["has_diagram"] = True
            response["mermaid_code"] = diagram_data["mermaid_code"]
            response["diagram_type"] = diagram_data.get("diagram_type", "auto")
        
        return response
    
    def _reset_teaching_state(self) -> None:
        """
        Reset all teaching state variables when exiting a teaching mode.
        """
        self.logger.info("Resetting teaching state")
        
        # Reset teaching mode
        self.teaching_mode = "exploratory"
        self.update_shared_state("teaching_mode", "exploratory")
        
        # Reset lesson plan state
        self.is_teaching_lesson_plan = False
        self.current_lesson_plan = None
        self.current_activity_index = 0
        self.update_shared_state("lesson_plan", None)
        self.update_shared_state("current_activity_index", 0)
        
        # Reset teaching flow state
        self.is_teaching_flow = False
        self.current_flow_position = 0
        self.flow_items = []
        self.update_shared_state("flow_position", 0)
        self.update_shared_state("flow_items", [])
        
        # Reset question state
        self.current_question = None
        self.waiting_for_question_response = False
        self.update_shared_state("current_question", None)
        self.update_shared_state("waiting_for_question_response", False)
        
        # Reset topic selection state
        self.waiting_for_topic_selection = False
        self.update_shared_state("waiting_for_topic_selection", False)
        self.update_shared_state("waiting_for_learning_option", False)
        
        self.logger.info("Teaching state reset complete")
    
    def _analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """
        Analyze the user's query to determine the intent and extract relevant information.
        
        Args:
            query: The user's query to analyze
            
        Returns:
            Dict containing the intent and additional information
        """
        self.logger.info(f"Analyzing query intent: {query}")
        
        # Initialize default result
        result = {
            "intent": "general_question",
            "confidence": 0.6
        }
        
        # Check for topic request intent
        topic_patterns = [
            r"(?:teach|explain|learn about|what is|tell me about) ([^?.,!]+)",
            r"(?:can you|could you|would you) (?:teach|explain|tell) (?:me|us) about ([^?.,!]+)",
            r"(?:i want to|i'd like to) learn about ([^?.,!]+)",
            r"(?:how does|how do) ([^?.,!]+) work"
        ]
        
        for pattern in topic_patterns:
            match = re.search(pattern, query.lower())
            if match:
                topic = match.group(1).strip()
                result["intent"] = "topic_request"
                result["topic"] = topic
                result["confidence"] = 0.8
                return result
        
        # Check for concept explanation intent
        explanation_patterns = [
            r"(?:explain|clarify|elaborate on|what is) (?:the concept of |the idea of |)?([^?.,!]+)",
            r"(?:what does|what do) ([^?.,!]+) mean",
            r"(?:define|definition of) ([^?.,!]+)"
        ]
        
        for pattern in explanation_patterns:
            match = re.search(pattern, query.lower())
            if match:
                concept = match.group(1).strip()
                result["intent"] = "concept_explanation"
                result["concept"] = concept
                result["confidence"] = 0.75
                return result
        
        # Check for comparison request
        comparison_patterns = [
            r"(?:compare|difference between|similarities between) ([^?.,!]+) and ([^?.,!]+)",
            r"(?:how does|how do) ([^?.,!]+) (?:compare to|differ from) ([^?.,!]+)",
            r"(?:what is|what are) the (?:difference|differences|similarity|similarities) between ([^?.,!]+) and ([^?.,!]+)"
        ]
        
        for pattern in comparison_patterns:
            match = re.search(pattern, query.lower())
            if match:
                try:
                    concept1 = match.group(1).strip()
                    concept2 = match.group(2).strip()
                    result["intent"] = "comparison_request"
                    result["concepts"] = [concept1, concept2]
                    result["confidence"] = 0.8
                    return result
                except IndexError:
                    # If the regex match didn't capture both groups, continue to next pattern
                    continue
        
        # Check for knowledge assessment/quiz request
        assessment_patterns = [
            r"(?:test|quiz|assess) (?:me|my knowledge) (?:on|about)? ([^?.,!]+)?",
            r"(?:check|evaluate) my understanding (?:of|on|about)? ([^?.,!]+)?",
            r"(?:what|how much) do i know about ([^?.,!]+)?",
            r"(?:give me|try) (?:a|some) (?:quiz|test|assessment|questions) (?:on|about)? ([^?.,!]+)?"
        ]
        
        for pattern in assessment_patterns:
            match = re.search(pattern, query.lower())
            if match:
                topic = match.group(1).strip() if match.group(1) else ""
                result["intent"] = "knowledge_assessment"
                if topic:
                    result["topic"] = topic
                result["confidence"] = 0.75
                return result
        
        # Check for example request
        example_patterns = [
            r"(?:show|give|provide) (?:me|some|an) example(?:s)? (?:of|for|about) ([^?.,!]+)",
            r"(?:can you|could you) (?:show|give|provide) (?:me|some|an) example(?:s)? (?:of|for|about) ([^?.,!]+)",
            r"(?:what are|what is) (?:an|some) example(?:s)? (?:of|for|about) ([^?.,!]+)",
            r"(?:illustrate|demonstrate) ([^?.,!]+) with (?:an|some) example(?:s)?"
        ]
        
        for pattern in example_patterns:
            match = re.search(pattern, query.lower())
            if match:
                concept = match.group(1).strip()
                result["intent"] = "example_request"
                result["concept"] = concept
                result["confidence"] = 0.75
                return result
        
        # If no specific intent was detected, return general question
        return result