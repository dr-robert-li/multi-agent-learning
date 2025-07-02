"""
Quality Assurance Team Agents

Agents responsible for ensuring academic quality and compliance.
"""

from typing import Dict, Any, List, Tuple
from datetime import datetime
from langchain_core.messages import BaseMessage
from .base_agent import BaseAgent, AgentState
import re


class PeerReviewAgent(BaseAgent):
    """Agent for conducting peer review of research outputs"""
    
    def __init__(self, model):
        super().__init__(
            name="PeerReviewAgent",
            model=model,
            role_description="Conduct rigorous peer review of research outputs for academic quality"
        )
    
    async def _execute(self, messages: List[BaseMessage], state: AgentState) -> Dict[str, Any]:
        """Conduct peer review"""
        # Gather all outputs for review
        synthesis = state["outputs"].get("SynthesisAgent", [{}])[0]
        research_questions = state["outputs"].get("ResearchQuestionFormulationAgent", [{}])[0]
        
        review_prompt = f"""Conduct a peer review of the research:

Research Questions: {research_questions.get('primary_question', '')}
Synthesis: {synthesis.get('synthesis', '')[:1000]}...

Evaluate:
1. Research rigor and methodology
2. Logical coherence and argumentation
3. Evidence quality and sufficiency
4. Theoretical contribution
5. Clarity and presentation
6. Limitations acknowledgment

Provide:
- Overall quality score (1-10)
- Strengths
- Weaknesses
- Recommendations for improvement
- Publication readiness assessment"""
        
        messages.append(BaseMessage(content=review_prompt, type="human"))
        
        response = await self.model.ainvoke(messages)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "review": response.content,
            "quality_score": self._extract_quality_score(response.content),
            "strengths": self._extract_strengths(response.content),
            "weaknesses": self._extract_weaknesses(response.content),
            "recommendations": self._extract_recommendations(response.content),
            "publication_ready": self._assess_publication_readiness(response.content)
        }
    
    def _extract_quality_score(self, content: str) -> float:
        """Extract quality score from review"""
        # Look for score pattern
        score_pattern = r'(?:score|rating).*?(\d+(?:\.\d+)?)\s*(?:/\s*10|out of 10)?'
        match = re.search(score_pattern, content, re.I)
        
        if match:
            score = float(match.group(1))
            return min(10.0, max(0.0, score))  # Ensure score is between 0-10
        
        # Fallback: analyze sentiment
        positive_words = ['excellent', 'strong', 'rigorous', 'comprehensive', 'thorough']
        negative_words = ['weak', 'insufficient', 'poor', 'lacking', 'inadequate']
        
        positive_count = sum(1 for word in positive_words if word in content.lower())
        negative_count = sum(1 for word in negative_words if word in content.lower())
        
        # Calculate score based on sentiment
        if positive_count > negative_count:
            return 7.0 + (positive_count - negative_count) * 0.5
        else:
            return 5.0 - (negative_count - positive_count) * 0.5
    
    def _extract_strengths(self, content: str) -> List[str]:
        """Extract identified strengths"""
        strengths = []
        lines = content.split('\n')
        
        in_strengths = False
        for line in lines:
            if "strength" in line.lower():
                in_strengths = True
            elif in_strengths and line.strip() and not any(word in line.lower() for word in ['weakness', 'recommendation']):
                strengths.append(line.strip())
            elif any(word in line.lower() for word in ['weakness', 'recommendation']):
                in_strengths = False
        
        return strengths[:5]
    
    def _extract_weaknesses(self, content: str) -> List[str]:
        """Extract identified weaknesses"""
        weaknesses = []
        lines = content.split('\n')
        
        in_weaknesses = False
        for line in lines:
            if "weakness" in line.lower() or "limitation" in line.lower():
                in_weaknesses = True
            elif in_weaknesses and line.strip() and not "recommendation" in line.lower():
                weaknesses.append(line.strip())
            elif "recommendation" in line.lower():
                in_weaknesses = False
        
        return weaknesses[:5]
    
    def _extract_recommendations(self, content: str) -> List[str]:
        """Extract recommendations for improvement"""
        recommendations = []
        lines = content.split('\n')
        
        for line in lines:
            if any(word in line.lower() for word in ['recommend', 'suggest', 'should', 'could improve']):
                recommendations.append(line.strip())
        
        return recommendations[:6]
    
    def _assess_publication_readiness(self, content: str) -> bool:
        """Assess if research is ready for publication"""
        positive_indicators = ['ready', 'suitable', 'acceptable', 'publishable']
        negative_indicators = ['not ready', 'needs work', 'significant revision', 'major issues']
        
        content_lower = content.lower()
        
        # Check for explicit statements
        for indicator in negative_indicators:
            if indicator in content_lower:
                return False
        
        for indicator in positive_indicators:
            if indicator in content_lower:
                return True
        
        # Fallback: use quality score
        score = self._extract_quality_score(content)
        return score >= 7.0


