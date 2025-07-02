"""
Question Generator for CLI Conversations

Generates contextual clarifying questions based on conversation state.
Uses a Strategic Analysis Template for structured business research.
"""

import os
from typing import List, Dict, Any
from ..config.models import ModelConfig
import re


class QuestionGenerator:
    """Generates contextual questions for requirement gathering"""
    
    def __init__(self, model_config: ModelConfig):
        self.model = model_config.get_cli_model()
        self.question_depth = os.getenv("CLARIFICATION_DEPTH", "standard").lower()
        self.max_questions_per_round = int(os.getenv("MAX_QUESTIONS_PER_ROUND", "3"))
        self.enable_strategic_mode = os.getenv("STRATEGIC_ANALYSIS_MODE", "true").lower() == "true"
    
    async def generate_contextual_questions(self, 
                                          conversation_history: List[Dict[str, Any]],
                                          research_domain: str,
                                          completeness_score: float,
                                          missing_requirements: List[str]) -> List[str]:
        """Generate questions based on conversation context and requirement gaps"""
        
        # Check if strategic mode is enabled and adjust approach
        if self.enable_strategic_mode and self._is_business_strategic_topic(research_domain):
            return await self._generate_strategic_questions(
                conversation_history, research_domain, completeness_score, missing_requirements
            )
        else:
            return await self._generate_standard_questions(
                conversation_history, research_domain, completeness_score, missing_requirements
            )
    
    def _is_business_strategic_topic(self, domain: str) -> bool:
        """Determine if the topic is business/strategic in nature"""
        # Primary business/strategic keywords
        primary_keywords = [
            "business", "strategy", "strategic", "market", "competitive", "organization", 
            "company", "revenue", "growth", "transformation", "innovation", "industry",
            "consulting", "planning", "executive", "leadership", "management", "mgmt",
            "economic", "financial", "investment", "merger", "acquisition", "venture",
            "corporate", "enterprise", "commercial", "operational"
        ]
        
        # Context-specific combinations (require both words)
        strategic_combinations = [
            ("business", "analysis"),
            ("market", "analysis"),
            ("competitive", "analysis"),
            ("strategic", "planning"),
            ("organizational", "development"),
            ("digital", "transformation")
        ]
        
        domain_lower = domain.lower()
        
        # Check primary keywords
        if any(keyword in domain_lower for keyword in primary_keywords):
            return True
        
        # Check strategic combinations
        for combo in strategic_combinations:
            if all(word in domain_lower for word in combo):
                return True
        
        return False
    
    async def _generate_strategic_questions(self, 
                                          conversation_history: List[Dict[str, Any]],
                                          research_domain: str,
                                          completeness_score: float,
                                          missing_requirements: List[str]) -> List[str]:
        """Generate strategic business analysis questions using Claude Code template"""
        
        # Format conversation history
        history_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in conversation_history[-5:]  # Last 5 messages for context
        ])
        
        # Determine question depth based on environment variable
        depth_instructions = self._get_depth_instructions()
        
        # Create strategic analysis prompt
        prompt = f"""You are conducting strategic business research on: {research_domain}

CONVERSATION CONTEXT:
{history_text}

ANALYSIS STATUS:
- Completeness: {completeness_score:.1%}
- Missing Areas: {', '.join(missing_requirements) if missing_requirements else 'None identified'}

Using a Strategic Analysis Template framework, generate {self.max_questions_per_round} targeted clarifying questions that follow this executive-focused approach:

{depth_instructions}

STRATEGIC QUESTION CATEGORIES TO PRIORITIZE:
1. Organization & Industry Context: Organization type, industry sector, size, business model
2. Strategic Challenge Definition: Primary question, time horizon, urgency, decision context
3. Current State Analysis: Performance baseline, known challenges, stakeholder context
4. Future State & Technology: Emerging technologies, market evolution, innovation needs
5. Analysis Scope & Constraints: Resource constraints, risk tolerance, success metrics

QUESTION QUALITY STANDARDS:
- Executive-focused: Frame questions in terms of business impact and strategic implications
- Decision-oriented: Focus on information needed for strategic recommendations
- Business-relevant: Ask about competitive advantage, market position, ROI expectations
- Actionable: Ensure responses will directly inform strategic analysis
- Time-sensitive: Respect executive time with focused, high-value questions

Format each question with a category prefix:
[CONTEXT] What industry sector and organization size are we analyzing?
[CHALLENGE] What specific strategic decision needs to be made?
[SCOPE] What are the key resource constraints and success metrics?

Generate exactly {self.max_questions_per_round} questions based on the missing information and conversation context.
"""
        
        try:
            response = await self.model.ainvoke(prompt)
            return self.parse_strategic_questions(response.content)
        except Exception as e:
            print(f"Warning: Strategic question generation failed, using fallback. Error: {str(e)}")
            return self._get_strategic_fallback_questions(missing_requirements)
    
    async def _generate_standard_questions(self, 
                                         conversation_history: List[Dict[str, Any]],
                                         research_domain: str,
                                         completeness_score: float,
                                         missing_requirements: List[str]) -> List[str]:
        """Generate standard research questions for non-business topics"""
        
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

