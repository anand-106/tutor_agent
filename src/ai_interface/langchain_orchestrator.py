"""
LangChain-based Orchestrator for Multi-Agent Tutoring System.

This orchestrator coordinates between specialized educational agents (diagram, quiz, 
flashcard, explainer) to create a cohesive learning experience.
"""

import logging
import traceback
import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI

# Import our specialized agents
from .agents.diagram_agent import DiagramAgent
from .agents.quiz_agent import QuizAgent
from .agents.flashcard_agent import FlashcardAgent
from .agents.explainer_agent import ExplainerAgent
from .agents.topic_agent import TopicAgent
from .agents.question_agent import QuestionAgent
from ..data_processing.logger_config import setup_logger

class LangChainOrchestrator:
    """
    Orchestrates multiple specialized agents using LangChain framework.
    
    This class replaces the previous TutorAgent implementation with a more
    structured approach for managing educational content.
    """
    
    def __init__(self, api_keys: List[str]):
        """
        Initialize the orchestrator with API keys and specialized agents.
        
        Args:
            api_keys: List of API keys for language models
        """
        self.logger = setup_logger("langchain_orchestrator")
        self.logger.info("Initializing LangChain Orchestrator")
        self.api_keys = api_keys
        
        # Initialize the Gemini model
        try:
            self.llm = ChatGoogleGenerativeAI(
                google_api_key=api_keys[0],
                temperature=0.2,
                model="gemini-1.5-pro"  # Use Gemini model
            )
            self.logger.info("Successfully initialized Gemini model")
        except Exception as e:
            self.logger.error(f"Error initializing Gemini model: {str(e)}")
            self.llm = None
        
        # Initialize our existing specialized agents
        self.logger.info("Initializing specialized agents")
        self.diagram_agent = DiagramAgent(api_keys)
        self.quiz_agent = QuizAgent(api_keys)
        self.flashcard_agent = FlashcardAgent(api_keys)
        self.explainer_agent = ExplainerAgent(api_keys)
        self.topic_agent = TopicAgent(api_keys)
        self.question_agent = QuestionAgent(api_keys)
        
        # Initialize the shared state (similar to the original implementation)
        self.shared_state = {
            "topics": [],
            "current_topic": "",  # Initialize as empty string instead of None
            "flow_items": [],
            "current_position": 0,
            "teaching_mode": "conversation",
            "progress": {}  # Make sure this is initialized as an empty dict
        }
        
        self.logger.info("LangChain Orchestrator initialization complete")
    
    def process(self, query: str, context: str = "", user_id: str = "user") -> Dict[str, Any]:
        """
        Process a user query and generate a response using the appropriate agent.
        
        Args:
            query: The user's query or message
            context: Additional context (e.g., from RAG) to help respond
            user_id: Identifier for the user
            
        Returns:
            A dictionary containing the response and any additional data
        """
        try:
            self.logger.info(f"Processing query: {query[:50]}...")
            
            # Check for special question answer format: !answer:id:text
            if query.startswith("!answer:"):
                self.logger.info("Detected formatted question response")
                
                # Get the last message that required feedback
                last_message_key = f"{user_id}_last_message"
                last_message = self.shared_state.get(last_message_key, {})
                
                if last_message.get("requires_feedback") and last_message.get("has_question") and "question" in last_message:
                    previous_question = last_message.get("question", {})
                    
                    # Parse the answer format
                    parts = query.split(":", 2)  # Split only on first two colons
                    if len(parts) >= 3:
                        answer_id = parts[1]
                        answer_text = parts[2]
                        
                        self.logger.info(f"Processing answer: ID={answer_id}, Text={answer_text}")
                        
                        # Check if the answer is correct for multiple choice questions
                        if previous_question.get("type") == "multiple_choice":
                            options = previous_question.get("options", [])
                            correct_option = next((opt for opt in options if opt.get("is_correct", False)), None)
                            
                            if correct_option:
                                is_correct = answer_id == correct_option.get("id")
                                
                                if is_correct:
                                    # Correct answer
                                    response = {
                                        "response": "Correct! That's right. Let's continue with our lesson.",
                                        "teaching_mode": self.shared_state.get("teaching_mode", "conversation") 
                                    }
                                    
                                    # If we're in dynamic flow mode, maintain that mode and format
                                    if self.shared_state.get("teaching_mode") == "dynamic_flow":
                                        response["teaching_mode"] = "dynamic_flow"
                                        response["curriculum"] = {
                                            "current_position": self.shared_state.get("current_position", 0),
                                            "total_items": len(self.shared_state.get("flow_items", []))
                                        }
                                        
                                        # After answering correctly, allow them to continue
                                        response["response"] += " You can say 'next' to continue."
                                    
                                    return response
                                else:
                                    # Incorrect answer
                                    correct_text = correct_option.get("text", "")
                                    response = {
                                        "response": f"That's not quite right. The correct answer is '{correct_text}'. Let's continue.",
                                        "teaching_mode": self.shared_state.get("teaching_mode", "conversation")
                                    }
                                    
                                    # If we're in dynamic flow mode, maintain that mode and format
                                    if self.shared_state.get("teaching_mode") == "dynamic_flow":
                                        response["teaching_mode"] = "dynamic_flow"
                                        response["curriculum"] = {
                                            "current_position": self.shared_state.get("current_position", 0),
                                            "total_items": len(self.shared_state.get("flow_items", []))
                                        }
                                        
                                        # Give them a chance to understand before continuing
                                        response["response"] += " Take a moment to understand, then say 'next' to continue."
                                    
                                    return response
                        
                        # For other question types, provide a generic response
                        response = {
                            "response": f"Thanks for your response: {answer_text}. Let's continue.",
                            "teaching_mode": self.shared_state.get("teaching_mode", "conversation")
                        }
                        
                        # If we're in dynamic flow mode, maintain that mode and format
                        if self.shared_state.get("teaching_mode") == "dynamic_flow":
                            response["teaching_mode"] = "dynamic_flow"
                            response["curriculum"] = {
                                "current_position": self.shared_state.get("current_position", 0),
                                "total_items": len(self.shared_state.get("flow_items", []))
                            }
                            
                            response["response"] += " Say 'next' to continue."
                        
                        return response
                
                # If we couldn't process the answer format, fall back to normal processing
                self.logger.warning("Could not process answer format properly")
            
            # Continue with normal command processing
            if query.lower().strip() == "start flow":
                self.logger.info("Detected 'start flow' command")
                return self._create_learning_path(user_id)
                
            elif query.lower().strip() == "next":
                self.logger.info("Detected 'next' command")
                return self._navigate_flow("next", user_id)
                
            elif query.lower().strip() == "previous":
                self.logger.info("Detected 'previous' command")
                return self._navigate_flow("previous", user_id)
            
            # If in flow mode, handle based on current position
            if self.shared_state.get("teaching_mode") == "flow":
                return self._process_flow_interaction(query, context, user_id)
            
            # Otherwise, route the query to the most appropriate agent
            # Simple intent detection for now - could be improved
            query_lower = query.lower()
            
            if any(word in query_lower for word in ["diagram", "visualize", "chart", "graph"]):
                self.logger.info("Routing to diagram agent")
                diagram = self.diagram_agent.process(context or query)
                return {
                    "response": diagram.get("explanation", "Here's a diagram to help visualize:"),
                    "has_diagram": True,
                    "mermaid_code": diagram.get("mermaid_code", ""),
                    "diagram_type": diagram.get("diagram_type", "flowchart"),
                    "teaching_mode": "conversation"
                }
                
            elif any(word in query_lower for word in ["quiz", "test", "question", "practice"]):
                self.logger.info("Routing to quiz agent")
                quiz = self.quiz_agent.process(context or query)
                return {
                    "response": "Let's test your understanding with these questions:",
                    "has_question": True,
                    "question": quiz,
                    "teaching_mode": "conversation"
                }
                
            elif any(word in query_lower for word in ["flashcard", "memorize", "review"]):
                self.logger.info("Routing to flashcard agent")
                flashcards = self.flashcard_agent.process(context or query)
                return {
                    "response": "Here are some flashcards to help you study:",
                    "has_flashcards": True,
                    "flashcards": flashcards,
                    "teaching_mode": "conversation"
                }
                
            elif any(word in query_lower for word in ["topic", "extract", "document"]):
                self.logger.info("Routing to topic agent")
                topics = self.topic_agent.process(context or query)
                self.shared_state["topics"] = topics.get("topics", [])
                if topics.get("topics"):
                    self.shared_state["current_topic"] = topics["topics"][0]
                return {
                    "response": f"I've analyzed the content and identified {len(topics.get('topics', []))} main topics.",
                    "teaching_mode": "conversation",
                    "topics": topics.get("topics", [])
                }
                
            else:
                # Default to explainer for general questions
                self.logger.info("Routing to explainer agent")
                explanation = self.explainer_agent.process(context or query)
                return {
                    "response": explanation.get("detailed_explanation", "I don't have enough information to answer that."),
                    "key_points": explanation.get("key_points", []),
                    "teaching_mode": "conversation"
                }
            
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            traceback.print_exc()
            return {
                "response": f"I encountered an error processing your request: {str(e)}",
                "teaching_mode": "conversation"
            }
            
    def _process_flow_interaction(self, query: str, context: str, user_id: str) -> Dict[str, Any]:
        """Process user interaction while in flow mode"""
        # Simple handling for now - we could add more sophisticated interaction here
        self.logger.info("Processing interaction in flow mode")
        
        # Check if we're in dynamic_flow mode which requires special handling
        if self.shared_state.get("teaching_mode") == "dynamic_flow":
            return self._process_dynamic_flow_interaction(query, context, user_id)
        
        # Check if this is a response to a question
        last_message_key = f"{user_id}_last_message"
        last_message = self.shared_state.get(last_message_key, {})
        
        if last_message.get("requires_feedback") and last_message.get("has_question") and "question" in last_message:
            # This is a response to a previous question
            previous_question = last_message.get("question", {})
            return self._process_user_response(query, previous_question, user_id)
        
        # Check for keywords in the user's message that might indicate they need help
        query_lower = query.lower()
        
        # Check if user is asking for help or confused
        if any(word in query_lower for word in ["help", "don't understand", "confused", "unclear", "explain"]):
            self.logger.info("User needs help, providing alternative explanation")
            
            current_position = self.shared_state.get("current_position", 0)
            flow_items = self.shared_state.get("flow_items", [])
            
            # Generate an alternative explanation
            return self._generate_alternative_explanation(user_id, current_position, flow_items)
        
        # Check if user is asking for a check on their understanding
        elif any(word in query_lower for word in ["check", "test", "quiz", "understand", "assessment"]):
            self.logger.info("User wants to check understanding, generating question")
            
            # Generate a comprehension check question
            response = self._generate_comprehension_check(user_id)
            
            # Store this message for later reference
            self.shared_state[f"{user_id}_last_message"] = response
            
            return response
        
        # Check if user is asking for a visual or diagram
        elif any(word in query_lower for word in ["show", "visual", "diagram", "picture", "graph"]):
            self.logger.info("User wants a visual, generating diagram")
            
            # Get the current topic
            current_topic = self.shared_state.get("current_topic", {})
            topic_title = current_topic.get("title", "Topic") if isinstance(current_topic, dict) else str(current_topic)
            topic_content = current_topic.get("content", "") if isinstance(current_topic, dict) else ""
            
            # Generate a diagram
            diagram = self.diagram_agent.process(f"Topic: {topic_title}\n\n{topic_content}")
            
            return {
                "response": "Here's a visual representation of this concept:",
                "has_diagram": True,
                "mermaid_code": diagram.get("mermaid_code", ""),
                "diagram_type": diagram.get("diagram_type", "flowchart"),
                "teaching_mode": "flow",
                "flow": {
                    "topics": self.shared_state.get("flow_items", []),
                    "current_position": self.shared_state.get("current_position", 0)
                }
            }
        
        # Check if we should ask for feedback
        current_position = self.shared_state.get("current_position", 0)
        interactions_count = self.shared_state.get("interactions_count", 0)
        
        # Every 3 interactions, ask for feedback
        if interactions_count % 3 == 2:  # Every 3rd interaction (0, 3, 6, etc.)
            self.logger.info("Periodic check-in, asking for feedback")
            
            # Reset the counter
            self.shared_state["interactions_count"] = 0
            
            # Generate feedback question
            response = self._ask_for_feedback(user_id)
            
            # Store this message for later reference
            self.shared_state[f"{user_id}_last_message"] = response
            
            return response
        else:
            # Increment the interaction counter
            self.shared_state["interactions_count"] = interactions_count + 1
        
        # Default response - acknowledge and continue
        return {
            "response": f"I understand your question: '{query}'. Let's continue with our current learning flow.",
            "teaching_mode": "flow",
            "flow": {
                "topics": self.shared_state.get("flow_items", []),
                "current_position": self.shared_state.get("current_position", 0)
            }
        }
    
    def _process_dynamic_flow_interaction(self, query: str, context: str, user_id: str) -> Dict[str, Any]:
        """
        Process user interaction in dynamic flow mode, which progresses through all topics
        and subtopics automatically with minimal user input.
        
        Args:
            query: The user's query
            context: Additional context
            user_id: The user identifier
            
        Returns:
            A dictionary containing the response
        """
        self.logger.info("Processing interaction in dynamic flow mode")
        
        # Check if this is a response to a previous question
        last_message_key = f"{user_id}_last_message"
        last_message = self.shared_state.get(last_message_key, {})
        
        if last_message.get("requires_feedback") and last_message.get("has_question") and "question" in last_message:
            # Process the question response first
            previous_question = last_message.get("question", {})
            response = self._process_user_response(query, previous_question, user_id)
            
            # Clear the last message so we don't process it again
            self.shared_state.pop(last_message_key, None)
            
            # If this was a transition between topics, handle special logic
            if last_message.get("is_transition") and query.lower() in ["yes", "y", "ready", "next", "continue"]:
                next_topic_idx = last_message.get("next_topic_idx")
                if next_topic_idx is not None:
                    # Find the next position after the transition
                    current_position = self.shared_state.get("current_position", 0)
                    flow_items = self.shared_state.get("flow_items", [])
                    
                    # Move to the next topic's first item
                    for i, item in enumerate(flow_items):
                        if i > current_position and item.get("topic_idx") == next_topic_idx:
                            self.shared_state["current_position"] = i
                            
                            # Generate content for the new position
                            next_content = self._generate_curriculum_content(flow_items[i], user_id)
                            
                            # Add the transition acknowledgment
                            transition_msg = f"Great! Moving on to the next topic."
                            if "response" in next_content:
                                next_content["response"] = transition_msg + "\n\n" + next_content["response"]
                            else:
                                next_content["response"] = transition_msg
                            
                            return next_content
                            
            # If the response was to a comprehension check, move forward automatically
            if last_message.get("question", {}).get("type") == "multiple_choice":
                # After answering a question, move to the next item automatically
                return self._navigate_curriculum("next", user_id)
            
            # Return the response to the question
            return response
        
        # Check if the user wants to move forward or backward
        query_lower = query.lower().strip()
        
        if query_lower in ["next", "continue", "go on", "proceed", "forward"]:
            return self._navigate_curriculum("next", user_id)
            
        elif query_lower in ["back", "previous", "go back", "backward"]:
            return self._navigate_curriculum("previous", user_id)
            
        # Check for keywords in the user's message that might indicate they need help
        if any(word in query_lower for word in ["help", "don't understand", "confused", "unclear", "explain"]):
            self.logger.info("User needs help, providing alternative explanation")
            
            current_position = self.shared_state.get("current_position", 0)
            flow_items = self.shared_state.get("flow_items", [])
            
            # Generate an alternative explanation
            return self._generate_alternative_explanation(user_id, current_position, flow_items)
        
        # Check if user is asking for a check on their understanding
        elif any(word in query_lower for word in ["check", "test", "quiz", "understand", "assessment"]):
            self.logger.info("User wants to check understanding, generating question")
            
            # Generate a comprehension check question
            response = self._generate_comprehension_check(user_id)
            
            # Store this message for later reference
            self.shared_state[f"{user_id}_last_message"] = response
            
            return response
        
        # Check if user is asking for a visual or diagram
        elif any(word in query_lower for word in ["show", "visual", "diagram", "picture", "graph"]):
            self.logger.info("User wants a visual, generating diagram")
            
            # Get the current topic
            current_topic = self.shared_state.get("current_topic", {})
            topic_title = current_topic.get("title", "Topic") if isinstance(current_topic, dict) else str(current_topic)
            topic_content = current_topic.get("content", "") if isinstance(current_topic, dict) else ""
            
            # Generate a diagram
            diagram = self.diagram_agent.process(f"Topic: {topic_title}\n\n{topic_content}")
            
            return {
                "response": "Here's a visual representation of this concept:",
                "has_diagram": True,
                "mermaid_code": diagram.get("mermaid_code", ""),
                "diagram_type": diagram.get("diagram_type", "flowchart"),
                "teaching_mode": "dynamic_flow",
                "curriculum": {
                    "current_position": self.shared_state.get("current_position", 0),
                    "total_items": len(self.shared_state.get("flow_items", []))
                }
            }
        
        # For any other type of query, process it as a relevant question about the current topic
        current_position = self.shared_state.get("current_position", 0)
        flow_items = self.shared_state.get("flow_items", [])
        
        if current_position < len(flow_items):
            current_item = flow_items[current_position]
            topic_idx = current_item.get("topic_idx")
            
            if topic_idx is not None:
                all_topics = self.shared_state.get("topics", [])
                if 0 <= topic_idx < len(all_topics):
                    # Generate a response using the current topic's content
                    topic = all_topics[topic_idx]
                    topic_title = topic.get("title", f"Topic {topic_idx+1}")
                    topic_content = topic.get("content", "")
                    
                    # Use the explainer to answer the specific question
                    response_text = f"Let me address your question about {topic_title}."
                    try:
                        # Create a prompt that includes both the topic content and the user's question
                        prompt = f"Topic: {topic_title}\n\n{topic_content}\n\nQuestion: {query}"
                        explanation = self.explainer_agent.process(prompt)
                        response_text = explanation.get("detailed_explanation", f"I'll do my best to answer your question about {topic_title}.")
                    except Exception as e:
                        self.logger.error(f"Error generating response: {str(e)}")
                    
                    # Remind the user they can continue when ready
                    response_text += "\n\nWhen you're ready to continue, just say 'next'."
                    
                    return {
                        "response": response_text,
                        "teaching_mode": "dynamic_flow",
                        "curriculum": {
                            "current_position": current_position,
                            "total_items": len(flow_items)
                        }
                    }
        
        # Fallback response - encourage to continue
        return {
            "response": f"I see your question: '{query}'. Let's continue with our curriculum. Say 'next' to proceed or ask a more specific question about the current topic.",
            "teaching_mode": "dynamic_flow",
            "curriculum": {
                "current_position": self.shared_state.get("current_position", 0),
                "total_items": len(self.shared_state.get("flow_items", []))
            }
        }
    
    def _navigate_curriculum(self, direction: str, user_id: str) -> Dict[str, Any]:
        """
        Navigate forward or backward in the curriculum.
        
        Args:
            direction: Either "next" or "previous"
            user_id: The user identifier
            
        Returns:
            A dictionary containing the content for the new position
        """
        try:
            self.logger.info(f"Navigating {direction} in the curriculum")
            
            # Get the current items and position
            flow_items = self.shared_state.get("flow_items", [])
            if not flow_items:
                self.logger.warning("No curriculum items available")
                return {
                    "response": "The learning path is empty. Let's create a new one.",
                    "teaching_mode": "conversation"
                }
                
            current_position = self.shared_state.get("current_position", 0)
            
            # Calculate the new position
            if direction == "next":
                new_position = min(current_position + 1, len(flow_items) - 1)
            else:  # previous
                new_position = max(current_position - 1, 0)
                
            # Check if we actually moved
            if new_position == current_position:
                if direction == "next":
                    self.logger.info("Already at the end of the curriculum")
                    return {
                        "response": "We've completed the entire curriculum! Would you like me to review any specific topic?",
                        "teaching_mode": "conversation"
                    }
                else:
                    self.logger.info("Already at the beginning of the curriculum")
                    return {
                        "response": "We're already at the beginning of this learning path.",
                        "teaching_mode": "dynamic_flow",
                        "curriculum": {
                            "current_position": current_position,
                            "total_items": len(flow_items)
                        }
                    }
            
            # Update the current position
            self.shared_state["current_position"] = new_position
            
            # Update progress tracking
            curriculum_progress = self.shared_state.get("curriculum_progress", {})
            if direction == "next":
                completed_items = curriculum_progress.get("completed_items", 0)
                curriculum_progress["completed_items"] = max(completed_items, current_position + 1)
                self.shared_state["curriculum_progress"] = curriculum_progress
            
            # Get the new item
            new_item = flow_items[new_position]
            
            # Create a base response
            response = {
                "teaching_mode": "dynamic_flow",
                "curriculum": {
                    "current_position": new_position,
                    "total_items": len(flow_items)
                }
            }
            
            # Try to generate content but handle errors gracefully
            try:
                content = self._generate_curriculum_content(new_item, user_id)
                # Include any additional content from the specific agent
                response.update(content)
            except Exception as e:
                self.logger.error(f"Error generating curriculum content: {str(e)}")
                traceback.print_exc()
                title = new_item.get("title", "this section")
                response["response"] = f"Moving to: **{title}**\n\nI encountered an issue preparing this content. Please try again or say 'next' to proceed to the next section."
            
            # Track the interaction
            self._track_interaction(user_id, f"navigate_{direction}", f"{direction} in curriculum", response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error navigating curriculum: {str(e)}")
            traceback.print_exc()
            return {
                "response": f"I encountered an error navigating the curriculum: {str(e)}",
                "teaching_mode": "dynamic_flow"
            }
    
    def _navigate_flow(self, direction: str, user_id: str) -> Dict[str, Any]:
        """
        Navigate forward or backward in the learning flow.
        
        Args:
            direction: Either "next" or "previous"
            user_id: The user identifier
            
        Returns:
            A dictionary containing the content for the new position
        """
        try:
            self.logger.info(f"Navigating {direction} in learning flow")
            
            # If we're in dynamic_flow mode, use the curriculum navigation method
            if self.shared_state.get("teaching_mode") == "dynamic_flow":
                return self._navigate_curriculum(direction, user_id)
            
            # Check if we're in a flow
            if self.shared_state.get("teaching_mode") != "flow":
                self.logger.warning("Not in flow mode, cannot navigate")
                return {
                    "response": "We're not currently in a learning flow. Would you like to start one?",
                    "teaching_mode": "conversation"
                }
                
            flow_items = self.shared_state.get("flow_items", [])
            if not flow_items:
                self.logger.warning("No flow items available")
                return {
                    "response": "The learning path is empty. Let's create a new one.",
                    "teaching_mode": "conversation"
                }
                
            current_position = self.shared_state.get("current_position", 0)
            
            # Calculate the new position
            if direction == "next":
                new_position = min(current_position + 1, len(flow_items) - 1)
            else:  # previous
                new_position = max(current_position - 1, 0)
                
            # Check if we actually moved
            if new_position == current_position:
                if direction == "next":
                    self.logger.info("Already at the end of the flow")
                    return {
                        "response": "We've reached the end of this learning path. Would you like to start a new one?",
                        "teaching_mode": "flow",
                        "flow": {
                            "topics": flow_items,
                            "current_position": current_position
                        }
                    }
                else:
                    self.logger.info("Already at the beginning of the flow")
                    return {
                        "response": "We're already at the beginning of this learning path.",
                        "teaching_mode": "flow",
                        "flow": {
                            "topics": flow_items,
                            "current_position": current_position
                        }
                    }
            
            # Update the current position
            self.shared_state["current_position"] = new_position
            
            # Generate content for the new position
            flow_item = flow_items[new_position]
            
            # Create a base response first
            response = {
                "response": f"Moving to: **{flow_item['title']}**",
                "teaching_mode": "flow",
                "flow": {
                    "topics": flow_items,
                    "current_position": new_position
                }
            }
            
            # Try to generate content but handle errors gracefully
            try:
                content = self._generate_flow_content(flow_item, user_id)
                # Include any additional content from the specific agent
                response.update(content)
            except Exception as e:
                self.logger.error(f"Error generating content: {str(e)}")
                traceback.print_exc()
                response["response"] += f"\n\nI encountered an issue preparing this content. Please try again or proceed to the next topic."
            
            # Track the interaction
            self._track_interaction(user_id, f"navigate_{direction}", direction, response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error navigating flow: {str(e)}")
            traceback.print_exc()
            return {
                "response": f"I encountered an error navigating the learning path: {str(e)}",
                "teaching_mode": "flow"
            }
            
    def _generate_flow_content(self, flow_item: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Generate content based on the flow item type using the appropriate agent."""
        # Initialize interaction counter if not present
        if "interactions_count" not in self.shared_state:
            self.shared_state["interactions_count"] = 0
            
        # Use the shared method that handles content generation with specific text
        current_topic = self.shared_state.get("current_topic", {})
        topic_title = current_topic.get("title", "Topic") if isinstance(current_topic, dict) else str(current_topic)
        topic_content = current_topic.get("content", "") if isinstance(current_topic, dict) else ""
        content_text = f"Topic: {topic_title}\n\n{topic_content}"
        
        return self._generate_flow_content_with_text(flow_item, user_id, content_text)
    
    def _create_learning_path(self, user_id: str) -> Dict[str, Any]:
        """
        Create a multi-agent learning path for the selected topic.
        
        Args:
            user_id: The user identifier
            
        Returns:
            A dictionary containing the initial content and flow structure
        """
        try:
            self.logger.info("Creating multi-agent learning path")
            
            # Check if topics are available
            topics = self.shared_state.get("topics", [])
            if not topics:
                self.logger.warning("No topics available for learning path creation")
                return {
                    "response": "I don't have any topics to create a learning path. Please upload a document first.",
                    "teaching_mode": "conversation"
                }
                
            # Get the first topic if none is selected
            current_topic = self.shared_state.get("current_topic")
            if not current_topic or isinstance(current_topic, str):
                current_topic = topics[0]
                self.shared_state["current_topic"] = current_topic
                self.logger.info(f"Set current_topic to first available topic: {current_topic['title']}")
            
            # Use the comprehensive curriculum approach for a guided learning experience
            if len(topics) > 1:
                self.logger.info(f"Creating comprehensive curriculum with {len(topics)} topics")
                return self._create_comprehensive_curriculum(user_id, topics)
                
            topic_title = current_topic["title"] if isinstance(current_topic, dict) else str(current_topic)
                
            # Create flow items for the learning path
            self.logger.info(f"Creating flow items for topic: {topic_title}")
            
            # Create a standard learning path with different agent types
            flow_items = [
                {
                    "type": "explainer",
                    "title": f"Understanding {topic_title}",
                    "description": "Clear explanation of the core concepts"
                },
                {
                    "type": "diagram",
                    "title": f"Visual Representation of {topic_title}",
                    "description": "Diagram showing relationships and structure"
                },
                {
                    "type": "practice",
                    "title": f"Practice Questions on {topic_title}",
                    "description": "Test your understanding with practice questions"
                },
                {
                    "type": "flashcards",
                    "title": f"Flashcards for {topic_title}",
                    "description": "Review key concepts with flashcards"
                },
                {
                    "type": "summary",
                    "title": f"Summary of {topic_title}",
                    "description": "Recap of what you've learned"
                }
            ]
            
            # Update shared state
            self.shared_state["flow_items"] = flow_items
            self.shared_state["current_position"] = 0
            self.shared_state["teaching_mode"] = "flow"
            
            # Generate content for the first flow item
            first_item = flow_items[0]
            content = self._generate_flow_content(first_item, user_id)
            
            # Create the response
            response = {
                "response": (
                    f"I've created a learning path for **{topic_title}**. "
                    f"We'll go through explanation, visualization, practice, and review."
                ),
                "teaching_mode": "flow",
                "flow": {
                    "topics": flow_items,
                    "current_position": 0
                }
            }
            
            # Include any additional content from the specific agent
            response.update(content)
            
            # Track the interaction
            self._track_interaction(user_id, "start_flow", "start flow", response)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error creating learning path: {str(e)}")
            traceback.print_exc()
            return {
                "response": f"I encountered an error creating the learning path: {str(e)}",
                "teaching_mode": "conversation"
            }
    
    def _create_comprehensive_curriculum(self, user_id: str, topics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a comprehensive curriculum that systematically teaches all topics and subtopics.
        
        This creates a learning flow that automatically progresses through all topics with minimal
        user input, using the QuestionAgent to collect feedback and adapt the learning experience.
        
        Args:
            user_id: The user identifier
            topics: List of topics to cover
            
        Returns:
            A dictionary containing the initial content and curriculum structure
        """
        self.logger.info(f"Creating comprehensive curriculum with {len(topics)} topics")
        
        # First, we'll build a complete learning path that includes all topics and subtopics
        curriculum_items = []
        topic_map = {}  # Map to keep track of topic indices
        
        for topic_idx, topic in enumerate(topics):
            topic_title = topic.get("title", f"Topic {topic_idx+1}")
            topic_content = topic.get("content", "")
            topic_map[topic_title] = topic_idx
            
            # Add main topic explanation
            curriculum_items.append({
                "type": "explainer",
                "title": f"Understanding {topic_title}",
                "description": "Clear explanation of the core concepts",
                "topic_idx": topic_idx,
                "subtopic_idx": None,
                "is_subtopic": False
            })
            
            # Add diagram for the main topic
            curriculum_items.append({
                "type": "diagram",
                "title": f"Visual Representation of {topic_title}",
                "description": "Diagram showing relationships and structure",
                "topic_idx": topic_idx,
                "subtopic_idx": None,
                "is_subtopic": False
            })
            
            # Add comprehension check for main topic
            curriculum_items.append({
                "type": "practice",
                "title": f"Quick Check: {topic_title}",
                "description": "A quick check to assess understanding",
                "topic_idx": topic_idx,
                "subtopic_idx": None,
                "is_subtopic": False
            })
            
            # Process subtopics if they exist
            subtopics = topic.get("subtopics", [])
            for subtopic_idx, subtopic in enumerate(subtopics):
                subtopic_title = subtopic.get("title", f"Subtopic {subtopic_idx+1}")
                subtopic_content = subtopic.get("content", "")
                
                # Add subtopic explanation
                curriculum_items.append({
                    "type": "explainer",
                    "title": f"Understanding {subtopic_title}",
                    "description": "Detailed explanation of this subtopic",
                    "topic_idx": topic_idx,
                    "subtopic_idx": subtopic_idx,
                    "is_subtopic": True,
                    "parent_topic": topic_title
                })
                
                # Add comprehension check for subtopic (only if there's substantial content)
                if len(subtopic_content) > 100:
                    curriculum_items.append({
                        "type": "practice",
                        "title": f"Quick Check: {subtopic_title}",
                        "description": "A quick check to assess understanding",
                        "topic_idx": topic_idx,
                        "subtopic_idx": subtopic_idx,
                        "is_subtopic": True,
                        "parent_topic": topic_title
                    })
            
            # After covering all subtopics, add flashcards and summary for the main topic
            curriculum_items.append({
                "type": "flashcards",
                "title": f"Flashcards for {topic_title}",
                "description": "Review key concepts with flashcards",
                "topic_idx": topic_idx,
                "subtopic_idx": None,
                "is_subtopic": False
            })
            
            curriculum_items.append({
                "type": "summary",
                "title": f"Summary of {topic_title}",
                "description": "Recap of what you've learned about this topic",
                "topic_idx": topic_idx,
                "subtopic_idx": None,
                "is_subtopic": False
            })
            
            # After each topic except the last one, add a progress check and transition
            if topic_idx < len(topics) - 1:
                curriculum_items.append({
                    "type": "transition",
                    "title": f"Progress Check: Moving to Next Topic",
                    "description": "Checking your readiness to move to the next topic",
                    "topic_idx": topic_idx,
                    "next_topic_idx": topic_idx + 1,
                    "subtopic_idx": None,
                    "is_subtopic": False
                })
        
        # Add a final curriculum completion item
        curriculum_items.append({
            "type": "completion",
            "title": "Curriculum Completion",
            "description": "Final assessment and wrap-up",
            "topic_idx": None,
            "subtopic_idx": None,
            "is_subtopic": False
        })
        
        # Update shared state with the comprehensive curriculum
        self.shared_state["flow_items"] = curriculum_items
        self.shared_state["current_position"] = 0
        self.shared_state["teaching_mode"] = "dynamic_flow"
        self.shared_state["topic_map"] = topic_map
        self.shared_state["curriculum_progress"] = {
            "completed_topics": [],
            "completed_items": 0,
            "total_items": len(curriculum_items)
        }
        
        # Set the current topic to the first one in the list
        first_topic = topics[0]
        self.shared_state["current_topic"] = first_topic
        
        # Generate content for the first item
        first_item = curriculum_items[0]
        content = self._generate_curriculum_content(first_item, user_id)
        
        # Create the response
        response = {
            "response": (
                f"I've created a comprehensive learning path that will guide you through all {len(topics)} topics "
                f"and their subtopics. We'll start with **{first_topic.get('title', 'the first topic')}**.\n\n"
                f"As we progress, I'll automatically guide you through each concept, checking your understanding along the way. "
                f"You can say 'next' to continue, 'back' to review the previous section, or ask specific questions at any time."
            ),
            "teaching_mode": "dynamic_flow",
            "curriculum": {
                "topics": [topic.get("title", f"Topic {i+1}") for i, topic in enumerate(topics)],
                "current_topic": first_topic.get("title", "Topic 1"),
                "current_position": 0,
                "total_items": len(curriculum_items)
            }
        }
        
        # Include any additional content from the specific agent
        response.update(content)
        
        # Track the interaction
        self._track_interaction(user_id, "start_curriculum", "start comprehensive learning", response)
        
        return response
    
    def _generate_curriculum_content(self, curriculum_item: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Generate content for a curriculum item based on its type and associated topic.
        
        Args:
            curriculum_item: The curriculum item configuration
            user_id: The user identifier
            
        Returns:
            A dictionary containing the generated content
        """
        try:
            item_type = curriculum_item.get("type", "explainer")
            title = curriculum_item.get("title", "Learning Content")
            self.logger.info(f"Generating content for curriculum item: {title} (type: {item_type})")
            
            # Get topic information
            topic_idx = curriculum_item.get("topic_idx")
            subtopic_idx = curriculum_item.get("subtopic_idx")
            is_subtopic = curriculum_item.get("is_subtopic", False)
            
            # Get all topics from shared state
            all_topics = self.shared_state.get("topics", [])
            
            # If we have valid indices, get the correct topic/subtopic
            topic = None
            subtopic = None
            content_text = ""
            
            if topic_idx is not None and 0 <= topic_idx < len(all_topics):
                topic = all_topics[topic_idx]
                
                if is_subtopic and subtopic_idx is not None:
                    subtopics = topic.get("subtopics", [])
                    if 0 <= subtopic_idx < len(subtopics):
                        subtopic = subtopics[subtopic_idx]
                        topic_title = subtopic.get("title", f"Subtopic {subtopic_idx+1}")
                        topic_content = subtopic.get("content", "")
                        parent_title = topic.get("title", f"Topic {topic_idx+1}")
                        content_text = f"Topic: {parent_title} - {topic_title}\n\n{topic_content}"
                else:
                    topic_title = topic.get("title", f"Topic {topic_idx+1}")
                    topic_content = topic.get("content", "")
                    content_text = f"Topic: {topic_title}\n\n{topic_content}"
            
            # Set current_topic in shared state
            if is_subtopic and subtopic:
                self.shared_state["current_subtopic"] = subtopic
                self.shared_state["current_topic"] = topic
            elif topic:
                self.shared_state["current_topic"] = topic
                self.shared_state.pop("current_subtopic", None)
            
            # For transition items, handle differently
            if item_type == "transition":
                next_topic_idx = curriculum_item.get("next_topic_idx")
                if next_topic_idx is not None and 0 <= next_topic_idx < len(all_topics):
                    next_topic = all_topics[next_topic_idx]
                    next_topic_title = next_topic.get("title", f"Topic {next_topic_idx+1}")
                    
                    # Use the question agent to create a transition question
                    question = self.question_agent.process(
                        content=f"Are you ready to move on to {next_topic_title}?",
                        question_type="confirmation",
                        title=f"Ready for {next_topic_title}?"
                    )
                    
                    return {
                        "response": f"You've completed the section on {topic.get('title', 'this topic')}. Are you ready to continue to {next_topic_title}?",
                        "has_question": True,
                        "question": question,
                        "requires_feedback": True,
                        "is_transition": True,
                        "next_topic_idx": next_topic_idx
                    }
            
            # For completion items, create a wrap-up message
            if item_type == "completion":
                total_topics = len(all_topics)
                completed_topics = self.shared_state.get("curriculum_progress", {}).get("completed_topics", [])
                
                return {
                    "response": (
                        f"Congratulations! You've completed all {total_topics} topics in this curriculum.\n\n"
                        f"We've covered: {', '.join([t.get('title', f'Topic {i+1}') for i, t in enumerate(all_topics)])}.\n\n"
                        f"Do you have any final questions about what we've learned?"
                    ),
                    "teaching_mode": "conversation",
                    "curriculum_complete": True
                }
            
            # Now use the standard flow content generation based on item type
            # but pass through the specific topic content
            flow_item = {
                "type": item_type,
                "title": title,
                "description": curriculum_item.get("description", "")
            }
            
            # Generate content using the regular flow content generator
            # but with our specific content_text
            return self._generate_flow_content_with_text(flow_item, user_id, content_text)
            
        except Exception as e:
            self.logger.error(f"Error generating curriculum content: {str(e)}")
            traceback.print_exc()
            return {
                "response": f"I encountered an error generating this section's content: {str(e)}"
            }
    
    def _generate_flow_content_with_text(self, flow_item: Dict[str, Any], user_id: str, content_text: str) -> Dict[str, Any]:
        """
        Generate content based on the flow item type using the appropriate agent, with specific text.
        
        Args:
            flow_item: The flow item configuration
            user_id: The user identifier
            content_text: The specific content text to use
            
        Returns:
            A dictionary containing the generated content
        """
        try:
            item_type = flow_item.get("type", "explainer")
            title = flow_item.get("title", "Learning Content")
            self.logger.info(f"Generating content with specific text for: {title} (type: {item_type})")
            
            # Determine if we should include a question
            should_add_question = False
            position = self.shared_state.get("current_position", 0)
            
            # Add a question after explainer or diagram if it's not the first item
            if item_type in ["explainer", "diagram"] and position > 0:
                # Do it randomly - approximately 1/3 of the time
                import random
                should_add_question = random.random() < 0.3
            
            # Generate content based on item type, using our specific content_text
            content_response = {}
            
            if item_type == "explainer":
                self.logger.info("Using explainer agent with specific content")
                explanation = self.explainer_agent.process(content_text)
                content_response = {
                    "response": explanation.get("detailed_explanation", ""),
                    "key_points": explanation.get("key_points", [])
                }
                
            elif item_type == "diagram":
                self.logger.info("Using diagram agent with specific content")
                diagram = self.diagram_agent.process(content_text)
                content_response = {
                    "has_diagram": True,
                    "mermaid_code": diagram.get("mermaid_code", ""),
                    "diagram_type": diagram.get("diagram_type", "flowchart"),
                    "response": diagram.get("explanation", "")
                }
                
            elif item_type == "practice":
                self.logger.info("Using quiz agent with specific content")
                quiz = self.quiz_agent.process(content_text, num_questions=1)  # Just one question for quick checks
                
                # Convert quiz questions to question agent format
                if "questions" in quiz and len(quiz["questions"]) > 0:
                    first_question = quiz["questions"][0]
                    options = [option["text"] for option in first_question.get("options", [])]
                    correct_index = next((i for i, opt in enumerate(first_question.get("options", [])) 
                                        if opt.get("is_correct", False)), 0)
                    
                    question = self.question_agent.process(
                        content=first_question.get("text", "Check your understanding:"),
                        question_type="multiple_choice",
                        options=options,
                        question_text=first_question.get("text", ""),
                        correct_option=correct_index
                    )
                    
                    content_response = {
                        "has_question": True,
                        "question": question,
                        "response": "Let's check your understanding with a quick question:",
                        "requires_feedback": True
                    }
                    
                    # Store this message for later reference
                    self.shared_state[f"{user_id}_last_message"] = content_response
                else:
                    content_response = {
                        "has_question": True,
                        "question": quiz,
                        "response": "Let's check your understanding with a quick question:"
                    }
                
            elif item_type == "flashcards":
                self.logger.info("Using flashcard agent with specific content")
                flashcards = self.flashcard_agent.process(content_text)
                content_response = {
                    "has_flashcards": True,
                    "flashcards": flashcards,
                    "response": "Here are some flashcards to help you review the key concepts."
                }
                
            elif item_type == "summary":
                self.logger.info("Using explainer agent for summary with specific content")
                summary = self.explainer_agent.process(content_text, "Provide a concise summary of this topic")
                content_response = {
                    "response": summary.get("summary", ""),
                    "key_points": summary.get("key_points", [])
                }
                
            else:
                self.logger.warning(f"Unknown flow item type: {item_type}")
                content_response = {
                    "response": f"I'm not sure how to present content of type '{item_type}'. Let's continue with a standard explanation."
                }
            
            # Add a question if appropriate (for non-practice items)
            if should_add_question and item_type not in ["practice", "flashcards"]:
                self.logger.info("Adding comprehension check question")
                
                # Don't add a question if we already have one
                if not content_response.get("has_question"):
                    # Generate a comprehension check
                    question_response = self._generate_comprehension_check_with_text(user_id, content_text)
                    
                    # Store the original response
                    original_response = content_response.get("response", "")
                    
                    # Add the question to the response
                    content_response.update({
                        "has_question": True,
                        "question": question_response.get("question"),
                        "response": original_response + "\n\n" + question_response.get("response", ""),
                        "requires_feedback": True
                    })
                    
                    # Store this message for later reference
                    self.shared_state[f"{user_id}_last_message"] = content_response
            
            # Add a curriculum navigation hint
            current_position = self.shared_state.get("current_position", 0)
            total_items = self.shared_state.get("curriculum_progress", {}).get("total_items", 0)
            
            if "response" in content_response:
                content_response["response"] += f"\n\n(Progress: Item {current_position + 1} of {total_items}. Say 'next' to continue or ask a question if you need more information.)"
            
            return content_response
                
        except Exception as e:
            self.logger.error(f"Error generating content with specific text: {str(e)}")
            traceback.print_exc()
            return {
                "response": f"I encountered an error generating content for this section: {str(e)}"
            }
    
    def _generate_comprehension_check_with_text(self, user_id: str, content_text: str) -> Dict[str, Any]:
        """
        Generate a comprehension check question based on specific content text.
        
        Args:
            user_id: The user identifier
            content_text: The content to generate questions from
            
        Returns:
            A dictionary containing the comprehension question
        """
        self.logger.info(f"Generating comprehension check for specific content")
        
        try:
            # Use the quiz agent to generate a multiple-choice question
            quiz_result = self.quiz_agent.process(content_text, num_questions=1)
            
            if not quiz_result or not isinstance(quiz_result, dict) or "questions" not in quiz_result:
                self.logger.warning("Failed to generate quiz question, using fallback")
                # Create a simple feedback question as fallback
                return self._ask_for_feedback(user_id)
            
            # Format the first question using the question agent
            if not quiz_result["questions"] or len(quiz_result["questions"]) == 0:
                self.logger.warning("No questions in quiz result, using fallback")
                return self._ask_for_feedback(user_id)
                
            quiz_question = quiz_result["questions"][0]
            
            # Validate quiz question format
            if not isinstance(quiz_question, dict) or "options" not in quiz_question:
                self.logger.warning("Invalid quiz question format, using fallback")
                return self._ask_for_feedback(user_id)
            
            # Extract options and correct answer
            options_data = quiz_question.get("options", [])
            question_text = quiz_question.get("question", "Check your understanding:")
            explanation = quiz_question.get("explanation", "")
            
            # Ensure options is a list
            if not isinstance(options_data, list):
                self.logger.warning("Options is not a list, using fallback")
                return self._ask_for_feedback(user_id)
            
            # Handle different option formats (can be strings or dicts with "text" key)
            options = []
            correct_index = 0
            
            try:
                for i, option in enumerate(options_data):
                    if isinstance(option, dict) and "text" in option:
                        # Option is a dictionary with text field
                        options.append(option["text"])
                        # Check if this is the correct option
                        if option.get("is_correct", False):
                            correct_index = i
                    elif isinstance(option, str):
                        # Option is directly a string
                        options.append(option)
                        # Check if this matches the correct_answer
                        if "correct_answer" in quiz_question and option == quiz_question["correct_answer"]:
                            correct_index = i
                    else:
                        # Fallback for unexpected option format
                        options.append(f"Option {i+1}")
            except Exception as e:
                self.logger.error(f"Error processing options: {str(e)}")
                # Just create some default options if we hit an error
                options = ["Yes", "No", "Maybe", "Not sure"]
                correct_index = 0
                
            # If no options were found, create a default set
            if not options:
                options = ["Yes", "No", "Maybe", "Not sure"]
                correct_index = 0
            
            # Log the question for debugging
            self.logger.info(f"Quiz question text: {question_text}")
            self.logger.info(f"Quiz options: {options}")
            
            question = self.question_agent.process(
                content=explanation,
                question_type="multiple_choice",
                options=options,
                question_text=question_text,
                correct_option=correct_index
            )
            
            # Ensure all required fields are present in the question
            if not question.get("message"):
                question["message"] = question_text
            
            if not question.get("title"):
                question["title"] = "Check Your Understanding"
                
            # Log the formatted question for debugging
            self.logger.info(f"Formatted question: {question}")
            
            return {
                "response": "Let's check your understanding with a quick question:",
                "has_question": True,
                "question": question,
                "teaching_mode": "dynamic_flow",
                "requires_feedback": True
            }
        except Exception as e:
            self.logger.error(f"Error generating comprehension check: {str(e)}")
            traceback.print_exc()
            # Fall back to a confirmation question
            return self._ask_for_feedback(user_id)
    
    def _process_user_response(self, query: str, question: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Process a user's response to a question.
        
        Args:
            query: The user's response
            question: The original question object
            user_id: The user identifier
            
        Returns:
            A dictionary containing the next step in the learning flow
        """
        self.logger.info(f"Processing user response: {query}")
        
        # Process the response using the question agent
        processed_response = self.question_agent.process_response(question, query)
        
        # Track the interaction
        self._track_interaction(user_id, "question_response", query)
        
        # Get the question type
        question_type = question.get("type", "general")
        
        # Handle different response types
        if question_type == "confirmation":
            # User indicated their understanding level
            confirmed = processed_response.get("confirmed", False)
            
            if confirmed:
                # User understands, continue with flow
                return {
                    "response": "Great! Let's continue with the next part of the lesson.",
                    "teaching_mode": self.shared_state.get("teaching_mode", "conversation")
                }
            else:
                # User needs more help, provide alternative explanation
                current_position = self.shared_state.get("current_position", 0)
                flow_items = self.shared_state.get("flow_items", [])
                
                if current_position < len(flow_items):
                    return self._generate_alternative_explanation(user_id, current_position, flow_items)
                else:
                    return {
                        "response": "I understand you need more clarity. Let me explain this differently.",
                        "teaching_mode": self.shared_state.get("teaching_mode", "conversation")
                    }
                
        elif question_type == "multiple_choice":
            # User answered a comprehension question
            is_correct = processed_response.get("is_correct", False)
            
            if is_correct:
                # Correct answer
                return {
                    "response": "Correct! You're understanding this well. Let's continue.",
                    "teaching_mode": self.shared_state.get("teaching_mode", "conversation")
                }
            else:
                # Incorrect answer, provide more explanation
                return {
                    "response": "That's not quite right. Let me explain this concept differently.",
                    "teaching_mode": self.shared_state.get("teaching_mode", "conversation")
                }
        
        # Default response
        return {
            "response": "Thank you for your feedback. Let's continue with our learning.",
            "teaching_mode": self.shared_state.get("teaching_mode", "conversation")
        }
    
    def _generate_alternative_explanation(self, user_id: str, current_position: int, flow_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate an alternative explanation when the user needs more clarity.
        
        Args:
            user_id: The user identifier
            current_position: The current position in the flow
            flow_items: The flow items list
            
        Returns:
            A dictionary containing the alternative explanation
        """
        self.logger.info(f"Generating alternative explanation for flow position {current_position}")
        
        # Check if we have a valid position
        if current_position >= len(flow_items):
            return {
                "response": "I'll try to explain this differently. What specific part would you like me to clarify?",
                "teaching_mode": self.shared_state.get("teaching_mode", "conversation")
            }
        
        current_item = flow_items[current_position]
        item_type = current_item.get("type", "")
        
        # Get the current topic
        current_topic = self.shared_state.get("current_topic", {})
        topic_title = current_topic.get("title", "Topic") if isinstance(current_topic, dict) else str(current_topic)
        topic_content = current_topic.get("content", "") if isinstance(current_topic, dict) else ""
        
        # Prepare the content
        content_text = f"Topic: {topic_title}\n\n{topic_content}"
        prompt_addition = "Please explain this differently, using simpler terms and more examples."
        
        # Generate alternative explanation
        if item_type == "explainer":
            explanation = self.explainer_agent.process(content_text, prompt_addition)
            return {
                "response": explanation.get("detailed_explanation", "Let me try to explain this differently."),
                "key_points": explanation.get("key_points", []),
                "examples": explanation.get("examples", []),
                "teaching_mode": self.shared_state.get("teaching_mode", "conversation")
            }
        elif item_type == "diagram":
            # Try a different diagram type
            current_diagram_type = current_item.get("diagram_type", "flowchart")
            new_diagram_type = "class" if current_diagram_type != "class" else "flowchart"
            
            diagram = self.diagram_agent.process(content_text, new_diagram_type)
            return {
                "response": "Let me show this concept visually in a different way:",
                "has_diagram": True,
                "mermaid_code": diagram.get("mermaid_code", ""),
                "diagram_type": diagram.get("diagram_type", new_diagram_type),
                "teaching_mode": self.shared_state.get("teaching_mode", "conversation")
            }
        else:
            # Default to explainer for other types
            explanation = self.explainer_agent.process(content_text, prompt_addition)
            return {
                "response": explanation.get("detailed_explanation", "Let me try to explain this differently."),
                "key_points": explanation.get("key_points", []),
                "teaching_mode": self.shared_state.get("teaching_mode", "conversation")
            }
    
    def _track_interaction(self, user_id: str, intent: str, query: str, response: Optional[Dict[str, Any]] = None) -> None:
        """
        Track user interaction for analytics and progress tracking.
        
        Args:
            user_id: The user identifier
            intent: The detected intent or action
            query: The user's query
            response: The response provided to the user
        """
        try:
            # Ensure user_id is not null
            if not user_id:
                user_id = "default_user"
                
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Simple interaction tracking for now
            self.logger.info(f"Tracking interaction - User: {user_id}, Intent: {intent}, Time: {timestamp}")
            
            # Initialize progress tracking if not already present
            if "progress" not in self.shared_state:
                self.shared_state["progress"] = {}
                
            # Initialize user progress if not already present
            if user_id not in self.shared_state["progress"]:
                self.shared_state["progress"][user_id] = {}
                
            # Get the current topic (if any)
            current_topic = self.shared_state.get("current_topic", "")
            if isinstance(current_topic, dict) and "title" in current_topic:
                topic_name = current_topic["title"]
            else:
                topic_name = str(current_topic) if current_topic else "general"
                
            # Ensure topic name is not null
            if not topic_name:
                topic_name = "general"
                
            # Initialize topic progress if not already present
            if topic_name not in self.shared_state["progress"][user_id]:
                self.shared_state["progress"][user_id][topic_name] = {
                    "interactions": 0,
                    "last_interaction": timestamp,
                    "completed_activities": 0,
                    "knowledge_level": 0
                }
                
            # Update topic progress
            topic_progress = self.shared_state["progress"][user_id][topic_name]
            topic_progress["interactions"] = topic_progress.get("interactions", 0) + 1
            topic_progress["last_interaction"] = timestamp
            
            # Additional tracking could be added here
            
        except Exception as e:
            self.logger.error(f"Error tracking interaction: {str(e)}")
            traceback.print_exc()
            
    def set_topics(self, topics: List[Dict[str, Any]]) -> None:
        """Set the available topics in the orchestrator"""
        if not topics:
            topics = []  # Ensure topics is at least an empty list, not None
            
        self.shared_state["topics"] = topics
        
        # Set current_topic if not already set and topics are available
        if not self.shared_state.get("current_topic") and topics:
            self.shared_state["current_topic"] = topics[0]
        elif not topics:
            # If no topics, set current_topic to empty string, not None
            self.shared_state["current_topic"] = ""
            
        self.logger.info(f"Set {len(topics)} topics in orchestrator")
        
    def get_shared_state(self) -> Dict[str, Any]:
        """Get the current shared state"""
        return self.shared_state
        
    def update_shared_state(self, key: str, value: Any) -> None:
        """Update a value in the shared state"""
        if key is None:
            self.logger.warning("Attempted to update shared state with null key")
            return
            
        # Handle specific cases for certain keys
        if key == "current_topic" and value is None:
            # Convert None to empty string for current_topic
            value = ""
            
        # Handle progress data structures
        if key == "progress" and value is None:
            value = {}  # Convert None to empty dict
            
        # Update the shared state
        self.shared_state[key] = value 
        self.logger.info(f"Updated shared state: {key}")
        
    # New methods for using QuestionAgent
    
    def _ask_for_feedback(self, user_id: str, topic: str = None) -> Dict[str, Any]:
        """
        Ask the user for feedback about their understanding of the current topic.
        
        Args:
            user_id: The user identifier
            topic: Optional specific topic to ask about
            
        Returns:
            A dictionary containing the question to present to the user
        """
        self.logger.info(f"Asking for feedback from user {user_id}")
        
        if not topic:
            current_topic = self.shared_state.get("current_topic", "")
            if isinstance(current_topic, dict) and "title" in current_topic:
                topic = current_topic["title"]
            else:
                topic = str(current_topic) if current_topic else "the material"
        
        # Create a confirmation question to gauge understanding
        question = self.question_agent.process(
            content=f"How well do you understand {topic}?",
            question_type="confirmation",
            title="Understanding Check"
        )
        
        return {
            "response": f"Before we continue, I'd like to check: How well do you understand {topic} so far?",
            "has_question": True,
            "question": question,
            "teaching_mode": self.shared_state.get("teaching_mode", "conversation"),
            "requires_feedback": True
        }
    
    def _generate_comprehension_check(self, user_id: str, topic: str = None, content: str = "") -> Dict[str, Any]:
        """
        Generate a multiple-choice question to check the user's comprehension.
        
        Args:
            user_id: The user identifier
            topic: Optional specific topic to ask about
            content: Content to base the question on
            
        Returns:
            A dictionary containing the comprehension question
        """
        self.logger.info(f"Generating comprehension check for user {user_id}")
        
        if not topic:
            current_topic = self.shared_state.get("current_topic", "")
            if isinstance(current_topic, dict) and "title" in current_topic:
                topic = current_topic["title"]
                content = current_topic.get("content", "")
            else:
                topic = str(current_topic) if current_topic else "the material"
        
        # Use the quiz agent to generate a multiple-choice question
        quiz_result = self.quiz_agent.process(content or topic, num_questions=1)
        
        if not quiz_result or not isinstance(quiz_result, dict) or "questions" not in quiz_result:
            self.logger.warning("Failed to generate quiz question, using fallback")
            # Create a simple feedback question as fallback
            return self._ask_for_feedback(user_id, topic)
        
        # Format the first question using the question agent
        quiz_question = quiz_result["questions"][0]
        
        # Extract options and correct answer
        options = [option["text"] for option in quiz_question.get("options", [])]
        correct_index = next((i for i, opt in enumerate(quiz_question.get("options", [])) 
                             if opt.get("is_correct", False)), 0)
        
        question = self.question_agent.process(
            content=quiz_question.get("text", "Check your understanding:"),
            question_type="multiple_choice",
            options=options,
            question_text=quiz_question.get("text", ""),
            correct_option=correct_index
        )
        
        return {
            "response": "Let's check your understanding with a quick question:",
            "has_question": True,
            "question": question,
            "teaching_mode": self.shared_state.get("teaching_mode", "conversation"),
            "requires_feedback": True
        } 