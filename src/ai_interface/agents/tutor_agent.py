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

class TutorAgent(BaseAgent):
    """
    Main Tutor Agent that coordinates all other specialized agents.
    Acts as a natural teacher, maintaining conversation flow and selecting
    appropriate agents based on the context and learning needs.
    """
    
    def __init__(self, api_keys: List[str]):
        super().__init__(api_keys)
        
        # Initialize shared state dictionary that all agents can access
        self.shared_state = {
            "topics": [],  # List of topics and subtopics identified by the Topic Extractor Agent
            "lesson_plan": None,  # Ordered list of topics to be taught, created by the Lesson Planner Agent
            "current_topic": None,  # The topic currently being taught to the user
            "progress": {},  # Dictionary where each key is a topic, and the value is another dictionary containing the user's score and mastery level
            "user_input": None,  # The most recent input from the user (e.g., answers to quiz questions or responses to flashcards)
            "rag_content": None,  # The text content of the PDF or document being used for teaching
            "current_question": None,  # The current question being asked to the user
        }
        self.logger.info("Initialized shared state dictionary")
        
        # Initialize all specialized agents with shared state
        self.logger.info("Initializing specialized agents with shared state")
        self.topic_agent = TopicAgent(api_keys, self.shared_state)
        self.quiz_agent = QuizAgent(api_keys, self.shared_state)
        self.diagram_agent = DiagramAgent(api_keys, self.shared_state)
        self.explainer_agent = ExplainerAgent(api_keys, self.shared_state)
        self.flashcard_agent = FlashcardAgent(api_keys, self.shared_state)
        self.knowledge_tracking_agent = KnowledgeTrackingAgent(api_keys, self.shared_state)
        self.lesson_plan_agent = LessonPlanAgent(api_keys, self.shared_state)
        self.question_agent = QuestionAgent(api_keys, self.shared_state)
        self.logger.info("All specialized agents initialized with shared state")
        
        # Conversation state
        self.conversation_history = []
        self.current_topic = None
        self.teaching_mode = "exploratory"  # exploratory, focused, assessment
        self.student_knowledge_level = "intermediate"  # beginner, intermediate, advanced
        
        # Lesson plan state
        self.current_lesson_plan = None
        self.current_activity_index = 0
        self.is_teaching_lesson_plan = False
        
        # Topic selection state
        self.waiting_for_topic_selection = False
        self.presented_topics = []
        
        # Question state
        self.waiting_for_question_response = False
        self.current_question = None
        
        self.logger.info("Initialized Tutor Agent with all specialized agents and shared state")
    
    def process(self, context: str, query: str, user_id: str = "default_user", 
                conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Process the student's query and generate a natural teaching response.
        
        Args:
            context: The document context relevant to the query
            query: The student's question or statement
            user_id: Unique identifier for the student
            conversation_history: Previous conversation turns
            
        Returns:
            Dict containing the tutor's response and any additional data
        """
        self.retry_count = 0
        self.logger.info(f"Processing query for user {user_id}: {query[:50]}...")
        
        try:
            # Check for special commands
            if query.strip() == "!select_topics":
                self.logger.info("Received special command to trigger topic selection flow")
                # If we have topics, present them for selection
                if len(self.shared_state["topics"]) > 0:
                    self.logger.info("Presenting topics for selection")
                    return self._present_topics_as_question()
                else:
                    # No topics available
                    return self._create_fallback_response(
                        "No topics are available. Please upload a document first."
                    )
            
            # Check for direct study command (!study_topic:TOPIC_NAME)
            if query.strip().startswith("!study_topic:"):
                topic_name = query.strip()[13:].strip()  # Extract topic name after !study_topic:
                self.logger.info(f"Received direct study command for topic: {topic_name}")
                
                # Find the topic by name
                found_topic = None
                for topic in self.shared_state["topics"]:
                    if isinstance(topic, dict) and topic.get("title", "").lower() == topic_name.lower():
                        found_topic = topic
                        break
                
                if found_topic:
                    # Start a discussion about this topic without creating a lesson plan
                    return self._start_topic_discussion(found_topic, user_id)
                else:
                    return self._create_fallback_response(
                        f"I couldn't find the topic '{topic_name}'. Please check the topic name and try again."
                    )
        
            # Initialize conversation history if not provided
            if conversation_history:
                self.conversation_history = conversation_history
            
            # Add the user query to conversation history
            self.conversation_history.append({"role": "user", "content": query})
            self.logger.info(f"Added query to conversation history, now {len(self.conversation_history)} turns")
            
            # Check if we're waiting for a question response (like topic selection)
            if self.waiting_for_question_response and self.current_question:
                self.logger.info("Processing a response to a question")
                response = self._process_question_response(query, context, user_id)
                if response:
                    # Add the response to conversation history
                    self.conversation_history.append({"role": "tutor", "content": response["response"]})
                    self.logger.info(f"Added response to conversation history, now {len(self.conversation_history)} turns")
                    
                    # Track this interaction for knowledge modeling
                    self.logger.info("Tracking interaction for knowledge modeling")
                    self._track_interaction(user_id, "question_response", query, response)
                    
                    return response
            
            # Rest of the existing process method continues as before...
            self.retry_count = 0
            self.logger.info(f"Processing query for user {user_id}: {query[:50]}...")
            
            # Log the current state of the shared state
            self.logger.info(f"Current shared state summary:")
            self.logger.info(f"  - topics: {len(self.shared_state['topics'])} topics")
            self.logger.info(f"  - current_topic: {self.shared_state['current_topic']}")
            self.logger.info(f"  - progress: {len(self.shared_state['progress'])} topics tracked")
            self.logger.info(f"  - lesson_plan: {'Present' if self.shared_state['lesson_plan'] else 'None'}")
            self.logger.info(f"  - waiting_for_topic_selection: {self.waiting_for_topic_selection}")
            self.logger.info(f"  - waiting_for_question_response: {self.waiting_for_question_response}")
            
            # Update shared state with context and user input
            self.update_shared_state("rag_content", context)
            self.update_shared_state("user_input", query)
            
            if conversation_history:
                self.conversation_history = conversation_history
                self.logger.info(f"Using provided conversation history with {len(conversation_history)} turns")
            else:
                self.logger.info(f"Using existing conversation history with {len(self.conversation_history)} turns")
            
            # Add the current query to conversation history
            self.conversation_history.append({"role": "student", "content": query})
            
            while self.retry_count < self.max_retries:
                try:
                    # Check if we're waiting for a response to a question
                    if self.waiting_for_question_response and self.current_question:
                        self.logger.info("Processing response to question")
                        response = self._process_question_response(query, context, user_id)
                        if response:
                            # Add the response to conversation history
                            self.conversation_history.append({"role": "tutor", "content": response["response"]})
                            self.logger.info(f"Added response to conversation history, now {len(self.conversation_history)} turns")
                            
                            # Track this interaction for knowledge modeling
                            self.logger.info("Tracking interaction for knowledge modeling")
                            self._track_interaction(user_id, "question_response", query, response)
                            
                            return response
                    
                    # Check if we're waiting for a topic selection
                    if self.waiting_for_topic_selection and self.presented_topics:
                        self.logger.info("Processing query as topic selection")
                        response = self._process_topic_selection(query, context, user_id)
                        if response:
                            # Add the response to conversation history
                            self.conversation_history.append({"role": "tutor", "content": response["response"]})
                            self.logger.info(f"Added response to conversation history, now {len(self.conversation_history)} turns")
                            
                            # Track this interaction for knowledge modeling
                            self.logger.info("Tracking interaction for knowledge modeling")
                            self._track_interaction(user_id, "topic_selection", query, response)
                            
                            return response
                                    
                    # If not waiting for topic selection, proceed with normal flow
                    # Check if we're in lesson plan teaching mode
                    if self.is_teaching_lesson_plan and self.current_lesson_plan:
                        self.logger.info("Processing query in lesson plan teaching mode")
                        # Process the query in the context of the current lesson plan
                        response = self._process_lesson_plan_interaction(query, context, user_id)
                    else:
                        # Check for lesson plan commands
                        if "start lesson" in query.lower() or "teach me" in query.lower() or "begin lesson" in query.lower():
                            self.logger.info("Detected lesson plan command in query")
                            # If we have a lesson plan, start teaching it
                            if self.current_lesson_plan:
                                self.logger.info("Starting existing lesson plan")
                                self.is_teaching_lesson_plan = True
                                response = self._start_lesson_plan_teaching(user_id)
                            else:
                                self.logger.info("No existing lesson plan, checking if we have topics to present")
                                # If we have topics but no lesson plan, present topics for selection
                                if len(self.shared_state["topics"]) > 0:
                                    self.logger.info("Presenting topics for selection as interactive question")
                                    response = self._present_topics_as_question()
                                else:
                                    # No topics available, try to extract them from the context
                                    self.logger.info("Extracting topics from context")
                                    if len(context.strip()) > 100:
                                        topics = self.topic_agent.process(context)
                                        if isinstance(topics, dict) and "topics" in topics and len(topics["topics"]) > 0:
                                            self.update_shared_state("topics", topics["topics"])
                                            self.logger.info(f"Extracted {len(topics['topics'])} topics from context")
                                            # Present the extracted topics as a question
                                            response = self._present_topics_as_question()
                                        else:
                                            # No topics could be extracted, ask user for a topic
                                            self.logger.info("No topics could be extracted")
                                            response = self._create_fallback_response(
                                                "I couldn't identify specific topics in this document. What subject would you like to learn about?"
                                            )
                                    else:
                                        # Not enough context to extract topics, ask user for a topic
                                        response = self._create_fallback_response(
                                            "What topic would you like to learn about today?"
                                        )
                        else:
                            self.logger.info("Processing regular query")
                            # Analyze the query to determine intent and required agents
                            intent, required_agents = self._analyze_query(query, context)
                            self.logger.info(f"Query intent: {intent}, required agents: {required_agents}")
                            
                            # Update teaching mode based on intent
                            self._update_teaching_mode(intent)
                            self.logger.info(f"Teaching mode updated to: {self.teaching_mode}")
                            
                            # Generate response based on intent and required agents
                            response = self._generate_response(intent, required_agents, context, query, user_id)
                    
                    # Add the response to conversation history
                    self.conversation_history.append({"role": "tutor", "content": response["response"]})
                    self.logger.info(f"Added response to conversation history, now {len(self.conversation_history)} turns")
                    
                    # Track this interaction for knowledge modeling
                    self.logger.info("Tracking interaction for knowledge modeling")
                    self._track_interaction(user_id, "general", query, response)
                    
                    # Log the updated state of the shared state
                    self.logger.info(f"Updated shared state summary after processing:")
                    self.logger.info(f"  - topics: {len(self.shared_state['topics'])} topics")
                    self.logger.info(f"  - current_topic: {self.shared_state['current_topic']}")
                    self.logger.info(f"  - progress: {len(self.shared_state['progress'])} topics tracked")
                    self.logger.info(f"  - lesson_plan: {'Present' if self.shared_state['lesson_plan'] else 'None'}")
                    
                    return response
                    
                except Exception as e:
                    if "quota" in str(e).lower():
                        self.retry_count += 1
                        try:
                            self._switch_api_key()
                            continue
                        except Exception:
                            if self.retry_count >= self.max_retries:
                                self.logger.error("All API keys exhausted")
                                return self._create_fallback_response("I'm currently experiencing some technical difficulties. Let's continue our lesson in a moment.")
                            continue
                    else:
                        self.logger.error(f"Error in tutor agent: {str(e)}")
                        return self._create_fallback_response("I didn't quite understand that. Could you rephrase your question?")
        except Exception as e:
            self.logger.error(f"Error in process method: {str(e)}")
            return self._create_fallback_response("I'm currently experiencing some technical difficulties. Let's continue our lesson in a moment.")
    
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
        Process the user's topic selection and generate a lesson plan.
        
        Args:
            query: The user's topic selection
            context: Document context
            user_id: The user's ID
            
        Returns:
            Dict containing the response with the lesson plan, or None if selection was invalid
        """
        # Try to extract a topic selection (number or name)
        selected_topic = None
        selected_index = None
        
        # Check if the query is a number matching one of our topics
        try:
            selected_index = int(query.strip())
            if 1 <= selected_index <= len(self.presented_topics):
                selected_topic = self.presented_topics[selected_index - 1]
                self.logger.info(f"Selected topic by number: {selected_index} - {selected_topic['title']}")
            else:
                self.logger.info(f"Invalid topic number: {selected_index}")
                return {
                    "response": f"I don't have a topic number {selected_index}. Please select a number between 1 and {len(self.presented_topics)}.",
                    "teaching_mode": "topic_selection"
                }
        except ValueError:
            # If not a number, try to match the topic name
            query_lower = query.lower()
            
            # Check for keywords that indicate the user wants to select a topic
            selection_keywords = ["topic", "number", "select", "choose", "pick", "go with", "learn about", "study", "interested in"]
            
            # Try to extract a number mentioned in the text
            number_match = re.search(r"(?:topic|number|#)?\s*(\d+)", query_lower)
            if number_match:
                try:
                    selected_index = int(number_match.group(1))
                    if 1 <= selected_index <= len(self.presented_topics):
                        selected_topic = self.presented_topics[selected_index - 1]
                        self.logger.info(f"Selected topic by mentioned number: {selected_index} - {selected_topic['title']}")
                    else:
                        self.logger.info(f"Invalid topic number mentioned: {selected_index}")
                        return {
                            "response": f"I don't have a topic number {selected_index}. Please select a number between 1 and {len(self.presented_topics)}.",
                            "teaching_mode": "topic_selection"
                        }
                except ValueError:
                    pass
            
            # If no number was successfully extracted, try matching by name
            if not selected_topic:
                # Check if any topic titles closely match the query
                for topic in self.presented_topics:
                    title_lower = topic["title"].lower()
                    if title_lower in query_lower or query_lower in title_lower:
                        selected_topic = topic
                        selected_index = topic["index"]
                        self.logger.info(f"Selected topic by name match: {topic['title']}")
                        break
                
                # If still no match, check if there are any selection keywords and clear context matches
                if not selected_topic:
                    has_selection_keyword = any(keyword in query_lower for keyword in selection_keywords)
                    
                    if has_selection_keyword:
                        # Get the longest matching words between query and each topic title
                        best_match = None
                        best_match_score = 0
                        
                        for topic in self.presented_topics:
                            title_words = set(topic["title"].lower().split())
                            query_words = set(query_lower.split())
                            common_words = title_words.intersection(query_words)
                            
                            # If there are common words and it's better than our previous match
                            if common_words and len(common_words) > best_match_score:
                                best_match = topic
                                best_match_score = len(common_words)
                        
                        if best_match:
                            selected_topic = best_match
                            selected_index = best_match["index"]
                            self.logger.info(f"Selected topic by word matching: {best_match['title']}")
        
        # If we weren't able to determine a topic selection, ask for clarification
        if not selected_topic:
            self.logger.info("Unable to determine topic selection from query")
            return {
                "response": f"I'm not sure which topic you're selecting. Please specify by number (1-{len(self.presented_topics)}) or by the exact topic name.",
                "teaching_mode": "topic_selection"
            }
                
        # We now have a selected topic, generate a lesson plan for it
        topic_title = selected_topic["title"]
        
        # Update the current topic
        self.current_topic = topic_title
        self.update_shared_state("current_topic", topic_title)
        
        # Reset the topic selection state
        self.waiting_for_topic_selection = False
        
        # Get user knowledge level
        try:
            user_knowledge = self.knowledge_tracking_agent.get_user_knowledge_summary(user_id)
            knowledge_level = user_knowledge.get("average_level", 50)
        except Exception as e:
            self.logger.error(f"Error getting user knowledge: {str(e)}")
            knowledge_level = 50  # Default to intermediate if there's an error
        
        # Extract subtopics from the selected topic
        subtopics = selected_topic.get("subtopics", [])
        
        # Generate a lesson plan for the selected topic
        try:
            self.logger.info(f"Generating lesson plan for topic: {topic_title}")
            lesson_plan = self.lesson_plan_agent.process(
                user_id=user_id,
                topic=topic_title,
                knowledge_level=knowledge_level,
                subtopics=subtopics,
                time_available=60
            )
            
            # Set the generated lesson plan
            self.current_lesson_plan = lesson_plan
            self.update_shared_state("lesson_plan", lesson_plan)
            self.is_teaching_lesson_plan = True
            self.current_activity_index = 0
            
            # Start teaching the lesson plan
            return self._start_lesson_plan_teaching(user_id)
            
        except Exception as e:
            self.logger.error(f"Error generating lesson plan: {str(e)}")
            return self._create_fallback_response(
                f"I'm having trouble creating a lesson plan for {topic_title}. Would you like to try another topic or approach?"
            )
    
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
                explanation = self.explainer_agent.process(context, query)
                if isinstance(explanation, dict):
                    response_text = self._format_explanation(explanation, self.teaching_mode)
                    response_parts.append(response_text)
                else:
                    response_parts.append(str(explanation))
                    
            elif agent == "quiz":
                quiz = self.quiz_agent.process(context)
                if isinstance(quiz, dict):
                    # Add a natural introduction to the quiz
                    quiz_intro = f"Let's test your understanding of {quiz.get('topic', 'this topic')} with a few questions:"
                    response_parts.append(quiz_intro)
                    additional_data["quiz"] = quiz
                else:
                    response_parts.append(str(quiz))
                    
            elif agent == "flashcard":
                flashcards = self.flashcard_agent.process(context)
                if isinstance(flashcards, dict):
                    # Add a natural introduction to the flashcards
                    flashcard_intro = f"I've created some flashcards to help you memorize key points about {flashcards.get('topic', 'this topic')}:"
                    response_parts.append(flashcard_intro)
                    additional_data["flashcards"] = flashcards
                    
                    # Log that we're generating flashcards
                    self.logger.info(f"Generated {len(flashcards.get('flashcards', []))} flashcards for topic: {flashcards.get('topic', 'unknown')}")
                    
                    # Make sure we don't also generate a diagram for flashcard requests
                    if "diagram" in required_agents and intent == "request_flashcards":
                        required_agents.remove("diagram")
                else:
                    response_parts.append(str(flashcards))
                    
            elif agent == "diagram":
                # Determine the most appropriate diagram type
                diagram_type = self._determine_diagram_type(query, context)
                diagram = self.diagram_agent.process(context, diagram_type)
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
                    
            elif agent == "lesson_plan":
                # Get user knowledge level for personalization
                try:
                    user_knowledge = self.knowledge_tracking_agent.get_user_knowledge_summary(user_id)
                    knowledge_level = user_knowledge.get("average_level", 50)
                except:
                    knowledge_level = 50  # Default to intermediate if no data
                
                # Extract topic from query or use current topic
                topic_match = re.search(r"about\s+(.+?)(?:\s+for|\s+with|\s+to|\s+in|\s+at|\s+by|\s+$)", query)
                topic = topic_match.group(1) if topic_match else self.current_topic or "the subject"
                
                lesson_plan = self.lesson_plan_agent.process(
                    user_id, 
                    topic, 
                    knowledge_level, 
                    time_available=60
                )
                
                if isinstance(lesson_plan, dict):
                    # Add a natural introduction to the lesson plan
                    plan_intro = f"I've created a personalized lesson plan for {topic} based on your current knowledge level:"
                    response_parts.append(plan_intro)
                    additional_data["lesson_plan"] = lesson_plan
                    
                    # Update shared state with the lesson plan
                    self.shared_state["lesson_plan"] = lesson_plan
                else:
                    response_parts.append(str(lesson_plan))
                    
            elif agent == "topic":
                topics = self.topic_agent.process(context)
                if isinstance(topics, dict):
                    # Update shared state with topics
                    self.shared_state["topics"] = topics.get("topics", [])
                    
                    # Extract the new topic from the query
                    topic_match = re.search(r"about\s+(.+?)(?:\s+instead|\s+rather|\s+$)", query)
                    if topic_match:
                        new_topic = topic_match.group(1)
                        self.current_topic = new_topic
                        self.update_shared_state("current_topic", new_topic)
                        
                        # Find if the requested topic exists in our topics
                        found = False
                        for topic in topics.get("topics", []):
                            if new_topic.lower() in topic.get("title", "").lower():
                                found = True
                                topic_response = f"Let's talk about {topic['title']}. {topic.get('content', '')}"
                                response_parts.append(topic_response)
                                break
                                
                        if not found:
                            response_parts.append(f"I'd be happy to discuss {new_topic}. What would you like to know about it?")
                    else:
                        # If no specific topic mentioned, suggest available topics
                        topics_list = [topic.get("title") for topic in topics.get("topics", [])]
                        topics_text = ", ".join(topics_list)
                        response_parts.append(f"I can tell you about several topics in this document, including: {topics_text}. Which one interests you?")
                else:
                    response_parts.append(str(topics))
        
        # If no response parts were generated, create a fallback response
        if not response_parts:
            response_parts.append("I understand you're asking about this topic. Could you please be more specific about what you'd like to learn?")
        
        # Combine all response parts into a cohesive response
        combined_response = " ".join(response_parts)
        
        # Add follow-up suggestions based on teaching mode
        follow_ups = self._generate_follow_up_suggestions(intent, required_agents, self.teaching_mode)
        if follow_ups:
            combined_response += f"\n\n{follow_ups}"
        
        # Create the final response object
        response_obj = {
            "response": combined_response,
            **additional_data
        }
        
        return response_obj
    
    def _format_explanation(self, explanation: Dict, teaching_mode: str) -> str:
        """Format the explanation based on the current teaching mode"""
        if teaching_mode == "exploratory":
            # More concise, overview-focused explanation
            return f"{explanation.get('title', 'This topic')} - {explanation.get('summary', '')}\n\nKey points:\n" + \
                   "\n".join([f"• {point}" for point in explanation.get('key_points', [])])
                   
        elif teaching_mode == "focused":
            # More detailed explanation
            return f"{explanation.get('title', 'This topic')}\n\n{explanation.get('summary', '')}\n\n" + \
                   f"{explanation.get('detailed_explanation', '')}\n\n" + \
                   (f"For example:\n" + "\n".join([f"• {example}" for example in explanation.get('examples', [])]) 
                    if explanation.get('examples') else "")
                   
        elif teaching_mode == "assessment":
            # Focus on key points for assessment preparation
            return f"Let's review {explanation.get('title', 'this topic')}:\n\n" + \
                   "\n".join([f"• {point}" for point in explanation.get('key_points', [])]) + \
                   "\n\nRemember: " + explanation.get('additional_notes', '')
        
        # Default format
        return f"{explanation.get('title', 'This topic')}\n\n{explanation.get('summary', '')}"
    
    def _determine_diagram_type(self, query: str, context: str) -> str:
        """Determine the most appropriate diagram type based on query and context"""
        query_lower = query.lower()
        context_lower = context.lower()
        
        # Check for explicit diagram type requests
        if "sequence" in query_lower or "step" in query_lower or "process flow" in query_lower:
            return "sequence"
        elif "class" in query_lower or "object" in query_lower or "relationship" in query_lower:
            return "class"
        
        # Analyze context for clues
        if any(term in context_lower for term in ["class", "object", "inherit", "extend", "implement", "attribute", "method"]):
            return "class"
        elif any(term in context_lower for term in ["sequence", "step", "first", "then", "next", "finally", "process"]):
            return "sequence"
            
        # Default to flowchart
        return "flowchart"
    
    def _generate_greeting(self) -> str:
        """Generate a natural greeting response"""
        greetings = [
            "Hello! I'm your AI tutor. How can I help you with your learning today?",
            "Hi there! Ready to explore some interesting topics together?",
            "Welcome back! What would you like to learn about today?",
            "Greetings! I'm here to help you understand the material better. What questions do you have?"
        ]
        
        import random
        return random.choice(greetings)
    
    def _generate_feedback_response(self, query: str) -> str:
        """Generate a response to student feedback"""
        query_lower = query.lower()
        
        if any(term in query_lower for term in ["thanks", "thank you", "helpful", "good", "great", "excellent"]):
            positive_responses = [
                "You're welcome! I'm glad I could help.",
                "Happy to be of assistance! Is there anything else you'd like to learn?",
                "That's great to hear! Learning is always more effective when it's enjoyable.",
                "Excellent! Let me know if you have any other questions."
            ]
            import random
            return random.choice(positive_responses)
        else:
            # Assume confusion or negative feedback
            negative_responses = [
                "I'm sorry if that wasn't clear. Let me try to explain it differently.",
                "I understand this can be confusing. Let's break it down more simply.",
                "Let's approach this from another angle that might make more sense.",
                "Thank you for the feedback. Let me try to improve my explanation."
            ]
            import random
            return random.choice(negative_responses)
    
    def _generate_follow_up_suggestions(self, intent: str, agents: List[str], teaching_mode: str) -> str:
        """Generate follow-up suggestions based on the current context"""
        if teaching_mode == "exploratory":
            return "Would you like me to explain any specific part in more detail, or perhaps create a quiz to test your understanding?"
            
        elif teaching_mode == "focused":
            if "diagram" not in agents:
                return "Would a visual diagram help you understand this better? Or would you like some flashcards to help memorize the key points?"
            else:
                return "Would you like me to create some practice questions on this topic, or would you prefer flashcards for memorization?"
                
        elif teaching_mode == "assessment":
            return "How did you do with these questions? Would you like me to explain any of the concepts further?"
            
        return ""
    
    def _track_interaction(self, user_id: str, intent: str, query: str, response: Dict):
        """Track the interaction for knowledge modeling"""
        try:
            interaction_type = "study_session"
            if intent == "request_quiz":
                interaction_type = "quiz_result"
            elif intent == "request_flashcards":
                interaction_type = "flashcard_review"
                
            interaction_data = {
                "type": interaction_type,
                "topic": self.current_topic or "general",
                "duration_minutes": 5,  # Default duration
                "query": query,
                "response_type": ",".join(response.keys())
            }
            
            # Process the interaction and update the knowledge tracking
            knowledge_update = self.knowledge_tracking_agent.process(user_id, interaction_data)
            
            # Update the progress in shared state if we have knowledge updates
            if isinstance(knowledge_update, dict) and "topic" in knowledge_update and "knowledge_level" in knowledge_update:
                topic = knowledge_update["topic"]
                if topic not in self.shared_state["progress"]:
                    self.shared_state["progress"][topic] = {}
                
                self.shared_state["progress"][topic] = {
                    "score": knowledge_update.get("knowledge_level", 0),
                    "mastery": knowledge_update.get("knowledge_level", 0) / 100.0  # Convert to 0-1 scale
                }
                
        except Exception as e:
            self.logger.error(f"Error tracking interaction: {str(e)}")
    
    def _create_fallback_response(self, message: str) -> Dict[str, Any]:
        """Create a fallback response when errors occur"""
        return {
            "response": message,
            "fallback": True
        }
        
    def get_shared_state(self) -> Dict[str, Any]:
        """
        Get the current shared state dictionary.
        
        Returns:
            Dict containing the shared state that all agents can access
        """
        return self.shared_state
        
    def update_shared_state(self, key: str, value: Any) -> None:
        """
        Update a specific field in the shared state dictionary.
        
        Args:
            key: The key to update in the shared state
            value: The new value to set
        """
        if key in self.shared_state:
            old_value = self.shared_state[key]
            self.shared_state[key] = value
            
            # Log the update with appropriate detail based on the type
            if isinstance(value, dict) and isinstance(old_value, dict):
                # For dictionaries, log the keys that changed
                old_keys = set(old_value.keys())
                new_keys = set(value.keys())
                added_keys = new_keys - old_keys
                removed_keys = old_keys - new_keys
                updated_keys = {k for k in old_keys & new_keys if old_value[k] != value[k]}
                
                if added_keys:
                    self.logger.info(f"Added keys to shared_state['{key}']: {added_keys}")
                if removed_keys:
                    self.logger.info(f"Removed keys from shared_state['{key}']: {removed_keys}")
                if updated_keys:
                    self.logger.info(f"Updated keys in shared_state['{key}']: {updated_keys}")
                
                self.logger.info(f"Updated shared state: {key} (dictionary with {len(value)} items)")
            elif isinstance(value, list) and isinstance(old_value, list):
                # For lists, log the change in length
                self.logger.info(f"Updated shared state: {key} (list changed from {len(old_value)} to {len(value)} items)")
            else:
                # For other types, log a simple update message
                self.logger.info(f"Updated shared state: {key} (value changed)")
        else:
            self.logger.warning(f"Attempted to update unknown shared state key: {key}")
            self.shared_state[key] = value
            self.logger.info(f"Added new key to shared state: {key}")
    
    def _start_topic_discussion(self, topic: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Start a discussion about a specific topic without creating a lesson plan.
        This is used when the user clicks the "Study" button in the topics tab.
        
        Args:
            topic: The topic dictionary with title, content, and subtopics
            user_id: The user's ID
            
        Returns:
            Dict containing the initial response about the topic
        """
        self.logger.info(f"Starting discussion about topic: {topic.get('title')}")
        
        # Update the current topic
        self.current_topic = topic.get("title", "Unknown Topic")
        self.update_shared_state("current_topic", self.current_topic)
        
        # Track this interaction for knowledge modeling
        topic_title = topic.get("title", "Unknown Topic")
        self._track_interaction(user_id, "start_topic_discussion", f"Study {topic_title}", 
                               {"topic": topic_title, "method": "direct_study"})
        
        # Get topic content and subtopics for the response
        topic_content = topic.get("content", "")
        subtopics = topic.get("subtopics", [])
        
        # Generate an introduction to the topic
        intro_message = f"Let's discuss {topic_title}. "
        if topic_content:
            intro_message += f"{topic_content} "
        
        # Add information about subtopics if available
        if subtopics and len(subtopics) > 0:
            intro_message += f"\n\nThis topic includes {len(subtopics)} subtopics: "
            subtopic_list = []
            for st in subtopics[:5]:  # Limit to first 5 subtopics
                st_title = st.get("title", "")
                if st_title:
                    subtopic_list.append(st_title)
            
            intro_message += ", ".join(subtopic_list)
            if len(subtopics) > 5:
                intro_message += f", and {len(subtopics) - 5} more."
            
            intro_message += "\n\nWhat specific aspect would you like to learn about first?"
        else:
            intro_message += "\n\nWhat would you like to know about this topic?"
        
        # Return a response with the teaching mode set to "discussion"
        return {
            "response": intro_message,
            "teaching_mode": "discussion",
            "has_lesson_plan": False,
            "is_direct_study": True
        } 