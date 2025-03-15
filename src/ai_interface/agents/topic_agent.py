from typing import Dict
from .base_agent import BaseAgent
import json

class TopicAgent(BaseAgent):
    def process(self, text: str, max_level: int = 3) -> Dict:
        """Extract hierarchical topics from text"""
        self.retry_count = 0
        
        while self.retry_count < self.max_retries:
            try:
                if len(text) > 15000:
                    self.logger.info(f"Text is very long ({len(text)} chars), processing in chunks")
                    return self._process_long_document(text)

                if len(text.strip()) < 100:
                    self.logger.warning("Text too short for meaningful topic extraction")
                    return self._create_basic_structure("Text too short")

                prompt = f"""You are a topic extraction expert. Your task is to analyze the given document and create a hierarchical topic structure.

                IMPORTANT: Your response must be ONLY valid JSON, with no additional text or explanation.
                
                Required JSON structure:
                {{
                    "title": "Clear and concise document title",
                    "content": "Brief 1-2 sentence document overview",
                    "topics": [
                        {{
                            "title": "Main Topic Title",
                            "content": "Clear description of the topic",
                            "subtopics": [
                                {{
                                    "title": "Subtopic Title",
                                    "content": "Clear description of the subtopic",
                                    "subtopics": []
                                }}
                            ]
                        }}
                    ]
                }}

                Requirements:
                1. Title: Create a clear, descriptive title (max 10 words)
                2. Content: Write a concise document overview (1-2 sentences)
                3. Topics: Extract 3-7 main topics
                4. For each topic:
                   - Title: Clear, specific title (3-7 words)
                   - Content: Brief description (1-2 sentences)
                   - Subtopics: 2-4 relevant subtopics
                5. For each subtopic:
                   - Title: Clear, specific title
                   - Content: Brief description
                   - Nested subtopics if relevant (max {max_level} levels)
                6. All content must be factual and based on the document
                7. Response must be valid JSON only

                Document text to analyze:
                {text[:10000]}"""

                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.1,
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
                
                topic_structure = json.loads(response_text)
                
                # Validate structure
                if not isinstance(topic_structure, dict):
                    raise ValueError("Response is not a dictionary")
                
                required_keys = ["title", "content", "topics"]
                for key in required_keys:
                    if key not in topic_structure:
                        raise ValueError(f"Missing required key: {key}")
                
                if not isinstance(topic_structure["topics"], list):
                    raise ValueError("Topics is not a list")
                
                for topic in topic_structure["topics"]:
                    if not all(k in topic for k in ["title", "content", "subtopics"]):
                        raise ValueError("Topic missing required fields")
                    if not isinstance(topic["subtopics"], list):
                        topic["subtopics"] = []
                
                self.logger.info(f"Successfully extracted {len(topic_structure['topics'])} topics")
                return topic_structure

            except Exception as e:
                if "quota" in str(e).lower():
                    self.retry_count += 1
                    try:
                        self._switch_api_key()
                        continue
                    except Exception:
                        if self.retry_count >= self.max_retries:
                            self.logger.error("All API keys exhausted")
                            return self._create_basic_structure("API quota exceeded")
                        continue
                else:
                    self.logger.error(f"Error extracting topics: {str(e)}")
                    return self._create_basic_structure(str(e))

    def _process_long_document(self, text: str) -> Dict:
        """Process a long document by breaking it into chunks"""
        chunks = [text[i:i+10000] for i in range(0, len(text), 8000)]
        base_structure = self.process(chunks[0])
        
        for chunk in chunks[1:]:
            chunk_topics = self.process(chunk)
            if "topics" in chunk_topics:
                existing_titles = {t["title"].lower() for t in base_structure["topics"]}
                for topic in chunk_topics["topics"]:
                    if topic["title"].lower() not in existing_titles:
                        base_structure["topics"].append(topic)
                        existing_titles.add(topic["title"].lower())
        
        return base_structure

    def _create_basic_structure(self, reason: str) -> Dict:
        """Create a basic topic structure"""
        return {
            "title": "Document Structure",
            "content": f"Automatically generated structure ({reason})",
            "topics": [
                {
                    "title": "Main Content",
                    "content": "The document contains text but could not be automatically structured into detailed topics.",
                    "subtopics": []
                }
            ]
        } 