class CitationVerificationAgent(BaseAgent):
    """Agent for verifying citations and references"""
    
    def __init__(self, model):
        super().__init__(
            name="CitationVerificationAgent",
            model=model,
            role_description="Verify citations, check references, and ensure proper attribution"
        )
    
    async def _execute(self, messages: List[BaseMessage], state: AgentState) -> Dict[str, Any]:
        """Verify citations"""
        # Gather citation data from all agents
        citations = self._gather_citations(state)
        
        verification_prompt = f"""Verify citations and references:

Citations found: {len(citations)}
Sample citations: {citations[:5]}

Check for:
1. Citation format consistency
2. Complete citation information
3. Proper in-text citations
4. Reference list completeness
5. Citation style compliance (APA, MLA, etc.)
6. Potential plagiarism issues

Report any issues found and suggest corrections."""
        
        messages.append(BaseMessage(content=verification_prompt, type="human"))
        
        response = await self.model.ainvoke(messages)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "verification_report": response.content,
            "citation_count": len(citations),
            "format_issues": self._identify_format_issues(response.content),
            "missing_elements": self._identify_missing_elements(response.content),
            "style_compliance": self._assess_style_compliance(response.content),
            "recommendations": self._extract_citation_recommendations(response.content)
        }
    
    def _gather_citations(self, state: AgentState) -> List[str]:
        """Gather all citations from state"""
        citations = []
        
        for agent_name, outputs in state["outputs"].items():
            for output in outputs:
                # Extract citations from various fields
                if "key_papers" in output:
                    papers = output["key_papers"]
                    citations.extend([p.get("citation", "") for p in papers if p.get("citation")])
                
                # Look for citation patterns in text content
                for key, value in output.items():
                    if isinstance(value, str):
                        # Simple citation pattern
                        cite_pattern = r'\([A-Za-z\s&,]+,?\s*\d{4}\)'
                        matches = re.findall(cite_pattern, value)
                        citations.extend(matches)
        
        return list(set(citations))  # Deduplicate
    
    def _identify_format_issues(self, content: str) -> List[str]:
        """Identify citation format issues"""
        issues = []
        lines = content.split('\n')
        
        for line in lines:
            if any(word in line.lower() for word in ['format', 'inconsistent', 'incorrect', 'style']):
                issues.append(line.strip())
        
        return issues[:5]
    
    def _identify_missing_elements(self, content: str) -> List[str]:
        """Identify missing citation elements"""
        missing = []
        lines = content.split('\n')
        
        for line in lines:
            if any(word in line.lower() for word in ['missing', 'incomplete', 'lacks', 'needs']):
                missing.append(line.strip())
        
        return missing[:5]
    
    def _assess_style_compliance(self, content: str) -> Dict[str, Any]:
        """Assess citation style compliance"""
        styles = ['APA', 'MLA', 'Chicago', 'IEEE', 'Harvard']
        compliance = {}
        
        for style in styles:
            if style in content:
                # Check if compliant or not
                if any(word in content.lower() for word in ['compliant', 'follows', 'adheres']):
                    compliance[style] = "compliant"
                elif any(word in content.lower() for word in ['not compliant', 'violates', 'incorrect']):
                    compliance[style] = "non-compliant"
                else:
                    compliance[style] = "partially compliant"
        
        return compliance
    
    def _extract_citation_recommendations(self, content: str) -> List[str]:
        """Extract citation-related recommendations"""
        recommendations = []
        lines = content.split('\n')
        
        for line in lines:
            if any(word in line.lower() for word in ['should', 'recommend', 'suggest', 'correct', 'fix']):
                recommendations.append(line.strip())
        
        return recommendations[:6]


