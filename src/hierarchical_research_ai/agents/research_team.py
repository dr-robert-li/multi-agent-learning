"""
Research Team Agents

Agents responsible for initial research planning and data collection.
"""

from typing import Dict, Any, List
from datetime import datetime
from langchain_core.messages import BaseMessage, AIMessage
from .base_agent import BaseAgent, AgentState
import json


class DomainAnalysisAgent(BaseAgent):
    """Agent for analyzing research domains and identifying key areas"""
    
    def __init__(self, model):
        super().__init__(
            name="DomainAnalysisAgent",
            model=model,
            role_description="Analyze research domains, identify key concepts, theories, and research gaps"
        )
    
    async def _execute(self, messages: List[BaseMessage], state: AgentState) -> Dict[str, Any]:
        """Analyze the research domain"""
        # Add specific instructions for domain analysis
        analysis_prompt = """Analyze the research domain and provide:
1. Key concepts and definitions
2. Major theories and frameworks
3. Current research trends
4. Identified gaps in existing research
5. Recommended focus areas

Structure your analysis in a clear, academic format."""
        
        messages.append(BaseMessage(content=analysis_prompt, type="human"))
        
        # Get model response
        response = await self.model.ainvoke(messages)
        
        # Parse and structure the output
        return {
            "timestamp": datetime.now().isoformat(),
            "analysis": response.content,
            "domain_map": self._extract_domain_map(response.content),
            "research_gaps": self._extract_research_gaps(response.content)
        }
    
    def _extract_domain_map(self, content: str) -> Dict[str, Any]:
        """Extract structured domain map from analysis"""
        # Simple extraction logic - in production, use more sophisticated NLP
        domain_map = {
            "key_concepts": [],
            "theories": [],
            "methodologies": [],
            "applications": []
        }
        
        # Extract sections based on keywords
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            if "concept" in line.lower():
                current_section = "key_concepts"
            elif "theor" in line.lower():
                current_section = "theories"
            elif "method" in line.lower():
                current_section = "methodologies"
            elif "application" in line.lower():
                current_section = "applications"
            elif current_section and line.strip():
                domain_map[current_section].append(line.strip())
        
        return domain_map
    
    def _extract_research_gaps(self, content: str) -> List[str]:
        """Extract identified research gaps"""
        gaps = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if "gap" in line.lower() or "limitation" in line.lower():
                # Get this line and potentially the next one
                gaps.append(line.strip())
                if i + 1 < len(lines):
                    gaps.append(lines[i + 1].strip())
        
        return [gap for gap in gaps if gap]


class LiteratureSurveyAgent(BaseAgent):
    """Agent for conducting comprehensive literature surveys"""
    
    def __init__(self, model):
        super().__init__(
            name="LiteratureSurveyAgent",
            model=model,
            role_description="Conduct comprehensive literature surveys, identify seminal works and recent developments"
        )
    
    async def _execute(self, messages: List[BaseMessage], state: AgentState) -> Dict[str, Any]:
        """Conduct literature survey"""
        survey_prompt = """Conduct a comprehensive literature survey including:
1. Seminal works in the field
2. Recent publications (last 5 years)
3. Key authors and research groups
4. Major journals and conferences
5. Methodological approaches used
6. Conflicting findings or debates

Organize by themes and provide proper citations."""
        
        messages.append(BaseMessage(content=survey_prompt, type="human"))
        
        response = await self.model.ainvoke(messages)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "survey": response.content,
            "key_papers": self._extract_key_papers(response.content),
            "authors": self._extract_key_authors(response.content),
            "themes": self._extract_themes(response.content)
        }
    
    def _extract_key_papers(self, content: str) -> List[Dict[str, str]]:
        """Extract key papers from survey"""
        papers = []
        lines = content.split('\n')
        
        for line in lines:
            # Look for citation patterns
            if '(' in line and ')' in line and any(year in line for year in ['202', '201', '200']):
                paper = {
                    "citation": line.strip(),
                    "type": "recent" if '202' in line else "seminal"
                }
                papers.append(paper)
        
        return papers[:20]  # Limit to top 20
    
    def _extract_key_authors(self, content: str) -> List[str]:
        """Extract key authors mentioned"""
        authors = []
        # Simple extraction - look for capitalized names
        import re
        
        # Pattern for names (simplified)
        name_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
        matches = re.findall(name_pattern, content)
        
        # Deduplicate and return top authors
        seen = set()
        for match in matches:
            if match not in seen and "Research" not in match:
                seen.add(match)
                authors.append(match)
        
        return authors[:10]
    
    def _extract_themes(self, content: str) -> List[str]:
        """Extract research themes"""
        themes = []
        lines = content.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['theme', 'topic', 'area', 'field']):
                themes.append(line.strip())
        
        return themes[:10]


