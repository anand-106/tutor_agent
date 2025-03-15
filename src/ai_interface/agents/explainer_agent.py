from typing import Dict
from .base_agent import BaseAgent

class ExplainerAgent(BaseAgent):
    def process(self, text: str, query: str = "") -> Dict:
        """Generate detailed explanations from text"""
        self.retry_count = 0
        
        while self.retry_count < self.max_retries:
            try:
                if len(text.strip()) < 50:
                    self.logger.warning("Text too short for meaningful explanation")
                    return self._create_basic_explanation("Text too short")

                prompt = f"""You are an expert explainer. Your task is to provide a clear, detailed explanation based on the given text and query.
                If no specific query is provided, explain the main concepts and ideas from the text.

                Guidelines:
                1. Break down complex concepts into simpler terms
                2. Use clear examples when helpful
                3. Organize the explanation logically
                4. Highlight key points and important concepts
                5. Provide context where necessary
                6. Use analogies when appropriate to aid understanding

                Text to explain:
                {text[:8000]}

                Query (if any):
                {query}

                Format your response as a JSON object with the following structure:
                {{
                    "title": "Brief title summarizing the topic",
                    "summary": "One-paragraph overview",
                    "key_points": ["Point 1", "Point 2", ...],
                    "detailed_explanation": "Main explanation broken into paragraphs",
                    "examples": ["Example 1", "Example 2", ...],
                    "additional_notes": "Any important clarifications or context"
                }}

                Remember to provide ONLY the JSON response, no additional text."""

                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.3,
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

                explanation = self._validate_and_clean_response(response_text)
                self.logger.info("Successfully generated explanation")
                return explanation

            except Exception as e:
                if "quota" in str(e).lower():
                    self.retry_count += 1
                    try:
                        self._switch_api_key()
                        continue
                    except Exception:
                        if self.retry_count >= self.max_retries:
                            self.logger.error("All API keys exhausted")
                            return self._create_basic_explanation("API quota exceeded")
                        continue
                else:
                    self.logger.error(f"Error generating explanation: {str(e)}")
                    return self._create_basic_explanation(str(e))

    def _validate_and_clean_response(self, response_text: str) -> Dict:
        """Validate and clean the response JSON"""
        import json
        
        try:
            data = json.loads(response_text)
            
            # Ensure all required fields are present
            required_fields = ["title", "summary", "key_points", "detailed_explanation", "examples", "additional_notes"]
            for field in required_fields:
                if field not in data:
                    data[field] = ""
                    
            # Ensure key_points and examples are lists
            if not isinstance(data["key_points"], list):
                data["key_points"] = [str(data["key_points"])]
            if not isinstance(data["examples"], list):
                data["examples"] = [str(data["examples"])]
                
            return data
            
        except json.JSONDecodeError:
            return self._create_basic_explanation("Invalid response format")

    def _create_basic_explanation(self, reason: str) -> Dict:
        """Create a basic explanation structure"""
        return {
            "title": "Basic Explanation",
            "summary": f"Could not generate detailed explanation: {reason}",
            "key_points": ["Please try again with more detailed input"],
            "detailed_explanation": "The explanation generation process encountered an error.",
            "examples": ["No examples available"],
            "additional_notes": f"Error: {reason}"
        } 