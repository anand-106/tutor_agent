from typing import Dict, List
import google.generativeai as genai
import json
import re
import os
from .logger_config import setup_logger

class TopicExtractor:
    def __init__(self, api_key: str = None):
        self.logger = setup_logger('topic_extractor')
        self.api_key = api_key
        
        if api_key:
            try:
                genai.configure(api_key=api_key)
                # Use gemini-1.5-pro instead of gemini-pro
                self.model = genai.GenerativeModel('gemini-1.5-pro')
                self.logger.info("Initialized Gemini model for topic extraction")
            except Exception as e:
                self.logger.error(f"Failed to initialize Gemini model: {str(e)}")
                self.model = None
        else:
            self.logger.warning("No API key provided, topic extraction will be limited")
            self.model = None

    def extract_topics(self, text: str) -> Dict:
        """Extract hierarchical topic structure from text"""
        try:
            # Truncate text if too long
            max_length = 15000
            if len(text) > max_length:
                text = text[:max_length]
                self.logger.info(f"Text truncated from {len(text)} to {max_length} characters")
            
            # If no model available, return basic structure
            if not self.model:
                self.logger.warning("No Gemini model available, returning basic topic structure")
                return {
                    "title": "Document Title",
                    "content": "Document overview",
                    "subtopics": [
                        {
                            "title": "Document Content",
                            "content": "The document content could not be automatically structured.",
                            "subtopics": []
                        }
                    ]
                }
            
            # Extract document title
            try:
                title_prompt = f"""Extract the main title or subject of this document. 
                Return ONLY the title, nothing else.
                
                Document text:
                {text[:5000]}"""
                
                title_response = self.model.generate_content(title_prompt)
                title = title_response.text.strip()
                self.logger.info(f"Extracted document title: {title}")
            except Exception as e:
                self.logger.error(f"Error extracting document title: {str(e)}")
                title = "Document Title"
            
            # Extract main topics
            try:
                topics_prompt = f"""Analyze this document and identify the main topics or sections.
                Format your response as a simple list with one topic per line.
                Limit to 5-7 main topics maximum.
                
                Document text:
                {text}"""
                
                topics_response = self.model.generate_content(topics_prompt)
                topics_text = topics_response.text.strip()
                
                # Parse the topics
                main_topics = [
                    line.strip() for line in topics_text.split('\n') 
                    if line.strip() and not line.strip().startswith('-')
                ]
                
                # Clean up any numbering or bullets
                main_topics = [re.sub(r'^\d+\.\s*', '', topic) for topic in main_topics]
                main_topics = [re.sub(r'^[-•*]\s*', '', topic) for topic in main_topics]
                
                self.logger.info(f"Successfully extracted topics: {len(main_topics)} main topics found")
            except Exception as e:
                self.logger.error(f"Error extracting main topics: {str(e)}")
                main_topics = ["Document Content"]
            
            # Create topic structure
            topic_structure = {
                "title": title,
                "content": "Document overview",
                "subtopics": []
            }
            
            # Add main topics as subtopics
            for topic in main_topics:
                topic_structure["subtopics"].append({
                    "title": topic,
                    "content": f"Content related to {topic}",
                    "subtopics": []
                })
            
            return topic_structure
            
        except Exception as e:
            self.logger.error(f"Error in topic extraction: {str(e)}")
            # Return a basic structure on error
            return {
                "title": "Document Title",
                "content": "Document overview",
                "subtopics": [
                    {
                        "title": "Document Content",
                        "content": "The document content could not be automatically structured.",
                        "subtopics": []
                    }
                ]
            }
    
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