Generate {self.max_questions_per_round} targeted clarifying questions to improve research quality. Focus on:
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
    
    def _get_depth_instructions(self) -> str:
        """Get questioning instructions based on depth preference"""
        if self.question_depth == "minimal":
            return """DEPTH: MINIMAL - Ask only 1-2 essential questions for basic strategic context.
Focus on: Primary strategic challenge and organization type."""
        elif self.question_depth == "standard":
            return """DEPTH: STANDARD - Ask 2-3 focused questions covering key strategic areas.
Focus on: Strategic challenge, organization context, and analysis scope."""
        elif self.question_depth == "comprehensive":
            return """DEPTH: COMPREHENSIVE - Ask 3-4 detailed questions for thorough strategic analysis.
Focus on: Full strategic context, market dynamics, constraints, and success criteria."""
        elif self.question_depth == "executive":
            return """DEPTH: EXECUTIVE - Ask 2-3 high-level questions focused on business impact and ROI.
Focus on: Strategic implications, competitive advantage, and financial outcomes."""
        else:
            return """DEPTH: STANDARD - Ask 2-3 focused questions covering key strategic areas."""
    
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
        
        return questions[:self.max_questions_per_round]
    
    def parse_strategic_questions(self, response_content: str) -> List[str]:
        """Parse strategic questions with category prefixes"""
        lines = response_content.strip().split('\n')
        questions = []
        
        for line in lines:
            line = line.strip()
            if line and ('?' in line):
                # Clean up formatting but preserve category prefixes
                question = re.sub(r'^[-*•]\s*', '', line)
                question = re.sub(r'^\d+\.\s*', '', question)
                # Keep [CATEGORY] prefixes for strategic questions
                questions.append(question)
        
        return questions[:self.max_questions_per_round]
    
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
    
    def _get_strategic_fallback_questions(self, missing_requirements: List[str]) -> List[str]:
        """Get strategic fallback questions based on Strategic Analysis template"""
        strategic_fallback_questions = {
            "organization_context": "[CONTEXT] What organization or industry sector requires strategic analysis?",
            "strategic_challenge": "[CHALLENGE] What specific strategic decision or challenge needs to be addressed?",
            "time_horizon": "[SCOPE] What is the strategic planning timeframe (1-3 years, 3-5 years, long-term)?",
            "decision_context": "[CONTEXT] Who are the key decision-makers and what decision will this analysis inform?",
            "current_state": "[BASELINE] What is the current market position and performance baseline?",
            "competitive_dynamics": "[MARKET] What competitive or market changes are driving the strategic need?",
            "resource_constraints": "[SCOPE] What budget, time, or capability constraints affect strategic options?",
            "success_metrics": "[METRICS] How will strategic success be measured and what are the target outcomes?",
            "stakeholders": "[CONTEXT] Who are the key internal and external stakeholders affected by this strategy?",
            "risk_tolerance": "[CONSTRAINTS] What is the organization's appetite for risk and change?"
        }
        
        questions = []
        
        # Prioritize essential strategic questions based on depth setting
        if self.question_depth == "minimal":
            essential_questions = [
                "[CONTEXT] What organization and industry sector are we analyzing?",
                "[CHALLENGE] What specific strategic challenge or opportunity requires analysis?"
            ]
            questions = essential_questions
        elif self.question_depth == "executive":
            executive_questions = [
                "[IMPACT] What strategic decision needs to be made and what's the expected ROI?",
                "[COMPETITIVE] What competitive advantage or market position are you seeking?",
                "[CONSTRAINTS] What are the key resource constraints and success metrics?"
            ]
            questions = executive_questions
        else:
            # Standard comprehensive questions
            default_questions = [
                "[CONTEXT] What organization type and industry sector require strategic analysis?",
                "[CHALLENGE] What specific strategic question or decision needs to be addressed?",
                "[SCOPE] What are the key constraints, timeframe, and success criteria?"
            ]
            questions = default_questions
        
        return questions[:self.max_questions_per_round]