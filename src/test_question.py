import os
import sys
import json
import logging
from typing import Dict, Any, List
import argparse

print("Current directory:", os.getcwd())
print("Python path:", sys.path)

# Add the project root to the path so we can import our modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
print("Added to path:", project_root)

try:
    print("Attempting to import QuestionAgent...")
    from src.ai_interface.agents.question_agent import QuestionAgent
    from src.ai_interface.agents.base_agent import BaseAgent
    print("Import successful!")
except Exception as e:
    print(f"Import error: {e}")
    sys.exit(1)

def generate_mock_topics(num_topics: int = 5) -> List[Dict[str, Any]]:
    """Generate mock topic data for testing"""
    topics = []
    subjects = [
        "Python Programming", "Machine Learning", "Data Structures", 
        "Web Development", "Artificial Intelligence", "Computer Networks",
        "Database Systems", "Operating Systems", "Software Engineering",
        "Computer Graphics", "Natural Language Processing", "Robotics"
    ]
    
    for i in range(min(num_topics, len(subjects))):
        topic_title = subjects[i]
        topic = {
            "id": str(i + 1),
            "title": topic_title,
            "content": f"Learn about the fundamentals of {topic_title} and its applications.",
            "subtopics": [
                {
                    "id": f"{i + 1}.1",
                    "title": f"Introduction to {topic_title}",
                    "content": f"Basic concepts and principles of {topic_title}."
                },
                {
                    "id": f"{i + 1}.2",
                    "title": f"Advanced {topic_title}",
                    "content": f"Advanced techniques and methodologies in {topic_title}."
                }
            ]
        }
        topics.append(topic)
    
    return topics

def format_topics_for_question_agent(topics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format topics for the question agent"""
    formatted_topics = []
    
    for topic in topics:
        formatted_topic = {
            "id": topic.get("id", ""),
            "text": topic.get("title", ""),
            "description": topic.get("content", "")
        }
        formatted_topics.append(formatted_topic)
    
    return formatted_topics

def print_json_to_file(data: Dict[str, Any], filename: str):
    """Print JSON data to a file for easy inspection"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Output written to {filename}")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Test the QuestionAgent')
    parser.add_argument('--num-topics', type=int, default=5, help='Number of mock topics to generate')
    parser.add_argument('--output', type=str, default='question_output.json', help='Output file for the question JSON')
    parser.add_argument('--mock-file', action='store_true', help='Use mock file topics instead of generated ones')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("Creating QuestionAgent...")
    try:
        # Create mock API keys
        api_keys = ["mock_api_key_1", "mock_api_key_2"]
        
        # Create a shared state dict
        shared_state = {
            "current_question": None,
            "waiting_for_response": False
        }
        
        # Create a question agent
        question_agent = QuestionAgent(api_keys=api_keys, shared_state=shared_state)
        print("QuestionAgent created successfully")
    except Exception as e:
        print(f"Error creating QuestionAgent: {e}")
        sys.exit(1)
    
    # Generate or mock topics
    print(f"\n=== GENERATING {'MOCK FILE' if args.mock_file else 'RANDOM'} TOPICS ===\n")
    
    if args.mock_file:
        # Use a realistic structure that mimics what comes from the backend
        topics_data = {
            "status": "success",
            "topics": [
                {
                    "title": "Introduction to Machine Learning",
                    "content": "Machine Learning is a field of AI that focuses on developing systems that learn from data.",
                    "subtopics": [
                        {"title": "Supervised Learning", "content": "Learning with labeled data."},
                        {"title": "Unsupervised Learning", "content": "Learning from unlabeled data."},
                        {"title": "Reinforcement Learning", "content": "Learning through interaction with an environment."}
                    ]
                },
                {
                    "title": "Neural Networks",
                    "content": "Neural networks are computing systems inspired by biological neural networks.",
                    "subtopics": [
                        {"title": "Perceptrons", "content": "The basic unit of neural networks."},
                        {"title": "Backpropagation", "content": "Algorithm to train neural networks."}
                    ]
                },
                {
                    "title": "Natural Language Processing",
                    "content": "NLP is a field of AI that focuses on interactions between computers and human language.",
                    "subtopics": [
                        {"title": "Text Classification", "content": "Categorizing text into groups."},
                        {"title": "Named Entity Recognition", "content": "Identifying entities in text."}
                    ]
                },
                {
                    "title": "Computer Vision",
                    "content": "Computer Vision is a field of AI that enables computers to derive meaningful information from digital images and videos.",
                    "subtopics": [
                        {"title": "Image Classification", "content": "Categorizing images into groups."},
                        {"title": "Object Detection", "content": "Identifying objects in images."}
                    ]
                },
                {
                    "title": "Reinforcement Learning",
                    "content": "RL is an area of ML concerned with how software agents ought to take actions in an environment to maximize some notion of cumulative reward.",
                    "subtopics": [
                        {"title": "Q-Learning", "content": "Value-based reinforcement learning algorithm."},
                        {"title": "Policy Gradients", "content": "Direct optimization of policy."}
                    ]
                },
                {
                    "title": "Deep Learning",
                    "content": "Deep Learning is a subset of ML that involves neural networks with many layers.",
                    "subtopics": [
                        {"title": "Convolutional Neural Networks", "content": "Neural networks for image processing."},
                        {"title": "Recurrent Neural Networks", "content": "Neural networks for sequential data."}
                    ]
                },
                {
                    "title": "Generative AI",
                    "content": "Generative AI refers to AI systems that can generate new content.",
                    "subtopics": [
                        {"title": "GANs", "content": "Generative Adversarial Networks."},
                        {"title": "Diffusion Models", "content": "Probabilistic models for generating data."}
                    ]
                }
            ]
        }
        raw_topics = topics_data["topics"]
    else:
        # Generate random topics
        raw_topics = generate_mock_topics(args.num_topics)
    
    # Format topics for the question agent
    formatted_topics = format_topics_for_question_agent(raw_topics)
    
    print(f"Generated {len(formatted_topics)} topics")
    
    # Print topic titles for reference
    for topic in formatted_topics:
        print(f"- {topic['text']}")
    
    print("\n=== GENERATING TOPIC SELECTION QUESTION ===\n")
    
    try:
        # Generate a question to present the topics
        topic_question = question_agent.process(
            content=f"I have extracted {len(formatted_topics)} topics from your document. Please select one to explore.",
            question_type="topic_selection",
            options=formatted_topics,
            title="Document Topics"
        )
        print("Topic selection question generated successfully")
    except Exception as e:
        print(f"Error processing topic selection: {e}")
        sys.exit(1)
    
    # Prepare the API response format similar to what the frontend would receive
    api_response = {
        "response": "I've analyzed your document and extracted the following main topics. Which one would you like me to explain in more detail?",
        "has_question": True,
        "question": topic_question
    }
    
    # Save to file for inspection
    print_json_to_file(api_response, args.output)
    
    # Print the response in a format similar to the API response
    print("\n=== API RESPONSE ===\n")
    print(json.dumps(api_response, indent=2))
    
    print("\n=== SIMULATION COMPLETE ===\n")
    print(f"Use this JSON file to test your frontend: {args.output}")
    print("To test the response handling, modify the test script to process a sample user response.")

if __name__ == "__main__":
    main() 