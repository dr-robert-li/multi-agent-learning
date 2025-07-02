"""
Analysis Team Agents

Agents responsible for data analysis and synthesis.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_core.messages import BaseMessage
from .base_agent import BaseAgent, AgentState
import json
import re


class QuantitativeAnalysisAgent(BaseAgent):
    """Agent for quantitative data analysis"""
    
    def __init__(self, model):
        super().__init__(
            name="QuantitativeAnalysisAgent",
            model=model,
            role_description="Perform quantitative analysis, statistical evaluations, and data-driven insights"
        )
    
    async def _execute(self, messages: List[BaseMessage], state: AgentState) -> Dict[str, Any]:
        """Perform quantitative analysis"""
        # Get research data from state
        research_data = self._gather_quantitative_data(state)
        
        analysis_prompt = f"""Perform quantitative analysis on the research topic:

Available data points: {research_data}

Provide:
1. Statistical overview of the research field
2. Trend analysis (publication trends, citation patterns, etc.)
3. Quantitative comparisons between different approaches/theories
4. Data gaps and limitations
5. Visual representation suggestions (charts, graphs)
6. Key quantitative findings

Use appropriate statistical terminology and cite sources."""
        
        messages.append(BaseMessage(content=analysis_prompt, type="human"))
        
        response = await self.model.ainvoke(messages)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "analysis": response.content,
            "statistics": self._extract_statistics(response.content),
            "trends": self._extract_trends(response.content),
            "visualizations": self._suggest_visualizations(response.content),
            "key_findings": self._extract_key_findings(response.content)
        }
    
    def _gather_quantitative_data(self, state: AgentState) -> Dict[str, Any]:
        """Gather quantitative data from previous analyses"""
        data = {
            "paper_count": 0,
            "year_range": "",
            "top_venues": [],
            "citation_stats": {}
        }
        
        # Extract from literature survey if available
        if "LiteratureSurveyAgent" in state["outputs"]:
            survey = state["outputs"]["LiteratureSurveyAgent"][0]
            papers = survey.get("key_papers", [])
            data["paper_count"] = len(papers)
        
        return data
    
    def _extract_statistics(self, content: str) -> Dict[str, Any]:
        """Extract statistical information"""
        stats = {
            "numbers": [],
            "percentages": [],
            "comparisons": []
        }
        
        # Extract numbers with context
        number_pattern = r'(\d+(?:,\d+)*(?:\.\d+)?)\s*([a-zA-Z]+)'
        matches = re.findall(number_pattern, content)
        stats["numbers"] = [{"value": m[0], "context": m[1]} for m in matches[:10]]
        
        # Extract percentages
        percentage_pattern = r'(\d+(?:\.\d+)?)\s*%'
        percentages = re.findall(percentage_pattern, content)
        stats["percentages"] = percentages[:10]
        
        return stats
    
    def _extract_trends(self, content: str) -> List[str]:
        """Extract identified trends"""
        trends = []
        lines = content.split('\n')
        
        for line in lines:
            if any(word in line.lower() for word in ['trend', 'increase', 'decrease', 'growth', 'decline']):
                trends.append(line.strip())
        
        return trends[:10]
    
    def _suggest_visualizations(self, content: str) -> List[Dict[str, str]]:
        """Suggest appropriate visualizations"""
        visualizations = []
        
        # Simple heuristic-based suggestions
        if "trend" in content.lower() or "over time" in content.lower():
            visualizations.append({
                "type": "line_chart",
                "description": "Trend analysis over time"
            })
        
        if "comparison" in content.lower() or "compare" in content.lower():
            visualizations.append({
                "type": "bar_chart",
                "description": "Comparative analysis"
            })
        
        if "distribution" in content.lower() or "percentage" in content.lower():
            visualizations.append({
                "type": "pie_chart",
                "description": "Distribution analysis"
            })
        
        return visualizations
    
    def _extract_key_findings(self, content: str) -> List[str]:
        """Extract key quantitative findings"""
        findings = []
        lines = content.split('\n')
        
        for line in lines:
            if any(word in line.lower() for word in ['finding', 'result', 'significant', 'notable']):
                findings.append(line.strip())
        
        return findings[:5]


class QualitativeAnalysisAgent(BaseAgent):
    """Agent for qualitative analysis"""
    
    def __init__(self, model):
        super().__init__(
            name="QualitativeAnalysisAgent",
            model=model,
            role_description="Perform qualitative analysis, thematic analysis, and theoretical insights"
        )
    
    async def _execute(self, messages: List[BaseMessage], state: AgentState) -> Dict[str, Any]:
        """Perform qualitative analysis"""
        # Gather qualitative data from state
        qual_data = self._gather_qualitative_data(state)
        
        analysis_prompt = f"""Perform qualitative analysis on the research topic:

Research context: {qual_data}

Provide:
1. Thematic analysis of key concepts
2. Theoretical framework analysis
3. Qualitative patterns and relationships
4. Contextual factors and influences
5. Interpretive insights
6. Limitations of qualitative findings

