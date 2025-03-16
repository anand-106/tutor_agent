from typing import Dict, List, Any
from .base_agent import BaseAgent
import json
import datetime

class LessonPlanAgent(BaseAgent):
    """
    Agent responsible for generating personalized lesson plans based on topics and user knowledge.
    This agent creates structured learning paths with activities, resources, and assessments
    tailored to the user's current knowledge level.
    """
    
    def __init__(self, api_keys: List[str]):
        super().__init__(api_keys)
    
    def process(self, user_id: str, topic: str, knowledge_level: float, 
                subtopics: List[Dict] = None, time_available: int = 60) -> Dict:
        """
        Generate a personalized lesson plan for a specific topic.
        
        Args:
            user_id: Unique identifier for the user
            topic: The main topic for the lesson plan
            knowledge_level: Current knowledge level (0-100) of the user for this topic
            subtopics: Optional list of subtopics with their knowledge levels
            time_available: Available time in minutes for the lesson (default: 60)
            
        Returns:
            Dict containing the structured lesson plan
        """
        self.retry_count = 0
        
        while self.retry_count < self.max_retries:
            try:
                # Determine the appropriate learning approach based on knowledge level
                if knowledge_level < 30:
                    approach = "foundational"
                elif knowledge_level < 70:
                    approach = "intermediate"
                else:
                    approach = "advanced"
                
                # Format subtopics for the prompt
                subtopics_text = ""
                if subtopics:
                    subtopics_text = "Subtopics to include:\n"
                    for st in subtopics:
                        st_level = st.get("level", 0)
                        st_name = st.get("name", "")
                        if st_name:
                            subtopics_text += f"- {st_name} (knowledge level: {st_level})\n"
                
                prompt = f"""Generate a personalized lesson plan for a student learning about {topic}.

                IMPORTANT: Your response must be ONLY valid JSON, with no additional text or explanation.
                
                Student Profile:
                - Current knowledge level: {knowledge_level}/100 ({approach} level)
                - Available study time: {time_available} minutes
                {subtopics_text}
                
                Required JSON structure:
                {{
                    "title": "Lesson Plan: [Topic Title]",
                    "description": "Brief overview of the lesson plan",
                    "knowledge_level": "{approach}",
                    "duration_minutes": {time_available},
                    "learning_objectives": [
                        "Objective 1",
                        "Objective 2",
                        "..."
                    ],
                    "activities": [
                        {{
                            "title": "Activity title",
                            "type": "reading/exercise/discussion/quiz/etc",
                            "duration_minutes": 15,
                            "description": "Detailed description of the activity",
                            "resources": [
                                {{
                                    "title": "Resource title",
                                    "type": "article/video/interactive/etc",
                                    "description": "Brief description of the resource"
                                }}
                            ]
                        }}
                    ],
                    "assessment": {{
                        "type": "quiz/project/discussion/etc",
                        "description": "Description of how learning will be assessed",
                        "criteria": [
                            "Criterion 1",
                            "Criterion 2"
                        ]
                    }},
                    "next_steps": [
                        "Suggestion for further learning"
                    ]
                }}

                Guidelines:
                1. Tailor the plan to a {approach} knowledge level ({knowledge_level}/100)
                2. Include {3 if time_available < 60 else 4 if time_available < 120 else 5} activities that fit within {time_available} minutes
                3. For beginners (< 30), focus on foundational concepts and definitions
                4. For intermediate (30-70), focus on application and connections
                5. For advanced (> 70), focus on synthesis, evaluation, and extension
                6. Include varied activity types (reading, interactive exercises, discussions, etc.)
                7. Ensure all activities and resources are specific to {topic}
                8. Include appropriate assessment methods
                9. Suggest logical next steps for continued learning
                """

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
                
                # Extract JSON content
                start = response_text.find('{')
                end = response_text.rindex('}') + 1
                if start != -1 and end != -1:
                    response_text = response_text[start:end]
                
                lesson_plan = json.loads(response_text)
                
                # Validate structure
                required_keys = ["title", "description", "knowledge_level", "duration_minutes", 
                                "learning_objectives", "activities", "assessment", "next_steps"]
                for key in required_keys:
                    if key not in lesson_plan:
                        raise ValueError(f"Missing required key: {key}")
                
                # Add metadata
                lesson_plan["generated_at"] = datetime.datetime.now().isoformat()
                lesson_plan["user_id"] = user_id
                lesson_plan["topic"] = topic
                
                self.logger.info(f"Successfully generated lesson plan for {topic}")
                return lesson_plan

            except Exception as e:
                if "quota" in str(e).lower():
                    self.retry_count += 1
                    try:
                        self._switch_api_key()
                        continue
                    except Exception:
                        if self.retry_count >= self.max_retries:
                            self.logger.error("All API keys exhausted")
                            return self._create_basic_lesson_plan(topic, knowledge_level, time_available)
                        continue
                else:
                    self.logger.error(f"Error generating lesson plan: {str(e)}")
                    return self._create_basic_lesson_plan(topic, knowledge_level, time_available)
    
    def _create_basic_lesson_plan(self, topic: str, knowledge_level: float, time_available: int) -> Dict:
        """Create a basic lesson plan when the full generation fails"""
        approach = "foundational" if knowledge_level < 30 else "intermediate" if knowledge_level < 70 else "advanced"
        
        return {
            "title": f"Lesson Plan: {topic}",
            "description": f"Basic {approach} level introduction to {topic}",
            "knowledge_level": approach,
            "duration_minutes": time_available,
            "learning_objectives": [
                f"Understand the key concepts of {topic}",
                f"Apply basic knowledge of {topic} in simple scenarios"
            ],
            "activities": [
                {
                    "title": f"Introduction to {topic}",
                    "type": "reading",
                    "duration_minutes": time_available // 3,
                    "description": f"Read an introductory text about {topic}",
                    "resources": [
                        {
                            "title": f"{topic} fundamentals",
                            "type": "article",
                            "description": "Basic overview of the subject"
                        }
                    ]
                },
                {
                    "title": "Practice exercises",
                    "type": "exercise",
                    "duration_minutes": time_available // 3,
                    "description": "Complete basic exercises to reinforce understanding",
                    "resources": [
                        {
                            "title": "Practice worksheet",
                            "type": "worksheet",
                            "description": "Basic practice problems"
                        }
                    ]
                }
            ],
            "assessment": {
                "type": "quiz",
                "description": "Short quiz to test understanding of basic concepts",
                "criteria": [
                    "Correct identification of key concepts",
                    "Basic application of knowledge"
                ]
            },
            "next_steps": [
                f"Explore more advanced aspects of {topic}",
                "Practice with more complex examples"
            ],
            "generated_at": datetime.datetime.now().isoformat(),
            "topic": topic
        }
    
    def generate_curriculum(self, user_id: str, topics: List[Dict], total_time_available: int = 600) -> Dict:
        """
        Generate a comprehensive curriculum covering multiple topics.
        
        Args:
            user_id: Unique identifier for the user
            topics: List of topics with their knowledge levels
            total_time_available: Total available time in minutes (default: 600 - 10 hours)
            
        Returns:
            Dict containing the structured curriculum
        """
        # Sort topics by knowledge level (prioritize topics with lower knowledge)
        sorted_topics = sorted(topics, key=lambda x: x.get("level", 0))
        
        # Allocate time proportionally, with more time for less-known topics
        total_inverse_knowledge = sum(100 - t.get("level", 0) for t in sorted_topics)
        
        curriculum = {
            "title": "Personalized Learning Curriculum",
            "description": f"Comprehensive curriculum covering {len(topics)} topics",
            "total_duration_minutes": total_time_available,
            "user_id": user_id,
            "generated_at": datetime.datetime.now().isoformat(),
            "modules": []
        }
        
        for topic in sorted_topics:
            topic_name = topic.get("name", "")
            knowledge_level = topic.get("level", 0)
            
            # Allocate time inversely proportional to knowledge level
            inverse_knowledge = 100 - knowledge_level
            time_allocation = int((inverse_knowledge / total_inverse_knowledge) * total_time_available)
            
            # Generate lesson plan for this topic
            lesson_plan = self.process(
                user_id=user_id,
                topic=topic_name,
                knowledge_level=knowledge_level,
                subtopics=topic.get("subtopics", []),
                time_available=time_allocation
            )
            
            # Add to curriculum
            curriculum["modules"].append({
                "topic": topic_name,
                "knowledge_level": knowledge_level,
                "duration_minutes": time_allocation,
                "lesson_plan": lesson_plan
            })
        
        return curriculum 