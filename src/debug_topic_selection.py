import os
import sys
import json
import logging
import argparse
import time
from typing import Dict, Any, List, Optional

# Add the project root to the path so we can import our modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("debug_topic_selection")

try:
    logger.info("Importing required modules...")
    from src.ai_interface.agents.tutor_agent import TutorAgent
    from src.ai_interface.agents.question_agent import QuestionAgent
    from src.ai_interface.agents.topic_agent import TopicAgent
    logger.info("Imports successful!")
except Exception as e:
    logger.error(f"Import error: {e}")
    sys.exit(1)

def mock_document_content():
    """Return mock document content for testing"""
    return """
    # Introduction to Artificial Intelligence

    Artificial Intelligence (AI) is a branch of computer science that aims to create systems capable of performing tasks that would normally require human intelligence. These tasks include learning, reasoning, problem-solving, perception, and language understanding.

    ## Machine Learning

    Machine Learning is a subset of AI that provides systems the ability to automatically learn and improve from experience without being explicitly programmed. It focuses on the development of computer programs that can access data and use it to learn for themselves.

    ### Supervised Learning

    Supervised learning is a type of machine learning where the algorithm is trained on labeled data. The algorithm learns to map inputs to outputs based on example input-output pairs.

    ### Unsupervised Learning

    Unsupervised learning is a type of machine learning where the algorithm is trained on unlabeled data. The algorithm learns patterns, relationships, or structures from the data without explicit guidance.

    ## Neural Networks

    Neural networks are computing systems inspired by the biological neural networks that constitute animal brains. They consist of artificial neurons that can learn to perform tasks by considering examples, generally without being programmed with task-specific rules.

    ## Natural Language Processing

    Natural Language Processing (NLP) is a field of AI that focuses on the interaction between computers and humans through natural language. The ultimate objective of NLP is to read, decipher, understand, and make sense of human language in a valuable way.

    ## Computer Vision

    Computer Vision is a field of AI that enables computers to derive meaningful information from digital images, videos, and other visual inputs and take actions or make recommendations based on that information.
    """

def generate_mock_topics():
    """Generate mock topics from the document content"""
    return {
        "status": "success",
        "topics": [
            {
                "title": "Introduction to Artificial Intelligence",
                "content": "AI is a branch of computer science that aims to create systems capable of performing tasks that would normally require human intelligence.",
                "subtopics": [
                    {"title": "Definition of AI", "content": "AI systems are designed to mimic human cognitive functions."},
                    {"title": "History of AI", "content": "The field of AI research was founded in 1956."}
                ]
            },
            {
                "title": "Machine Learning",
                "content": "Machine Learning is a subset of AI that provides systems the ability to automatically learn and improve from experience.",
                "subtopics": [
                    {"title": "Supervised Learning", "content": "Training on labeled data to map inputs to outputs."},
                    {"title": "Unsupervised Learning", "content": "Finding patterns in unlabeled data."},
                    {"title": "Reinforcement Learning", "content": "Learning through interaction with an environment."}
                ]
            },
            {
                "title": "Neural Networks",
                "content": "Computing systems inspired by biological neural networks that constitute animal brains.",
                "subtopics": [
                    {"title": "Artificial Neurons", "content": "Basic computational units of neural networks."},
                    {"title": "Deep Learning", "content": "Neural networks with multiple layers."}
                ]
            },
            {
                "title": "Natural Language Processing",
                "content": "Field of AI focusing on interaction between computers and humans through natural language.",
                "subtopics": [
                    {"title": "Text Analysis", "content": "Extracting meaning from text."},
                    {"title": "Language Generation", "content": "Creating human-like text."}
                ]
            },
            {
                "title": "Computer Vision",
                "content": "Field enabling computers to derive meaningful information from visual inputs.",
                "subtopics": [
                    {"title": "Image Recognition", "content": "Identifying objects in images."},
                    {"title": "Object Detection", "content": "Locating objects in images."}
                ]
            },
            {
                "title": "Ethics in AI",
                "content": "Addressing ethical concerns in AI development and deployment.",
                "subtopics": [
                    {"title": "Bias and Fairness", "content": "Ensuring AI systems are fair and unbiased."},
                    {"title": "Privacy", "content": "Protecting personal data in AI systems."}
                ]
            },
            {
                "title": "Future of AI",
                "content": "Emerging trends and potential developments in the field of AI.",
                "subtopics": [
                    {"title": "AGI", "content": "Artificial General Intelligence with human-like capabilities."},
                    {"title": "AI in Society", "content": "Impact of AI on work, creativity, and daily life."}
                ]
            }
        ]
    }

