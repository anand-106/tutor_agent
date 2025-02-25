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
                return self._create_basic_structure("No AI model available")
            
            # Check if text is substantial enough
            if len(text.strip()) < 100:
                self.logger.warning("Text is too short for meaningful topic extraction")
                return self._create_basic_structure("Text too short")
            
            # Try to detect the document type/format to use appropriate extraction strategy
            doc_type = self._detect_document_type(text)
            self.logger.info(f"Detected document type: {doc_type}")
            
            # Extract document title
            try:
                title_prompt = f"""Extract the main title or subject of this document. 
                If there's no clear title, create a descriptive title based on the content.
                Return ONLY the title, nothing else.
                
                Document text:
                {text[:5000]}"""
                
                title_response = self.model.generate_content(title_prompt)
                title = title_response.text.strip()
                self.logger.info(f"Extracted document title: {title}")
            except Exception as e:
                self.logger.error(f"Error extracting document title: {str(e)}")
                title = "Document Title"
            
            # Extract main topics using a strategy based on document type
            try:
                if doc_type == "academic":
                    topics = self._extract_academic_topics(text)
                elif doc_type == "technical":
                    topics = self._extract_technical_topics(text)
                else:
                    topics = self._extract_general_topics(text)
                    
                self.logger.info(f"Successfully extracted topics: {len(topics)} main topics found")
                
                # If no topics were found, try the general approach
                if not topics and doc_type != "general":
                    self.logger.warning(f"No topics found with {doc_type} strategy, trying general approach")
                    topics = self._extract_general_topics(text)
            except Exception as e:
                self.logger.error(f"Error extracting main topics: {str(e)}")
                topics = [{"title": "Document Content", "content": "Content could not be structured.", "subtopics": []}]
            
            # Create topic structure
            topic_structure = {
                "title": title,
                "content": "Document overview",
                "subtopics": topics
            }
            
            return topic_structure
            
        except Exception as e:
            self.logger.error(f"Error in topic extraction: {str(e)}")
            # Return a basic structure on error
            return self._create_basic_structure(f"Error: {str(e)}")

    def _detect_document_type(self, text: str) -> str:
        """Detect the type of document based on content patterns"""
        try:
            # Check for academic patterns
            academic_patterns = [
                r'\b(?:abstract|introduction|methodology|conclusion|references)\b',
                r'\bcite[ds]?\b',
                r'\b(?:table|figure)\s+\d+\b',
                r'\b(?:et\s+al\.)\b'
            ]
            
            # Check for technical patterns
            technical_patterns = [
                r'\b(?:installation|configuration|setup|troubleshooting)\b',
                r'\b(?:function|method|class|object|variable)\b',
                r'\b(?:figure|diagram)\s+\d+\b',
                r'\bcode\s+example\b'
            ]
            
            # Count matches for each type
            academic_count = sum(len(re.findall(pattern, text, re.IGNORECASE)) for pattern in academic_patterns)
            technical_count = sum(len(re.findall(pattern, text, re.IGNORECASE)) for pattern in technical_patterns)
            
            if academic_count > technical_count and academic_count > 3:
                return "academic"
            elif technical_count > academic_count and technical_count > 3:
                return "technical"
            else:
                return "general"
        except Exception as e:
            self.logger.error(f"Error detecting document type: {str(e)}")
            return "general"

    def _extract_academic_topics(self, text: str) -> List[Dict]:
        """Extract topics from academic documents"""
        try:
            prompt = """This appears to be an academic document. Identify the main sections/topics.
            For each section, provide:
            1. The section title (e.g., Introduction, Methodology, Results)
            2. A brief summary of what this section covers
            
            Format your response as a numbered list with title and summary for each section.
            
            Document text:
            {text}"""
            
            response = self.model.generate_content(
                prompt.format(text=text),
                generation_config={"temperature": 0.1, "max_output_tokens": 1000}
            )
            
            return self._parse_topic_response(response.text)
        except Exception as e:
            self.logger.error(f"Error extracting academic topics: {str(e)}")
            return []

    def _extract_technical_topics(self, text: str) -> List[Dict]:
        """Extract topics from technical documents"""
        try:
            prompt = """This appears to be a technical document. Identify the main sections/topics.
            For each section, provide:
            1. The section title (e.g., Installation, Configuration, API Reference)
            2. A brief summary of what this section covers
            
            Format your response as a numbered list with title and summary for each section.
            
            Document text:
            {text}"""
            
            response = self.model.generate_content(
                prompt.format(text=text),
                generation_config={"temperature": 0.1, "max_output_tokens": 1000}
            )
            
            return self._parse_topic_response(response.text)
        except Exception as e:
            self.logger.error(f"Error extracting technical topics: {str(e)}")
            return []

    def _extract_general_topics(self, text: str) -> List[Dict]:
        """Extract topics from general documents"""
        try:
            prompt = """Analyze this document and identify 3-7 main topics or themes.
            For each topic:
            1. Provide a clear, concise title
            2. Write a brief 1-2 sentence summary
            
            Format your response as a numbered list with title and summary for each topic.
            
            Document text:
            {text}"""
            
            response = self.model.generate_content(
                prompt.format(text=text),
                generation_config={"temperature": 0.2, "max_output_tokens": 1000}
            )
            
            return self._parse_topic_response(response.text)
        except Exception as e:
            self.logger.error(f"Error extracting general topics: {str(e)}")
            return []

    def _parse_topic_response(self, response_text: str) -> List[Dict]:
        """Parse the AI response into structured topics"""
        topics = []
        
        # Try different parsing strategies
        
        # Strategy 1: Look for numbered items with title and description
        pattern1 = re.compile(r'(\d+)[.)\s]+([^:.\n-]+)[:.-]\s*(.+?)(?=\n\d+[.)\s]+|$)', re.DOTALL)
        matches = pattern1.findall(response_text)
        
        if matches:
            for _, title, content in matches:
                title = title.strip()
                content = content.strip()
                topics.append({
                    "title": title,
                    "content": content,
                    "subtopics": []
                })
        
        # Strategy 2: Look for bold or emphasized titles
        if not topics:
            pattern2 = re.compile(r'(?:\*\*|\*|__)([^*_]+)(?:\*\*|\*|__)[:.-]\s*(.+?)(?=\n\s*(?:\*\*|\*|__)|$)', re.DOTALL)
            matches = pattern2.findall(response_text)
            
            if matches:
                for title, content in matches:
                    title = title.strip()
                    content = content.strip()
                    topics.append({
                        "title": title,
                        "content": content,
                        "subtopics": []
                    })
        
        # Strategy 3: Simple line-by-line parsing
        if not topics:
            lines = response_text.split('\n')
            current_topic = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Check if this looks like a title line
                if len(line) < 100 and not line.endswith('.'):
                    # Start a new topic
                    current_topic = {
                        "title": line,
                        "content": "",
                        "subtopics": []
                    }
                    topics.append(current_topic)
                elif current_topic:
                    # Add to current topic's content
                    if current_topic["content"]:
                        current_topic["content"] += " " + line
                    else:
                        current_topic["content"] = line
        
        # If we still have no topics, create a default one
        if not topics:
            topics = [{
                "title": "Main Content",
                "content": "The document content could not be automatically structured into topics.",
                "subtopics": []
            }]
        
        return topics

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