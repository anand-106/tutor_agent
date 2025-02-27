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
        """Extract hierarchical topics from text"""
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
                
                # Try multiple extraction strategies and combine results
                all_topics = []
                
                # Extract main topics using a strategy based on document type
                try:
                    # Try the specific document type strategy first
                    if doc_type == "academic":
                        topics = self._extract_academic_topics(text)
                    elif doc_type == "technical":
                        topics = self._extract_technical_topics(text)
                    else:
                        topics = self._extract_general_topics(text)
                        
                    all_topics.extend(topics)
                    self.logger.info(f"Extracted {len(topics)} topics using {doc_type} strategy")
                    
                    # If we got very few topics, try the general approach as well
                    if len(topics) < 3 and doc_type != "general":
                        self.logger.info(f"Got only {len(topics)} topics, trying general approach as well")
                        general_topics = self._extract_general_topics(text)
                        
                        # Add any new topics that don't overlap with existing ones
                        existing_titles = {t["title"].lower() for t in all_topics}
                        for topic in general_topics:
                            if topic["title"].lower() not in existing_titles:
                                all_topics.append(topic)
                                existing_titles.add(topic["title"].lower())
                        
                        self.logger.info(f"Added {len(all_topics) - len(topics)} additional topics from general strategy")
                    
                    # If we still have very few topics, try a direct approach
                    if len(all_topics) < 3:
                        self.logger.info("Still have few topics, trying direct extraction")
                        direct_topics = self._extract_direct_topics(text)
                        
                        # Add any new topics
                        existing_titles = {t["title"].lower() for t in all_topics}
                        for topic in direct_topics:
                            if topic["title"].lower() not in existing_titles:
                                all_topics.append(topic)
                                existing_titles.add(topic["title"].lower())
                        
                        self.logger.info(f"Added {len(all_topics) - len(topics) - (len(general_topics) if 'general_topics' in locals() else 0)} additional topics from direct extraction")
                    
                    # Log the number of subtopics for each topic
                    for i, topic in enumerate(all_topics):
                        subtopic_count = len(topic.get("subtopics", []))
                        self.logger.info(f"Topic {i+1} '{topic['title']}' has {subtopic_count} subtopics")
                        
                        # Log second level subtopics
                        for j, subtopic in enumerate(topic.get("subtopics", [])):
                            sub_subtopic_count = len(subtopic.get("subtopics", []))
                            self.logger.info(f"  Subtopic {i+1}.{j+1} '{subtopic['title']}' has {sub_subtopic_count} sub-subtopics")
                
                except Exception as e:
                    self.logger.error(f"Error extracting main topics: {str(e)}")
                    all_topics = [{"title": "Document Content", "content": "Content could not be structured.", "subtopics": []}]
                
                # Create topic structure
                topic_structure = {
                    "title": title,
                    "content": "Document overview",
                    "subtopics": all_topics
                }
                
                return topic_structure
                
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
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

    def _process_long_document(self, text: str) -> Dict:
        """Process a long document by breaking it into chunks"""
        try:
            # Extract title from the beginning
            title_text = text[:5000]
            title_prompt = f"""Extract the main title or subject of this document. 
            If there's no clear title, create a descriptive title based on the content.
            Return ONLY the title, nothing else.
            
            Document text:
            {title_text}"""
            
            title_response = self.model.generate_content(title_prompt)
            title = title_response.text.strip()
            self.logger.info(f"Extracted document title: {title}")
            
            # Break the document into chunks of 10000 characters with 2000 character overlap
            chunk_size = 10000
            overlap = 2000
            chunks = []
            
            for i in range(0, len(text), chunk_size - overlap):
                chunk = text[i:i + chunk_size]
                chunks.append(chunk)
                
            self.logger.info(f"Split document into {len(chunks)} chunks")
            
            # Process each chunk
            all_topics = []
            existing_titles = set()
            
            for i, chunk in enumerate(chunks):
                self.logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                
                # Extract topics from this chunk
                chunk_topics = self._extract_general_topics(chunk)
                
                # Add non-duplicate topics
                for topic in chunk_topics:
                    if topic["title"].lower() not in existing_titles:
                        all_topics.append(topic)
                        existing_titles.add(topic["title"].lower())
            
            self.logger.info(f"Extracted {len(all_topics)} unique topics from all chunks")
            
            # Create topic structure
            topic_structure = {
                "title": title,
                "content": "Document overview",
                "subtopics": all_topics
            }
            
            return topic_structure
            
        except Exception as e:
            self.logger.error(f"Error processing long document: {str(e)}")
            return self._create_basic_structure(f"Error processing long document: {str(e)}")

    def _extract_direct_topics(self, text: str) -> List[Dict]:
        """Extract topics directly using a more aggressive approach"""
        try:
            prompt = """I need you to extract ALL possible topics from this document.
            Be very thorough and don't miss any important topics or sections.
            
            For each topic:
            1. Provide a clear title
            2. Write a brief description
            
            Format as a numbered list with at least 5-10 topics.
            Be comprehensive and include EVERYTHING of importance.
            
            Document text:
            {text}"""
            
            response = self.model.generate_content(
                prompt.format(text=text),
                generation_config={
                    "temperature": 0.3,  # Slightly higher temperature for more variety
                    "max_output_tokens": 2000,  # Much higher token limit
                    "top_p": 0.95,
                    "top_k": 40
                }
            )
            
            return self._parse_topic_response(response.text)
        except Exception as e:
            self.logger.error(f"Error in direct topic extraction: {str(e)}")
            return []

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
            prompt = """This appears to be an academic document. Identify all the main sections/topics.
            For each section, provide:
            1. The section title (e.g., Introduction, Methodology, Results)
            2. A brief summary of what this section covers
            
            Format your response as a numbered list with title and summary for each section.
            Include ALL important sections from the document.
            
            Document text:
            {text}"""
            
            response = self.model.generate_content(
                prompt.format(text=text),
                generation_config={"temperature": 0.1, "max_output_tokens": 1500}
            )
            
            return self._parse_topic_response(response.text)
        except Exception as e:
            self.logger.error(f"Error extracting academic topics: {str(e)}")
            return []

    def _extract_technical_topics(self, text: str) -> List[Dict]:
        """Extract topics from technical documents"""
        try:
            prompt = """This appears to be a technical document. Identify all the main sections/topics.
            For each section, provide:
            1. The section title (e.g., Installation, Configuration, API Reference)
            2. A brief summary of what this section covers
            
            Format your response as a numbered list with title and summary for each section.
            Include ALL important sections from the document.
            
            Document text:
            {text}"""
            
            response = self.model.generate_content(
                prompt.format(text=text),
                generation_config={"temperature": 0.1, "max_output_tokens": 1500}
            )
            
            return self._parse_topic_response(response.text)
        except Exception as e:
            self.logger.error(f"Error extracting technical topics: {str(e)}")
            return []

    def _extract_general_topics(self, text: str) -> List[Dict]:
        """Extract topics from general documents"""
        try:
            prompt = """Analyze this document and identify all main topics or themes.
            For each topic:
            1. Provide a clear, concise title
            2. Write a brief 1-2 sentence summary
            
            Format your response as a numbered list with title and summary for each topic.
            Be comprehensive and include ALL important topics from the document.
            
            Document text:
            {text}"""
            
            response = self.model.generate_content(
                prompt.format(text=text),
                generation_config={"temperature": 0.2, "max_output_tokens": 1500}
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
                
                # Generate subtopics for this topic
                subtopics = self._generate_subtopics(title, content, level=1)
                
                topics.append({
                    "title": title,
                    "content": content,
                    "subtopics": subtopics
                })
        
        # Strategy 2: Look for bold or emphasized titles
        if not topics:
            pattern2 = re.compile(r'(?:\*\*|\*|__)([^*_]+)(?:\*\*|\*|__)[:.-]\s*(.+?)(?=\n\s*(?:\*\*|\*|__)|$)', re.DOTALL)
            matches = pattern2.findall(response_text)
            
            if matches:
                for title, content in matches:
                    title = title.strip()
                    content = content.strip()
                    
                    # Generate subtopics for this topic
                    subtopics = self._generate_subtopics(title, content, level=1)
                    
                    topics.append({
                        "title": title,
                        "content": content,
                        "subtopics": subtopics
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
        
            # Generate subtopics for each topic
            for topic in topics:
                topic["subtopics"] = self._generate_subtopics(topic["title"], topic["content"], level=1)
        
        # If we still have no topics, create a default one
        if not topics:
            topics = [{
                "title": "Main Content",
                "content": "The document content could not be automatically structured into topics.",
                "subtopics": []
            }]
        
        return topics

    def _generate_subtopics(self, topic_title: str, topic_content: str, level: int = 1, max_level: int = 4) -> List[Dict]:
        """Generate subtopics for a topic, with support for nested levels"""
        try:
            # Skip if content is too short or we've reached max nesting level
            if len(topic_content) < 30 or level > max_level:  # Reduced minimum content length
                return []
            
            # Adjust prompt based on nesting level
            if level == 1:
                level_desc = "main"
                min_subtopics = "at least 3-5"
            elif level == 2:
                level_desc = "second-level"
                min_subtopics = "at least 2-4"
            elif level == 3:
                level_desc = "third-level"
                min_subtopics = "at least 2-3"
            else:
                level_desc = "detailed"
                min_subtopics = "at least 1-2"
            
            prompt = f"""Based on this {level_desc} topic, identify {min_subtopics} important subtopics or key points.
            
            Topic: {topic_title}
            Description: {topic_content}
            
            For each subtopic, provide:
            1. A clear, concise title
            2. A brief description (1-2 sentences)
            
            Format as a numbered list with title and description for each subtopic.
            Be thorough and don't miss any important subtopics.
            """
            
            # Try up to 2 times with different temperatures if we don't get enough subtopics
            subtopics = []
            attempts = 0
            max_attempts = 2
            
            while len(subtopics) < 2 and attempts < max_attempts:
                temperature = 0.2 + (attempts * 0.2)  # Increase temperature with each attempt
                
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": 1200,  # Further increased for more output
                        "top_p": 0.95,
                        "top_k": 40
                    }
                )
                
                # Log the response for debugging
                self.logger.debug(f"Level {level} subtopics response (attempt {attempts+1}) for '{topic_title}': {response.text[:200]}...")
                
                # Parse the response
                attempt_subtopics = self._parse_subtopics(response.text, level, max_level)
                
                if len(attempt_subtopics) > len(subtopics):
                    subtopics = attempt_subtopics
                
                attempts += 1
            
            return subtopics
            
        except Exception as e:
            self.logger.error(f"Error generating level {level} subtopics for {topic_title}: {str(e)}")
            return []

    def _parse_subtopics(self, response_text: str, level: int, max_level: int) -> List[Dict]:
        """Parse subtopics from response text"""
        subtopics = []
        
        # Strategy 1: Look for numbered items
        pattern1 = re.compile(r'(\d+)[.)\s]+([^:.\n-]+)[:.-]\s*(.+?)(?=\n\d+[.)\s]+|$)', re.DOTALL)
        matches = pattern1.findall(response_text)
        
        if matches:
            for _, title, content in matches:
                title = title.strip()
                content = content.strip()
                
                # Recursively generate next level of subtopics if not at max level
                next_level_subtopics = []
                if level < max_level:
                    next_level_subtopics = self._generate_subtopics(title, content, level=level+1, max_level=max_level)
                
                subtopics.append({
                    "title": title,
                    "content": content,
                    "subtopics": next_level_subtopics
                })
        
        # Strategy 2: Look for bold or emphasized titles
        if not subtopics:
            pattern2 = re.compile(r'(?:\*\*|\*|__)([^*_]+)(?:\*\*|\*|__)[:.-]\s*(.+?)(?=\n\s*(?:\*\*|\*|__)|$)', re.DOTALL)
            matches = pattern2.findall(response_text)
            
            if matches:
                for title, content in matches:
                    title = title.strip()
                    content = content.strip()
                    
                    # Recursively generate next level of subtopics if not at max level
                    next_level_subtopics = []
                    if level < max_level:
                        next_level_subtopics = self._generate_subtopics(title, content, level=level+1, max_level=max_level)
                    
                    subtopics.append({
                        "title": title,
                        "content": content,
                        "subtopics": next_level_subtopics
                    })
        
        # Strategy 3: Simple line-by-line parsing
        if not subtopics:
            lines = response_text.split('\n')
            current_subtopic = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Check if this looks like a title line
                if len(line) < 100 and not line.endswith('.'):
                    # Start a new subtopic
                    current_subtopic = {
                        "title": line,
                        "content": "",
                        "subtopics": []
                    }
                    subtopics.append(current_subtopic)
                elif current_subtopic:
                    # Add to current subtopic's content
                    if current_subtopic["content"]:
                        current_subtopic["content"] += " " + line
                    else:
                        current_subtopic["content"] = line
            
            # Generate next level of subtopics for each subtopic if not at max level
            if level < max_level:
                for subtopic in subtopics:
                    subtopic["subtopics"] = self._generate_subtopics(
                        subtopic["title"], 
                        subtopic["content"], 
                        level=level+1,
                        max_level=max_level
                    )
        
        return subtopics

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