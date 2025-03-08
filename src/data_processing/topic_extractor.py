from typing import Dict, List
import google.generativeai as genai
import json
import re
import os
from .logger_config import setup_logger

class TopicExtractor:
    def __init__(self, api_keys: List[str] = None):
        self.logger = setup_logger('topic_extractor')
        self.api_keys = api_keys or []
        self.current_key_index = 0
        self.retry_count = 0
        self.max_retries = 3
        
        if not self.api_keys:
            raise ValueError("No API keys provided")
            
        try:
            self._initialize_model()
            self.logger.info("Initialized Gemini model for topic extraction")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini model: {str(e)}")
            raise

    def _initialize_model(self):
        """Initialize model with current API key"""
        if not self.api_keys:
            raise ValueError("No API keys available")
            
        genai.configure(api_key=self.api_keys[self.current_key_index])
        self.model = genai.GenerativeModel('gemini-1.5-pro')

    def _switch_api_key(self):
        """Switch to next available API key"""
        original_index = self.current_key_index
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        
        if self.current_key_index == original_index:
            raise Exception("All API keys have been tried")
            
        self._initialize_model()
        self.logger.info(f"Switched to API key {self.current_key_index + 1}")

    def extract_topics(self, text: str, max_level: int = 3) -> Dict:
        """Extract hierarchical topics from text using a single API call"""
        self.retry_count = 0
        
        while self.retry_count < self.max_retries:
            try:
                # Process text in chunks if it's very long
                if len(text) > 15000:
                    self.logger.info(f"Text is very long ({len(text)} chars), processing in chunks")
                    return self._process_long_document(text)
                
                # If no model available, return basic structure
                if not self.model:
                    self.logger.warning("No Gemini model available, returning basic topic structure")
                    return self._create_basic_structure("No AI model available")
                
                # Check if text is substantial enough
                if len(text.strip()) < 100:
                    self.logger.warning("Text too short for meaningful topic extraction")
                    return self._create_basic_structure("Text too short")
                
                # Create a single comprehensive prompt that extracts all topics and subtopics at once
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

                try:
                    response = self.model.generate_content(
                        prompt,
                        generation_config={
                            "temperature": 0.1,  # Reduced temperature for more consistent output
                            "max_output_tokens": 2000,
                            "top_p": 0.95,
                            "top_k": 40
                        }
                    )
                    
                    # Clean and parse the JSON response
                    response_text = response.text.strip()
                    
                    # Remove any non-JSON text that might be present
                    try:
                        # Find the first '{' and last '}'
                        start = response_text.find('{')
                        end = response_text.rindex('}') + 1
                        if start != -1 and end != -1:
                            response_text = response_text[start:end]
                    except ValueError:
                        self.logger.error("Could not find valid JSON markers in response")
                        return self._create_basic_structure("Invalid response format")
                    
                    try:
                        topic_structure = json.loads(response_text)
                        
                        # Validate the structure
                        if not isinstance(topic_structure, dict):
                            raise ValueError("Response is not a dictionary")
                        
                        required_keys = ["title", "content", "topics"]
                        for key in required_keys:
                            if key not in topic_structure:
                                raise ValueError(f"Missing required key: {key}")
                        
                        if not isinstance(topic_structure["topics"], list):
                            raise ValueError("Topics is not a list")
                        
                        # Ensure each topic has required structure
                        for topic in topic_structure["topics"]:
                            if not all(k in topic for k in ["title", "content", "subtopics"]):
                                raise ValueError("Topic missing required fields")
                            if not isinstance(topic["subtopics"], list):
                                topic["subtopics"] = []
                        
                        self.logger.info(f"Successfully extracted {len(topic_structure['topics'])} topics")
                        return topic_structure
                        
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Failed to parse JSON response: {str(e)}")
                        self.logger.debug(f"Response text: {response_text[:500]}")
                        return self._create_basic_structure("Failed to parse topic structure")
                    except ValueError as e:
                        self.logger.error(f"Invalid topic structure: {str(e)}")
                        return self._create_basic_structure(f"Invalid topic structure: {str(e)}")
                        
                except Exception as e:
                    if "quota" in str(e).lower():
                        self.retry_count += 1
                        try:
                            self._switch_api_key()
                            continue
                        except Exception as switch_error:
                            if self.retry_count >= self.max_retries:
                                self.logger.error("All API keys exhausted")
                                return self._create_basic_structure("API quota exceeded")
                            continue
                    else:
                        raise
                        
            except Exception as e:
                self.logger.error(f"Error extracting topics: {str(e)}")
                return self._create_basic_structure(str(e))

    def _process_long_document(self, text: str) -> Dict:
        """Process a long document by breaking it into chunks"""
        try:
            # Split into chunks of 10000 characters
            chunks = [text[i:i+10000] for i in range(0, len(text), 8000)]
            
            # Process first chunk to get document structure
            base_structure = self.extract_topics(chunks[0])
            
            # Process remaining chunks to find additional topics
            for chunk in chunks[1:]:
                chunk_topics = self.extract_topics(chunk)
                if "topics" in chunk_topics:
                    # Add non-duplicate topics
                    existing_titles = {t["title"].lower() for t in base_structure["topics"]}
                    for topic in chunk_topics["topics"]:
                        if topic["title"].lower() not in existing_titles:
                            base_structure["topics"].append(topic)
                            existing_titles.add(topic["title"].lower())
            
            return base_structure
            
        except Exception as e:
            self.logger.error(f"Error processing long document: {str(e)}")
            return self._create_basic_structure(f"Error processing long document: {str(e)}")

    def _create_basic_structure(self, reason: str) -> Dict:
        """Create a basic topic structure"""
        structure = {
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
        self.logger.info(f"Created basic structure: {reason}")
        return structure 