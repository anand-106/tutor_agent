from typing import Dict, List
import google.generativeai as genai
import json
import re
import os
from .logger_config import setup_logger

class TopicExtractor:
    def __init__(self, gemini_api_key: str):
        self.logger = setup_logger('topic_extractor')
        try:
            if not gemini_api_key:
                self.logger.error("No Gemini API key provided")
                raise ValueError("Gemini API key is required for topic extraction")
                
            genai.configure(api_key=gemini_api_key)
            self.model = genai.GenerativeModel('gemini-pro')
            self.logger.info("Initialized TopicExtractor with Gemini")
        except Exception as e:
            self.logger.error(f"Failed to initialize TopicExtractor: {str(e)}")
            raise

    def extract_topics(self, text: str) -> Dict:
        """Extract topics and subtopics from text using AI"""
        try:
            if not text or len(text.strip()) < 50:
                self.logger.warning("Text is too short for meaningful topic extraction")
                return self._create_basic_structure("Empty or very short document")
            
            # Truncate text if too long
            max_length = 15000
            if len(text) > max_length:
                truncated_text = text[:max_length]
                self.logger.info(f"Text truncated from {len(text)} to {len(truncated_text)} characters")
            else:
                truncated_text = text

            # First, extract the document title
            title = self._extract_document_title(truncated_text)
            
            # Then extract main topics
            main_topics = self._extract_main_topics(truncated_text)
            
            # Create the structure
            document_structure = {
                "title": title,
                "subtopics": main_topics,
                "content": "Document overview"
            }
            
            self.logger.info(f"Successfully extracted topics: {len(main_topics)} main topics found")
            return document_structure
                
        except Exception as e:
            self.logger.error(f"Error extracting topics: {str(e)}")
            return self._create_basic_structure(f"Error: {str(e)}")
    
    def _extract_document_title(self, text: str) -> str:
        """Extract the document title using AI"""
        try:
            prompt = "What is the title or main subject of this document? Respond with just the title, no explanation.\n\nDocument text:\n{text}"
            
            response = self.model.generate_content(
                prompt.format(text=text[:2000]),  # Use just the beginning for title
                generation_config={"temperature": 0.1, "max_output_tokens": 100}
            )
            
            title = response.text.strip()
            if len(title) > 100:  # If too long, truncate
                title = title[:100] + "..."
                
            self.logger.info(f"Extracted document title: {title}")
            return title
        except Exception as e:
            self.logger.error(f"Error extracting document title: {str(e)}")
            return "Document Title"
    
    def _extract_main_topics(self, text: str) -> List[Dict]:
        """Extract main topics from text"""
        try:
            prompt = """List the 5-10 main topics or sections in this document. For each topic:
1. Provide a clear, concise title
2. Write a brief 1-2 sentence summary of what this section covers

Format each topic as a numbered list item. Don't include any other text.

Document text:
{text}"""
            
            response = self.model.generate_content(
                prompt.format(text=text),
                generation_config={"temperature": 0.2, "max_output_tokens": 1000}
            )
            
            topics_text = response.text.strip()
            self.logger.debug(f"Topics extraction response: {topics_text[:200]}...")
            
            # Parse the numbered list into topics
            topics = []
            
            # Match patterns like "1. Title: Description" or "1. Title - Description"
            topic_pattern = re.compile(r'(\d+)[.)\s]+([^:.\n-]+)[:.-]\s*(.+?)(?=\n\d+[.)\s]+|$)', re.DOTALL)
            matches = topic_pattern.findall(topics_text)
            
            if matches:
                for _, title, content in matches:
                    title = title.strip()
                    content = content.strip()
                    
                    # Create subtopics for this topic
                    subtopics = self._create_subtopics(title, content)
                    
                    topics.append({
                        "title": title,
                        "content": content,
                        "subtopics": subtopics
                    })
            
            # If parsing failed, try a simpler approach
            if not topics:
                # Split by numbered items
                simple_splits = re.split(r'\n\d+[.)\s]+', topics_text)
                for item in simple_splits:
                    if item.strip():
                        # Try to split into title and content
                        parts = item.split(':', 1)
                        if len(parts) > 1:
                            title, content = parts[0].strip(), parts[1].strip()
                        else:
                            title, content = item.strip(), ""
                        
                        topics.append({
                            "title": title,
                            "content": content,
                            "subtopics": []
                        })
            
            # If we still have no topics, create a default one
            if not topics:
                topics = [{
                    "title": "Main Content",
                    "content": "The document content could not be automatically structured into topics.",
                    "subtopics": []
                }]
                
            return topics
            
        except Exception as e:
            self.logger.error(f"Error extracting main topics: {str(e)}")
            return [{
                "title": "Document Content",
                "content": "The document content could not be automatically structured.",
                "subtopics": []
            }]
    
    def _create_subtopics(self, topic_title: str, topic_content: str) -> List[Dict]:
        """Create subtopics for a main topic"""
        try:
            # For simplicity, we'll create 2-3 subtopics based on the main topic
            prompt = f"""Based on this main topic and its description, suggest 2-3 likely subtopics.
            
Main Topic: {topic_title}
Description: {topic_content}

For each subtopic, provide:
1. A clear, concise title
2. A brief description of what this subtopic likely covers

Format as a numbered list only. No other text."""
            
            response = self.model.generate_content(
                prompt,
                generation_config={"temperature": 0.3, "max_output_tokens": 500}
            )
            
            subtopics_text = response.text.strip()
            
            # Parse the subtopics
            subtopics = []
            
            # Similar pattern as for main topics
            subtopic_pattern = re.compile(r'(\d+)[.)\s]+([^:.\n-]+)[:.-]\s*(.+?)(?=\n\d+[.)\s]+|$)', re.DOTALL)
            matches = subtopic_pattern.findall(subtopics_text)
            
            if matches:
                for _, title, content in matches:
                    subtopics.append({
                        "title": title.strip(),
                        "content": content.strip(),
                        "subtopics": []
                    })
            
            # If parsing failed, create simple subtopics
            if not subtopics:
                # Try simple splitting
                lines = subtopics_text.split('\n')
                for line in lines:
                    if line.strip():
                        subtopics.append({
                            "title": line.strip(),
                            "content": "",
                            "subtopics": []
                        })
            
            return subtopics[:3]  # Limit to 3 subtopics
            
        except Exception as e:
            self.logger.error(f"Error creating subtopics for {topic_title}: {str(e)}")
            return []
    
    def _create_basic_structure(self, reason: str) -> Dict:
        """Create a basic topic structure"""
        structure = {
            "title": "Document Structure",
            "content": f"Automatically generated structure ({reason})",
            "subtopics": [
                {
                    "title": "Main Content",
                    "content": "The document contains text but could not be automatically structured into detailed topics.",
                    "subtopics": []
                }
            ]
        }
        self.logger.info(f"Created basic structure: {reason}")
        return structure 