def print_json_file(data, filename):
    """Save data to a JSON file for testing"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Output written to {filename}")

def simulate_chat_message(question_data):
    """Format the question data as it would appear in the chat widget"""
    return {
        "response": "I've analyzed the document and identified several topics. Which one would you like to learn about?",
        "has_question": True,
        "question": question_data,
        "teaching_mode": "topic_selection"
    }

def process_topic_selection(tutor_agent, selection):
    """Process a topic selection response"""
    logger.info(f"Processing selection: {selection}")
    response = tutor_agent.process(
        context=mock_document_content(),
        query=selection,
        user_id="test_user"
    )
    return response

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Debug the topic selection flow')
    parser.add_argument('--api-keys', type=str, default="dummy_key", help='Comma-separated list of API keys')
    parser.add_argument('--output', type=str, default='debug_output.json', help='Output file for JSON')
    parser.add_argument('--selection', type=str, help='Optional topic selection (1-7) to test response handling')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Parse API keys
        api_keys = args.api_keys.split(',')
        logger.info(f"Using {len(api_keys)} API keys")
        
        # Create a tutor agent
        logger.info("Creating TutorAgent...")
        tutor_agent = TutorAgent(api_keys=api_keys)
        logger.info("TutorAgent created successfully")
        
        # Set mock topics
        logger.info("Setting mock topics...")
        mock_topics = generate_mock_topics()
        tutor_agent.set_topics(mock_topics["topics"])
        logger.info(f"Set {len(mock_topics['topics'])} topics")
        
        # Present topics as a question
        logger.info("Generating topic selection question...")
        topic_question_response = tutor_agent._present_topics_as_question()
        logger.info("Topic selection question generated")
        
        # Format as a chat message
        chat_message = simulate_chat_message(topic_question_response["question"])
        
        # Save to file
        print_json_file(chat_message, args.output)
        
        # Print the first few topics
        logger.info("\n=== TOPIC OPTIONS ===")
        for i, topic in enumerate(tutor_agent.presented_topics[:3], 1):
            logger.info(f"{i}. {topic['title']}")
        logger.info(f"... and {len(tutor_agent.presented_topics) - 3} more topics")
        
        # Process a selection if provided
        if args.selection:
            logger.info("\n=== PROCESSING SELECTION ===")
            response = process_topic_selection(tutor_agent, args.selection)
            logger.info("Response processed successfully")
            
            # Save the response
            selection_output = f"selection_{args.output}"
            print_json_file(response, selection_output)
            logger.info(f"Selection response saved to {selection_output}")
            
            # Print a summary of the response
            logger.info("\n=== SELECTION RESPONSE SUMMARY ===")
            if "lesson_plan" in response:
                logger.info(f"Lesson plan generated for: {response.get('lesson_plan', {}).get('title', 'Unknown')}")
                logger.info(f"Number of activities: {len(response.get('lesson_plan', {}).get('activities', []))}")
            else:
                logger.info(f"Response type: {response.get('teaching_mode', 'Unknown')}")
                logger.info(f"Response length: {len(response.get('response', ''))}")
        
        logger.info("\n=== DEBUG COMPLETE ===")
        logger.info(f"Test the UI with the file: {args.output}")
        
    except Exception as e:
        logger.error(f"Error in debug script: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 