Use appropriate qualitative research terminology."""
        
        messages.append(BaseMessage(content=analysis_prompt, type="human"))
        
        response = await self.model.ainvoke(messages)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "analysis": response.content,
            "themes": self._extract_themes(response.content),
            "frameworks": self._extract_frameworks(response.content),
            "patterns": self._extract_patterns(response.content),
            "insights": self._extract_insights(response.content)
        }
    
    def _gather_qualitative_data(self, state: AgentState) -> Dict[str, Any]:
        """Gather qualitative data from previous analyses"""
        data = {
            "domain_concepts": [],
            "research_gaps": [],
            "methodologies": []
        }
        
        if "DomainAnalysisAgent" in state["outputs"]:
            domain = state["outputs"]["DomainAnalysisAgent"][0]
            data["domain_concepts"] = domain.get("domain_map", {}).get("key_concepts", [])
            data["research_gaps"] = domain.get("research_gaps", [])
        
        return data
    
    def _extract_themes(self, content: str) -> List[Dict[str, str]]:
        """Extract themes from qualitative analysis"""
        themes = []
        lines = content.split('\n')
        
        current_theme = None
        for line in lines:
            if "theme" in line.lower():
                if ':' in line:
                    theme_name = line.split(':')[1].strip()
                    current_theme = {"name": theme_name, "description": ""}
                    themes.append(current_theme)
            elif current_theme and line.strip():
                current_theme["description"] += line.strip() + " "
        
        return themes[:8]
    
    def _extract_frameworks(self, content: str) -> List[str]:
        """Extract theoretical frameworks mentioned"""
        frameworks = []
        lines = content.split('\n')
        
        for line in lines:
            if any(word in line.lower() for word in ['framework', 'theory', 'model', 'approach']):
                frameworks.append(line.strip())
        
        return frameworks[:6]
    
    def _extract_patterns(self, content: str) -> List[str]:
        """Extract identified patterns"""
        patterns = []
        lines = content.split('\n')
        
        for line in lines:
            if any(word in line.lower() for word in ['pattern', 'relationship', 'connection', 'correlation']):
                patterns.append(line.strip())
        
        return patterns[:8]
    
    def _extract_insights(self, content: str) -> List[str]:
        """Extract key insights"""
        insights = []
        lines = content.split('\n')
        
        for line in lines:
            if any(word in line.lower() for word in ['insight', 'implication', 'suggest', 'indicate']):
                insights.append(line.strip())
        
        return insights[:6]


class SynthesisAgent(BaseAgent):
    """Agent for synthesizing quantitative and qualitative analyses"""
    
    def __init__(self, model):
        super().__init__(
            name="SynthesisAgent",
            model=model,
            role_description="Synthesize findings from multiple analyses into coherent insights and recommendations"
        )
    
    async def _execute(self, messages: List[BaseMessage], state: AgentState) -> Dict[str, Any]:
        """Synthesize analyses"""
        # Gather all analyses
        quant_analysis = state["outputs"].get("QuantitativeAnalysisAgent", [{}])[0]
        qual_analysis = state["outputs"].get("QualitativeAnalysisAgent", [{}])[0]
        
        synthesis_prompt = f"""Synthesize the quantitative and qualitative analyses:

Quantitative key findings: {quant_analysis.get('key_findings', [])}
Qualitative themes: {qual_analysis.get('themes', [])}
Patterns identified: {qual_analysis.get('patterns', [])}

Create a comprehensive synthesis that:
1. Integrates quantitative and qualitative findings
2. Identifies convergent and divergent findings
3. Develops overarching insights
4. Proposes theoretical contributions
5. Suggests practical implications
6. Recommends future research directions

Ensure the synthesis is balanced and evidence-based."""
        
        messages.append(BaseMessage(content=synthesis_prompt, type="human"))
        
        response = await self.model.ainvoke(messages)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "synthesis": response.content,
            "integrated_findings": self._extract_integrated_findings(response.content),
            "theoretical_contributions": self._extract_theoretical_contributions(response.content),
            "practical_implications": self._extract_practical_implications(response.content),
            "future_directions": self._extract_future_directions(response.content)
        }
    
    def _extract_integrated_findings(self, content: str) -> List[str]:
        """Extract integrated findings"""
        findings = []
        lines = content.split('\n')
        
        in_findings = False
        for line in lines:
            if "finding" in line.lower() or "insight" in line.lower():
                in_findings = True
            elif in_findings and line.strip():
                findings.append(line.strip())
            elif in_findings and not line.strip():
                in_findings = False
        
        return findings[:10]
    
    def _extract_theoretical_contributions(self, content: str) -> List[str]:
        """Extract theoretical contributions"""
        contributions = []
        lines = content.split('\n')
        
        for line in lines:
            if any(word in line.lower() for word in ['theoretical', 'contribution', 'framework', 'advance']):
                contributions.append(line.strip())
        
        return contributions[:5]
    
    def _extract_practical_implications(self, content: str) -> List[str]:
        """Extract practical implications"""
        implications = []
        lines = content.split('\n')
        
        for line in lines:
            if any(word in line.lower() for word in ['practical', 'implication', 'application', 'implement']):
                implications.append(line.strip())
        
        return implications[:5]
    
    def _extract_future_directions(self, content: str) -> List[str]:
        """Extract future research directions"""
        directions = []
        lines = content.split('\n')
        
        for line in lines:
            if any(word in line.lower() for word in ['future', 'research', 'direction', 'recommend', 'suggest']):
                directions.append(line.strip())
        
        return directions[:6]