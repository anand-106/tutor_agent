import os
import sys
import json
import logging
from typing import Dict, Any, List

# Add the project root to the path so we can import our modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_topics_display")

try:
    from src.ai_interface.agents.question_agent import QuestionAgent
    logger.info("Successfully imported QuestionAgent")
except Exception as e:
    logger.error(f"Failed to import QuestionAgent: {e}")
    sys.exit(1)

def main():
    # Create sample topics
    topics = [
        {
            "title": "Education and Skills",
            "content": "Anand's educational background and technical skills demonstrate a strong foundation in computer science."
        },
        {
            "title": "Project Portfolio",
            "content": "Anand has developed a diverse range of projects demonstrating practical application of technical skills."
        },
        {
            "title": "Additional Information",
            "content": "Further details about Anand's profile, including languages spoken and online presence."
        }
    ]
    
    # Create formatted topics for question agent
    formatted_topics = []
    for i, topic in enumerate(topics, 1):
        formatted_topics.append({
            "id": str(i),
            "text": topic["title"],
            "description": topic["content"]
        })
    
    logger.info(f"Created {len(formatted_topics)} formatted topics")
    for i, topic in enumerate(formatted_topics):
        logger.info(f"Topic {i+1}: {topic['text']}")
    
    # Create question agent
    api_keys = ["mock_key"]
    question_agent = QuestionAgent(api_keys=api_keys)
    
    # Generate a topic selection question
    question = question_agent.process(
        content="Please select a topic to explore",
        question_type="topic_selection",
        options=formatted_topics,
        title="Document Topics"
    )
    
    logger.info("Generated question with the following options:")
    for i, option in enumerate(question.get("options", [])):
        logger.info(f"Option {i+1}: id={option.get('id')}, text={option.get('text')}")
    
    # Save the question to a file for inspection
    with open("test_topics_question.json", "w") as f:
        json.dump(question, f, indent=2)
    logger.info("Saved question to test_topics_question.json")
    
    # Create a simulated API response
    api_response = {
        "response": "I've analyzed your document and extracted the following main topics. Which one would you like me to explain in more detail?",
        "has_question": True,
        "question": question
    }
    
    with open("test_topics_api_response.json", "w") as f:
        json.dump(api_response, f, indent=2)
    logger.info("Saved API response to test_topics_api_response.json")

if __name__ == "__main__":
    main() 