class AcademicStandardsComplianceAgent(BaseAgent):
    """Agent for ensuring academic standards compliance"""
    
    def __init__(self, model):
        super().__init__(
            name="AcademicStandardsComplianceAgent",
            model=model,
            role_description="Ensure compliance with academic standards, ethics, and best practices"
        )
    
    async def _execute(self, messages: List[BaseMessage], state: AgentState) -> Dict[str, Any]:
        """Check academic standards compliance"""
        # Gather relevant data
        peer_review = state["outputs"].get("PeerReviewAgent", [{}])[0]
        citation_verification = state["outputs"].get("CitationVerificationAgent", [{}])[0]
        
        compliance_prompt = f"""Assess academic standards compliance:

Quality Score: {peer_review.get('quality_score', 'N/A')}
Citation Issues: {len(citation_verification.get('format_issues', []))}

Evaluate:
1. Research ethics compliance
2. Academic integrity (plagiarism, self-citation)
3. Methodological rigor
4. Transparency and reproducibility
5. Conflict of interest declarations
6. Data availability statements
7. Limitations acknowledgment

Provide compliance assessment and recommendations."""
        
        messages.append(BaseMessage(content=compliance_prompt, type="human"))
        
        response = await self.model.ainvoke(messages)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "compliance_report": response.content,
            "ethics_compliance": self._assess_ethics_compliance(response.content),
            "integrity_check": self._check_academic_integrity(response.content),
            "transparency_score": self._assess_transparency(response.content),
            "compliance_issues": self._identify_compliance_issues(response.content),
            "recommendations": self._extract_compliance_recommendations(response.content),
            "overall_compliance": self._calculate_overall_compliance(response.content)
        }
    
    def _assess_ethics_compliance(self, content: str) -> Dict[str, Any]:
        """Assess research ethics compliance"""
        ethics_aspects = {
            "human_subjects": "not applicable",
            "data_privacy": "compliant",
            "informed_consent": "not applicable",
            "ethical_approval": "not required"
        }
        
        content_lower = content.lower()
        
        # Check for ethics mentions
        if "human subject" in content_lower:
            ethics_aspects["human_subjects"] = "requires review"
        if "privacy" in content_lower or "confidential" in content_lower:
            ethics_aspects["data_privacy"] = "needs attention"
        if "consent" in content_lower:
            ethics_aspects["informed_consent"] = "required"
        if "ethics committee" in content_lower or "irb" in content_lower:
            ethics_aspects["ethical_approval"] = "required"
        
        return ethics_aspects
    
    def _check_academic_integrity(self, content: str) -> Dict[str, bool]:
        """Check for academic integrity issues"""
        integrity_check = {
            "plagiarism_risk": False,
            "self_citation_excessive": False,
            "data_fabrication_risk": False,
            "authorship_concerns": False
        }
        
        content_lower = content.lower()
        
        if "plagiar" in content_lower:
            integrity_check["plagiarism_risk"] = True
        if "self-citation" in content_lower and "excessive" in content_lower:
            integrity_check["self_citation_excessive"] = True
        if "data" in content_lower and any(word in content_lower for word in ["fabricat", "manipulat"]):
            integrity_check["data_fabrication_risk"] = True
        if "authorship" in content_lower and any(word in content_lower for word in ["concern", "issue"]):
            integrity_check["authorship_concerns"] = True
        
        return integrity_check
    
    def _assess_transparency(self, content: str) -> float:
        """Assess research transparency score"""
        transparency_indicators = [
            "data available",
            "code available",
            "methodology clear",
            "limitations acknowledged",
            "reproducible",
            "open access"
        ]
        
        score = 0.0
        content_lower = content.lower()
        
        for indicator in transparency_indicators:
            if indicator in content_lower:
                score += 1.67  # Each indicator worth ~1.67 points out of 10
        
        return min(10.0, score)
    
    def _identify_compliance_issues(self, content: str) -> List[str]:
        """Identify compliance issues"""
        issues = []
        lines = content.split('\n')
        
        for line in lines:
            if any(word in line.lower() for word in ['issue', 'concern', 'violation', 'non-compliant', 'problem']):
                issues.append(line.strip())
        
        return issues[:8]
    
    def _extract_compliance_recommendations(self, content: str) -> List[str]:
        """Extract compliance recommendations"""
        recommendations = []
        lines = content.split('\n')
        
        for line in lines:
            if any(word in line.lower() for word in ['should', 'must', 'require', 'recommend']):
                recommendations.append(line.strip())
        
        return recommendations[:6]
    
    def _calculate_overall_compliance(self, content: str) -> str:
        """Calculate overall compliance level"""
        # Count positive and negative indicators
        positive_words = ['compliant', 'satisfactory', 'meets', 'adheres', 'follows']
        negative_words = ['non-compliant', 'violates', 'fails', 'issues', 'concerns']
        
        content_lower = content.lower()
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if negative_count > positive_count:
            return "Needs Improvement"
        elif positive_count > negative_count * 2:
            return "Fully Compliant"
        else:
            return "Partially Compliant"