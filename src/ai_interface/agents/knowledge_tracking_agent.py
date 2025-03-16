from typing import Dict, List, Any
from .base_agent import BaseAgent
import json
import datetime

class KnowledgeTrackingAgent(BaseAgent):
    """
    Agent responsible for tracking user knowledge and progress across topics.
    This agent analyzes user interactions, quiz results, and study patterns
    to build a comprehensive model of user knowledge.
    """
    
    def __init__(self, api_keys: List[str]):
        super().__init__(api_keys)
        self.user_knowledge_map = {}  # Maps user_id -> topic -> knowledge level
        self.interaction_history = {}  # Maps user_id -> list of interactions
        
    def process(self, user_id: str, interaction_data: Dict[str, Any]) -> Dict:
        """
        Process a user interaction and update the knowledge model.
        
        Args:
            user_id: Unique identifier for the user
            interaction_data: Data about the interaction (quiz results, study session, etc.)
            
        Returns:
            Dict containing updated knowledge metrics
        """
        self.retry_count = 0
        
        # Initialize user data if not exists
        if user_id not in self.user_knowledge_map:
            self.user_knowledge_map[user_id] = {}
            self.interaction_history[user_id] = []
            
        # Record the interaction
        interaction_with_timestamp = {
            "timestamp": datetime.datetime.now().isoformat(),
            **interaction_data
        }
        self.interaction_history[user_id].append(interaction_with_timestamp)
        
        # Process based on interaction type
        interaction_type = interaction_data.get("type", "unknown")
        
        if interaction_type == "quiz_result":
            return self._process_quiz_result(user_id, interaction_data)
        elif interaction_type == "study_session":
            return self._process_study_session(user_id, interaction_data)
        elif interaction_type == "flashcard_review":
            return self._process_flashcard_review(user_id, interaction_data)
        elif interaction_type == "topic_view":
            return self._process_topic_view(user_id, interaction_data)
        else:
            self.logger.warning(f"Unknown interaction type: {interaction_type}")
            return {"status": "error", "message": f"Unknown interaction type: {interaction_type}"}
            
    def _process_quiz_result(self, user_id: str, data: Dict[str, Any]) -> Dict:
        """Process quiz results to update knowledge model"""
        topic = data.get("topic", "")
        score = data.get("score", 0)
        questions = data.get("questions", [])
        
        # Update topic knowledge based on quiz score
        if topic:
            current_level = self.user_knowledge_map[user_id].get(topic, {}).get("level", 0)
            
            # Calculate new knowledge level (0-100)
            if score > 80:
                new_level = min(current_level + 15, 100)
            elif score > 60:
                new_level = min(current_level + 10, 100)
            elif score > 40:
                new_level = min(current_level + 5, 100)
            else:
                # If score is very low, knowledge level might decrease
                new_level = max(current_level - 5, 0)
                
            # Update knowledge map
            self.user_knowledge_map[user_id][topic] = {
                "level": new_level,
                "last_updated": datetime.datetime.now().isoformat(),
                "quiz_attempts": self.user_knowledge_map[user_id].get(topic, {}).get("quiz_attempts", 0) + 1
            }
            
            # Process individual questions to identify specific knowledge gaps
            for question in questions:
                subtopic = question.get("subtopic", "")
                is_correct = question.get("is_correct", False)
                
                if subtopic:
                    if subtopic not in self.user_knowledge_map[user_id]:
                        self.user_knowledge_map[user_id][subtopic] = {
                            "level": 50 if is_correct else 30,  # Initial estimate
                            "last_updated": datetime.datetime.now().isoformat(),
                            "parent_topic": topic
                        }
                    else:
                        # Update subtopic knowledge
                        current_subtopic_level = self.user_knowledge_map[user_id][subtopic].get("level", 50)
                        if is_correct:
                            new_subtopic_level = min(current_subtopic_level + 10, 100)
                        else:
                            new_subtopic_level = max(current_subtopic_level - 10, 0)
                            
                        self.user_knowledge_map[user_id][subtopic]["level"] = new_subtopic_level
                        self.user_knowledge_map[user_id][subtopic]["last_updated"] = datetime.datetime.now().isoformat()
            
            return {
                "status": "success",
                "user_id": user_id,
                "topic": topic,
                "knowledge_level": new_level,
                "knowledge_change": new_level - current_level,
                "recommendations": self._generate_recommendations(user_id, topic)
            }
        
        return {"status": "error", "message": "No topic specified in quiz result"}
    
    def _process_study_session(self, user_id: str, data: Dict[str, Any]) -> Dict:
        """Process study session data to update knowledge model"""
        topic = data.get("topic", "")
        duration_minutes = data.get("duration_minutes", 0)
        
        if topic and duration_minutes > 0:
            current_level = self.user_knowledge_map[user_id].get(topic, {}).get("level", 0)
            
            # Calculate knowledge gain based on study duration
            # Diminishing returns for longer sessions
            if duration_minutes > 60:
                knowledge_gain = 10
            elif duration_minutes > 30:
                knowledge_gain = 7
            elif duration_minutes > 15:
                knowledge_gain = 5
            else:
                knowledge_gain = 3
                
            new_level = min(current_level + knowledge_gain, 100)
            
            # Update knowledge map
            self.user_knowledge_map[user_id][topic] = {
                "level": new_level,
                "last_updated": datetime.datetime.now().isoformat(),
                "study_sessions": self.user_knowledge_map[user_id].get(topic, {}).get("study_sessions", 0) + 1,
                "total_study_minutes": self.user_knowledge_map[user_id].get(topic, {}).get("total_study_minutes", 0) + duration_minutes
            }
            
            return {
                "status": "success",
                "user_id": user_id,
                "topic": topic,
                "knowledge_level": new_level,
                "knowledge_change": new_level - current_level,
                "recommendations": self._generate_recommendations(user_id, topic)
            }
            
        return {"status": "error", "message": "Invalid study session data"}
    
    def _process_flashcard_review(self, user_id: str, data: Dict[str, Any]) -> Dict:
        """Process flashcard review data to update knowledge model"""
        topic = data.get("topic", "")
        cards_reviewed = data.get("cards_reviewed", 0)
        correct_recalls = data.get("correct_recalls", 0)
        
        if topic and cards_reviewed > 0:
            current_level = self.user_knowledge_map[user_id].get(topic, {}).get("level", 0)
            
            # Calculate recall rate
            recall_rate = correct_recalls / cards_reviewed if cards_reviewed > 0 else 0
            
            # Update knowledge level based on recall rate
            if recall_rate > 0.8:
                knowledge_gain = 8
            elif recall_rate > 0.6:
                knowledge_gain = 5
            elif recall_rate > 0.4:
                knowledge_gain = 3
            else:
                knowledge_gain = 0
                
            new_level = min(current_level + knowledge_gain, 100)
            
            # Update knowledge map
            self.user_knowledge_map[user_id][topic] = {
                "level": new_level,
                "last_updated": datetime.datetime.now().isoformat(),
                "flashcard_sessions": self.user_knowledge_map[user_id].get(topic, {}).get("flashcard_sessions", 0) + 1,
                "total_cards_reviewed": self.user_knowledge_map[user_id].get(topic, {}).get("total_cards_reviewed", 0) + cards_reviewed
            }
            
            return {
                "status": "success",
                "user_id": user_id,
                "topic": topic,
                "knowledge_level": new_level,
                "knowledge_change": new_level - current_level,
                "recall_rate": recall_rate,
                "recommendations": self._generate_recommendations(user_id, topic)
            }
            
        return {"status": "error", "message": "Invalid flashcard review data"}
    
    def _process_topic_view(self, user_id: str, data: Dict[str, Any]) -> Dict:
        """Process topic view data to update knowledge model"""
        topic = data.get("topic", "")
        view_duration_seconds = data.get("view_duration_seconds", 0)
        
        if topic:
            # Just viewing a topic provides minimal knowledge gain
            current_level = self.user_knowledge_map[user_id].get(topic, {}).get("level", 0)
            
            # Small knowledge gain for viewing content
            knowledge_gain = 1 if view_duration_seconds > 30 else 0
            new_level = min(current_level + knowledge_gain, 100)
            
            # Update knowledge map
            if topic not in self.user_knowledge_map[user_id]:
                self.user_knowledge_map[user_id][topic] = {
                    "level": new_level,
                    "last_updated": datetime.datetime.now().isoformat(),
                    "views": 1
                }
            else:
                self.user_knowledge_map[user_id][topic]["level"] = new_level
                self.user_knowledge_map[user_id][topic]["last_updated"] = datetime.datetime.now().isoformat()
                self.user_knowledge_map[user_id][topic]["views"] = self.user_knowledge_map[user_id][topic].get("views", 0) + 1
            
            return {
                "status": "success",
                "user_id": user_id,
                "topic": topic,
                "knowledge_level": new_level,
                "knowledge_change": knowledge_gain,
                "recommendations": self._generate_recommendations(user_id, topic)
            }
            
        return {"status": "error", "message": "No topic specified in view data"}
    
    def _generate_recommendations(self, user_id: str, current_topic: str) -> List[Dict]:
        """Generate personalized learning recommendations based on knowledge model"""
        recommendations = []
        
        # Get current topic knowledge level
        current_level = self.user_knowledge_map[user_id].get(current_topic, {}).get("level", 0)
        
        # If knowledge level is low, recommend more study on this topic
        if current_level < 40:
            recommendations.append({
                "type": "study_more",
                "topic": current_topic,
                "reason": "Your knowledge in this area needs improvement",
                "priority": "high"
            })
            
        # Find related topics with low knowledge
        for topic, data in self.user_knowledge_map[user_id].items():
            if topic != current_topic and data.get("parent_topic") == current_topic and data.get("level", 0) < 50:
                recommendations.append({
                    "type": "review_subtopic",
                    "topic": topic,
                    "reason": "Related subtopic needs review",
                    "priority": "medium"
                })
                
        # If knowledge level is high, recommend advancing to more complex topics
        if current_level > 80:
            recommendations.append({
                "type": "advance_topic",
                "topic": current_topic,
                "reason": "You've mastered this topic, consider more advanced material",
                "priority": "low"
            })
            
        return recommendations
    
    def get_user_knowledge_summary(self, user_id: str) -> Dict:
        """Get a summary of the user's knowledge across all topics"""
        if user_id not in self.user_knowledge_map:
            return {
                "user_id": user_id,
                "topics_studied": 0,
                "average_knowledge": 0,
                "weak_topics": [],
                "medium_topics": [],
                "strong_topics": []
            }
            
        topics_data = self.user_knowledge_map[user_id]
        topic_levels = [data.get("level", 0) for data in topics_data.values()]
        average_knowledge = sum(topic_levels) / len(topic_levels) if topic_levels else 0
        
        # Organize topics by knowledge level
        weak_topics = []
        medium_topics = []
        strong_topics = []
        
        for topic, data in topics_data.items():
            level = data.get("level", 0)
            topic_info = {
                "name": topic,
                "level": level,
                "last_updated": data.get("last_updated", "")
            }
            
            if level < 40:
                weak_topics.append(topic_info)
            elif level < 70:
                medium_topics.append(topic_info)
            else:
                strong_topics.append(topic_info)
                
        # Sort topics by knowledge level
        weak_topics.sort(key=lambda x: x["level"])
        medium_topics.sort(key=lambda x: x["level"])
        strong_topics.sort(key=lambda x: x["level"], reverse=True)
        
        return {
            "user_id": user_id,
            "topics_studied": len(topics_data),
            "average_knowledge": average_knowledge,
            "weak_topics": weak_topics,
            "medium_topics": medium_topics,
            "strong_topics": strong_topics
        }
    
    def get_topic_progress(self, user_id: str, topic: str) -> Dict:
        """Get detailed progress for a specific topic"""
        if user_id not in self.user_knowledge_map or topic not in self.user_knowledge_map[user_id]:
            return {
                "user_id": user_id,
                "topic": topic,
                "knowledge_level": 0,
                "study_sessions": 0,
                "quiz_attempts": 0,
                "flashcard_sessions": 0,
                "status": "not_started"
            }
            
        topic_data = self.user_knowledge_map[user_id][topic]
        knowledge_level = topic_data.get("level", 0)
        
        # Determine status based on knowledge level
        status = "not_started"
        if knowledge_level > 0:
            if knowledge_level < 30:
                status = "beginner"
            elif knowledge_level < 60:
                status = "intermediate"
            elif knowledge_level < 90:
                status = "advanced"
            else:
                status = "mastered"
                
        return {
            "user_id": user_id,
            "topic": topic,
            "knowledge_level": knowledge_level,
            "study_sessions": topic_data.get("study_sessions", 0),
            "quiz_attempts": topic_data.get("quiz_attempts", 0),
            "flashcard_sessions": topic_data.get("flashcard_sessions", 0),
            "total_study_minutes": topic_data.get("total_study_minutes", 0),
            "status": status,
            "last_updated": topic_data.get("last_updated", "")
        }
    
    def analyze_learning_patterns(self, user_id: str) -> Dict:
        """Analyze user learning patterns and provide insights"""
        if user_id not in self.interaction_history or not self.interaction_history[user_id]:
            return {
                "user_id": user_id,
                "interaction_counts": {},
                "study_regularity": "none",
                "insights": []
            }
            
        interactions = self.interaction_history[user_id]
        
        # Count interaction types
        interaction_counts = {}
        for interaction in interactions:
            interaction_type = interaction.get("type", "unknown")
            interaction_counts[interaction_type] = interaction_counts.get(interaction_type, 0) + 1
            
        # Analyze study regularity
        timestamps = [datetime.datetime.fromisoformat(i.get("timestamp", datetime.datetime.now().isoformat())) 
                     for i in interactions]
        timestamps.sort()
        
        # Calculate average time between study sessions
        if len(timestamps) > 1:
            time_diffs = [(timestamps[i+1] - timestamps[i]).total_seconds() / 3600 
                         for i in range(len(timestamps)-1)]
            avg_hours_between = sum(time_diffs) / len(time_diffs)
            
            if avg_hours_between < 24:
                regularity = "frequent"
            elif avg_hours_between < 72:
                regularity = "regular"
            else:
                regularity = "infrequent"
        else:
            regularity = "new"
            
        # Generate insights
        insights = []
        
        # Insight on most studied topic
        topic_counts = {}
        for interaction in interactions:
            topic = interaction.get("topic", "")
            if topic:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
                
        if topic_counts:
            most_studied = max(topic_counts.items(), key=lambda x: x[1])[0]
            insights.append({
                "type": "most_studied",
                "value": most_studied,
                "description": f"You've spent the most time studying {most_studied}"
            })
            
        # Insight on study method preference
        if interaction_counts:
            preferred_method = max(interaction_counts.items(), key=lambda x: x[1])[0]
            method_description = {
                "quiz_result": "taking quizzes",
                "study_session": "focused study sessions",
                "flashcard_review": "reviewing flashcards",
                "topic_view": "browsing topics"
            }.get(preferred_method, preferred_method)
            
            insights.append({
                "type": "preferred_method",
                "value": preferred_method,
                "description": f"Your preferred study method is {method_description}"
            })
            
        # Insight on study regularity
        insights.append({
            "type": "regularity",
            "value": regularity,
            "description": f"Your study pattern is {regularity}"
        })
        
        return {
            "user_id": user_id,
            "interaction_counts": interaction_counts,
            "study_regularity": regularity,
            "insights": insights
        } 