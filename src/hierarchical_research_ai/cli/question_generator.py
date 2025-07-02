"""
Question Generator for CLI Conversations

Generates contextual clarifying questions based on conversation state.
"""

from typing import List, Dict, Any
from ..config.models import ModelConfig
import re


class QuestionGenerator:
    """Generates contextual questions for requirement gathering"""
    
    def __init__(self, model_config: ModelConfig):
        self.model = model_config.get_cli_model()
    
    async def generate_contextual_questions(self, 
                                          conversation_history: List[Dict[str, Any]],
                                          research_domain: str,
                                          completeness_score: float,
                                          missing_requirements: List[str]) -> List[str]:
        """Generate questions based on conversation context and requirement gaps"""
        
        # Format conversation history
        history_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in conversation_history[-5:]  # Last 5 messages for context
        ])
        
        # Create prompt for question generation
        prompt = f"""Based on this research conversation about {research_domain}:

{history_text}

Current completeness: {completeness_score:.1%}
Missing information: {', '.join(missing_requirements) if missing_requirements else 'None identified'}

Generate 2-3 targeted clarifying questions to improve research quality. Focus on:
1. Missing requirement categories
2. Ambiguous or unclear specifications
3. Important details that would affect research quality

Questions should be:
- Specific and actionable
- Relevant to the research domain
- Easy for the user to answer
- Focused on critical information gaps

Format each question on a new line, starting with a dash (-).
"""
        
        try:
            response = await self.model.ainvoke(prompt)
            return self.parse_questions(response.content)
        except Exception as e:
            # Fallback to predefined questions if model fails
            print(f"Warning: Question generation failed, using fallback questions. Error: {str(e)}")
            return self._get_fallback_questions(missing_requirements)
    
    def parse_questions(self, response_content: str) -> List[str]:
        """Parse generated questions from model response"""
        lines = response_content.strip().split('\n')
        questions = []
        
        for line in lines:
            line = line.strip()
            if line and ('?' in line):
                # Clean up formatting
                question = re.sub(r'^[-*•]\s*', '', line)
                question = re.sub(r'^\d+\.\s*', '', question)
                questions.append(question)
        
        return questions[:3]  # Limit to 3 questions per round
    
    def _get_fallback_questions(self, missing_requirements: List[str]) -> List[str]:
        """Get fallback questions based on missing requirements"""
        fallback_questions = {
            "research topic": "What specific topic or question would you like to research?",
            "scope definition": "What aspects of this topic should we focus on? Are there any boundaries we should set?",
            "target audience": "Who is the intended audience for this research (e.g., academics, professionals, general public)?",
            "research methodology": "Do you have any preferences for research methods (e.g., empirical, theoretical, mixed methods)?",
            "output preferences": "What format would you prefer for the final report? Any specific sections you need?"
        }
        
        questions = []
        for req in missing_requirements[:3]:
            if req in fallback_questions:
                questions.append(fallback_questions[req])
        
        # Add general questions if needed
        if len(questions) < 2:
            general_questions = [
                "What's the primary goal or outcome you're hoping to achieve with this research?",
                "Are there any specific sources or types of evidence you'd like us to prioritize?",
                "What level of technical detail would be appropriate for your needs?",
                "Are there any time constraints or deadlines we should be aware of?",
                "Do you have any concerns about budget or resource limitations?"
            ]
            questions.extend(general_questions[:3-len(questions)])
        
        return questions