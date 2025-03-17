from typing import Dict, Optional, Any
from .base_agent import BaseAgent

class DiagramAgent(BaseAgent):
    def __init__(self, api_keys: list, shared_state: Optional[Dict[str, Any]] = None):
        super().__init__(api_keys, shared_state)
        
    def process(self, text: str, diagram_type: Optional[str] = None) -> Dict:
        """Generate Mermaid diagram from text"""
        self.retry_count = 0
        
        while self.retry_count < self.max_retries:
            try:
                if len(text.strip()) < 50:
                    self.logger.warning("Text too short for meaningful diagram generation")
                    return self._create_basic_diagram("Text too short")

                # Determine diagram type if not specified
                if not diagram_type:
                    diagram_type = self._determine_diagram_type(text)

                prompt = f"""Create a Mermaid diagram that visualizes the following text.
                Use the {diagram_type} diagram type.

                Guidelines:
                1. Create a clear and focused diagram
                2. Use meaningful labels and descriptions
                3. Show relationships and connections clearly
                4. Keep the diagram simple and readable
                5. For flowcharts, use TD (top-down) direction
                6. For sequence diagrams, show clear actor interactions
                7. For class diagrams, show important relationships

                Text to visualize:
                {text[:5000]}

                Respond with ONLY:
                1. A brief explanation of what the diagram shows
                2. The Mermaid diagram code
                
                Format your response exactly like this:
                Brief explanation here...

                ```mermaid
                [Your Mermaid diagram code here]
                ```"""

                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.2,
                        "max_output_tokens": 2000,
                        "top_p": 0.95,
                        "top_k": 40
                    }
                )

                response_text = response.text.strip()
                
                # Split explanation and diagram code
                parts = response_text.split("```mermaid")
                if len(parts) != 2:
                    raise ValueError("Invalid response format")
                
                explanation = parts[0].strip()
                mermaid_code = parts[1].split("```")[0].strip()
                
                # Ensure proper diagram type prefix
                if diagram_type == "flowchart" and not mermaid_code.startswith("graph"):
                    mermaid_code = "graph TD\n" + mermaid_code
                elif diagram_type == "sequence" and not mermaid_code.startswith("sequenceDiagram"):
                    mermaid_code = "sequenceDiagram\n" + mermaid_code
                elif diagram_type == "class" and not mermaid_code.startswith("classDiagram"):
                    mermaid_code = "classDiagram\n" + mermaid_code

                self.logger.info(f"Successfully generated {diagram_type} diagram")
                return {
                    "explanation": explanation,
                    "mermaid_code": mermaid_code,
                    "diagram_type": diagram_type
                }

            except Exception as e:
                if "quota" in str(e).lower():
                    self.retry_count += 1
                    try:
                        self._switch_api_key()
                        continue
                    except Exception:
                        if self.retry_count >= self.max_retries:
                            self.logger.error("All API keys exhausted")
                            return self._create_basic_diagram("API quota exceeded")
                        continue
                else:
                    self.logger.error(f"Error generating diagram: {str(e)}")
                    return self._create_basic_diagram(str(e))

    def _determine_diagram_type(self, text: str) -> str:
        """Determine the most appropriate diagram type based on text content"""
        text_lower = text.lower()
        
        # Check for class-related content
        if any(word in text_lower for word in ['class', 'object', 'inheritance', 'method', 'attribute']):
            return 'class'
        
        # Check for sequence-related content
        if any(word in text_lower for word in ['sequence', 'interaction', 'message', 'actor', 'response']):
            return 'sequence'
        
        # Default to flowchart for process flows and other content
        return 'flowchart'

    def _create_basic_diagram(self, reason: str) -> Dict:
        """Create a basic diagram structure"""
        return {
            "explanation": f"Could not generate diagram: {reason}",
            "mermaid_code": f"""graph TD
    A[Error] --> B[{reason}]
    B --> C[Please try again with more detailed input]""",
            "diagram_type": "flowchart"
        } 