class ResearchQuestionFormulationAgent(BaseAgent):
    """Agent for formulating precise research questions"""
    
    def __init__(self, model):
        super().__init__(
            name="ResearchQuestionFormulationAgent",
            model=model,
            role_description="Formulate precise, answerable research questions based on domain analysis and gaps"
        )
    
    async def _execute(self, messages: List[BaseMessage], state: AgentState) -> Dict[str, Any]:
        """Formulate research questions"""
        # Get domain analysis and literature survey from state
        domain_analysis = state["outputs"].get("DomainAnalysisAgent", [{}])[0]
        literature_survey = state["outputs"].get("LiteratureSurveyAgent", [{}])[0]
        
        formulation_prompt = f"""Based on the domain analysis and literature survey, formulate:

1. Primary research question (overarching)
2. 3-5 sub-questions that support the primary question
3. Hypotheses (if applicable)
4. Expected contributions to the field
5. Methodology recommendations

Domain gaps identified: {domain_analysis.get('research_gaps', [])}
Key themes: {literature_survey.get('themes', [])}

Ensure questions are:
- Specific and measurable
- Achievable within scope
- Relevant to current research
- Time-bound where appropriate"""
        
        messages.append(BaseMessage(content=formulation_prompt, type="human"))
        
        response = await self.model.ainvoke(messages)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "formulation": response.content,
            "primary_question": self._extract_primary_question(response.content),
            "sub_questions": self._extract_sub_questions(response.content),
            "hypotheses": self._extract_hypotheses(response.content),
            "methodology": self._extract_methodology(response.content)
        }
    
    def _extract_primary_question(self, content: str) -> str:
        """Extract the primary research question"""
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if "primary" in line.lower() and "question" in line.lower():
                # Return the next non-empty line
                for j in range(i + 1, min(i + 5, len(lines))):
                    if lines[j].strip() and '?' in lines[j]:
                        return lines[j].strip()
        
        # Fallback: return first question found
        for line in lines:
            if '?' in line:
                return line.strip()
        
        return "Research question not clearly identified"
    
    def _extract_sub_questions(self, content: str) -> List[str]:
        """Extract sub-questions"""
        questions = []
        lines = content.split('\n')
        
        in_sub_questions = False
        for line in lines:
            if "sub-question" in line.lower() or "secondary" in line.lower():
                in_sub_questions = True
            elif in_sub_questions and '?' in line:
                questions.append(line.strip())
            elif in_sub_questions and not line.strip():
                in_sub_questions = False
        
        return questions[:5]
    
    def _extract_hypotheses(self, content: str) -> List[str]:
        """Extract hypotheses if present"""
        hypotheses = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if "hypothesis" in line.lower() or "hypotheses" in line.lower():
                # Get next few lines
                for j in range(i + 1, min(i + 6, len(lines))):
                    if lines[j].strip():
                        hypotheses.append(lines[j].strip())
        
        return hypotheses
    
    def _extract_methodology(self, content: str) -> str:
        """Extract methodology recommendations"""
        lines = content.split('\n')
        methodology = []
        
        in_methodology = False
        for line in lines:
            if "methodolog" in line.lower():
                in_methodology = True
            elif in_methodology and line.strip():
                methodology.append(line.strip())
            elif in_methodology and not line.strip():
                break
        
        return ' '.join(methodology)