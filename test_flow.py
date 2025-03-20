#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import json
import sys
import os
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("test_flow")

# Parse arguments
parser = argparse.ArgumentParser(description='Test the teaching flow functionality')
parser.add_argument('--output', type=str, default='flow_test_output.json', help='Output file for the flow test results')
parser.add_argument('--topic_id', type=str, default='1', help='ID of the topic to teach (default: 1)')
args = parser.parse_args()

logger.info("Importing required modules...")
try:
    # Import the TutorAgent
    from src.ai_interface.agents.tutor_agent import TutorAgent
except Exception as e:
    logger.error(f"Error importing modules: {e}")
    sys.exit(1)
logger.info("Imports successful!")

def main():
    try:
        # Check if API key is available
        api_keys = os.environ.get("OPENAI_API_KEY", "").split(",")
        if not api_keys or not api_keys[0]:
            logger.error("No OpenAI API key found in environment variables")
            sys.exit(1)
        
        logger.info(f"Using {len(api_keys)} API keys")
        
        # Create TutorAgent
        logger.info("Creating TutorAgent...")
        tutor_agent = TutorAgent()
        logger.info("TutorAgent created successfully")
        
        # Set mock topics
        logger.info("Setting mock topics...")
        mock_topics = [
            {
                "title": "Introduction to Artificial Intelligence",
                "content": "AI is a branch of computer science that aims to create systems capable of performing tasks that would normally require human intelligence.",
                "subtopics": [
                    {
                        "title": "Definition of AI",
                        "content": "AI systems are designed to mimic human cognitive functions."
                    },
                    {
                        "title": "History of AI",
                        "content": "The field of AI research was founded in 1956."
                    }
                ]
            },
            {
                "title": "Machine Learning",
                "content": "Machine Learning is a subset of AI that provides systems the ability to automatically learn and improve from experience.",
                "subtopics": [
                    {
                        "title": "Supervised Learning",
                        "content": "Training on labeled data to map inputs to outputs."
                    },
                    {
                        "title": "Unsupervised Learning",
                        "content": "Finding patterns in unlabeled data."
                    },
                    {
                        "title": "Reinforcement Learning",
                        "content": "Learning through interaction with an environment."
                    }
                ]
            },
            {
                "title": "Neural Networks",
                "content": "Computing systems inspired by biological neural networks that constitute animal brains.",
                "subtopics": [
                    {
                        "title": "Artificial Neurons",
                        "content": "Basic computational units of neural networks."
                    },
                    {
                        "title": "Deep Learning",
                        "content": "Neural networks with multiple layers."
                    }
                ]
            },
            {
                "title": "Natural Language Processing",
                "content": "Field of AI focusing on interaction between computers and humans through natural language.",
                "subtopics": [
                    {
                        "title": "Text Analysis",
                        "content": "Extracting meaning from text."
                    },
                    {
                        "title": "Language Generation",
                        "content": "Creating human-like text."
                    }
                ]
            },
            {
                "title": "Computer Vision",
                "content": "Field enabling computers to derive meaningful information from visual inputs.",
                "subtopics": [
                    {
                        "title": "Image Recognition",
                        "content": "Identifying objects in images."
                    },
                    {
                        "title": "Object Detection",
                        "content": "Locating objects in images."
                    }
                ]
            },
            {
                "title": "Ethics in AI",
                "content": "Addressing ethical concerns in AI development and deployment.",
                "subtopics": [
                    {
                        "title": "Bias and Fairness",
                        "content": "Ensuring AI systems are fair and unbiased."
                    },
                    {
                        "title": "Privacy",
                        "content": "Protecting personal data in AI systems."
                    }
                ]
            },
            {
                "title": "Future of AI",
                "content": "Emerging trends and potential developments in the field of AI.",
                "subtopics": [
                    {
                        "title": "AGI",
                        "content": "Artificial General Intelligence with human-like capabilities."
                    },
                    {
                        "title": "AI in Society",
                        "content": "Impact of AI on work, creativity, and daily life."
                    }
                ]
            }
        ]
        
        tutor_agent.shared_state["topics"] = mock_topics
        logger.info(f"Set {len(mock_topics)} topics")
        
        # Simulate topic selection by directly calling the process method with a start flow command
        logger.info(f"Testing teaching flow with topic ID: {args.topic_id}")
        response = tutor_agent.process(f"!start_flow:{args.topic_id}", "test_user")
        
        # Write the output to a file
        logger.info(f"Writing response to {args.output}")
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(response, f, indent=2)
        
        logger.info(f"Output written to {args.output}")
        logger.info("\n=== FLOW TEST COMPLETE ===")
        logger.info(f"Test the UI with the file: {args.output}")
        
        # Print a summary of the response
        logger.info("\n=== RESPONSE SUMMARY ===")
        try:
            if "teaching_mode" in response:
                logger.info(f"Teaching mode: {response['teaching_mode']}")
            if "flow" in response:
                logger.info(f"Flow structure has {len(response['flow']['topics'])} topics")
                logger.info(f"Current position: {response['flow']['current_position']}")
            if "response" in response:
                logger.info(f"Response message: {response['response'][:100]}...")
        except Exception as e:
            logger.error(f"Error summarizing response: {e}")
        
    except Exception as e:
        logger.error(f"Error in debug script: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 