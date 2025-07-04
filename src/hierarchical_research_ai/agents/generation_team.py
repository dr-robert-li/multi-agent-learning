"""
Report Generation Team Agents

Agents responsible for writing and assembling the final research report.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_core.messages import BaseMessage
from .base_agent import BaseAgent, AgentState
import json
import re


class SectionWritingAgent(BaseAgent):
    """Agent for writing individual report sections"""
    
    def __init__(self, model):
        super().__init__(
            name="SectionWritingAgent",
            model=model,
            role_description="Write clear, academic-quality sections of the research report"
        )
        self.section_templates = self._load_section_templates()
    
    def _load_section_templates(self) -> Dict[str, str]:
        """Load section templates"""
        return {
            "abstract": "Brief summary of research question, methodology, findings, and implications",
            "introduction": "Background, context, research questions, and thesis statement",
            "literature_review": "Comprehensive review of existing research and theoretical frameworks",
            "methodology": "Research design, data collection, and analysis methods",
            "results": "Presentation of findings with appropriate visualizations",
            "discussion": "Interpretation of results, theoretical implications, and limitations",
            "conclusion": "Summary of findings, contributions, and future directions",
            "references": "Complete bibliography in specified citation style"
        }
    
    async def _execute(self, messages: List[BaseMessage], state: AgentState) -> Dict[str, Any]:
        """Write report sections with QA improvement guidelines"""
        # Determine which section to write
        section_name = state.get("current_section", "introduction")
        
        # Gather relevant data for the section
        section_data = self._gather_section_data(state, section_name)
        
        # Get improvement guidelines if available
        improvement_guidelines = self._get_improvement_guidelines(state, section_name)
        
        writing_prompt = f"""Write the {section_name} section of the research report.

Section guidelines: {self.section_templates.get(section_name, '')}
Relevant data: {json.dumps(section_data, indent=2)[:2000]}...

{improvement_guidelines}

Requirements:
1. Academic writing style with publication-quality prose
2. Clear structure with subsections if needed
3. Proper citations and references
4. Target length: {self._get_section_length(section_name, state)} words
5. Coherent flow and logical progression
6. Address all improvement guidelines above
7. Ensure content is polished and professional

Write a complete, publication-ready {section_name} section."""
        
        messages.append(BaseMessage(content=writing_prompt, type="human"))
        
        response = await self.model.ainvoke(messages)
        
        # Clean the generated content
        cleaned_content = self._clean_section_content(response.content)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "section_name": section_name,
            "content": cleaned_content,
            "word_count": len(cleaned_content.split()),
            "subsections": self._extract_subsections(cleaned_content),
            "citations_used": self._extract_citations(cleaned_content),
            "guidelines_applied": bool(improvement_guidelines)
        }
    
    def _gather_section_data(self, state: AgentState, section_name: str) -> Dict[str, Any]:
        """Gather relevant data for each section"""
        data = {}
        
        if section_name == "abstract":
            # Gather summary data from all analyses
            if "SynthesisAgent" in state["outputs"]:
                synthesis = state["outputs"]["SynthesisAgent"][0]
                data["key_findings"] = synthesis.get("integrated_findings", [])
                data["implications"] = synthesis.get("practical_implications", [])
        
        elif section_name == "introduction":
            # Gather research questions and domain analysis
            if "ResearchQuestionFormulationAgent" in state["outputs"]:
                questions = state["outputs"]["ResearchQuestionFormulationAgent"][0]
                data["primary_question"] = questions.get("primary_question", "")
                data["sub_questions"] = questions.get("sub_questions", [])
            if "DomainAnalysisAgent" in state["outputs"]:
                domain = state["outputs"]["DomainAnalysisAgent"][0]
                data["research_gaps"] = domain.get("research_gaps", [])
        
        elif section_name == "literature_review":
            # Gather literature survey data
            if "LiteratureSurveyAgent" in state["outputs"]:
                survey = state["outputs"]["LiteratureSurveyAgent"][0]
                data["key_papers"] = survey.get("key_papers", [])
                data["themes"] = survey.get("themes", [])
                data["authors"] = survey.get("authors", [])
        
        elif section_name == "methodology":
            # Gather methodology recommendations
            if "ResearchQuestionFormulationAgent" in state["outputs"]:
                questions = state["outputs"]["ResearchQuestionFormulationAgent"][0]
                data["methodology"] = questions.get("methodology", "")
        
        elif section_name == "results":
            # Gather analysis results
            if "QuantitativeAnalysisAgent" in state["outputs"]:
                quant = state["outputs"]["QuantitativeAnalysisAgent"][0]
                data["statistics"] = quant.get("statistics", {})
                data["trends"] = quant.get("trends", [])
            if "QualitativeAnalysisAgent" in state["outputs"]:
                qual = state["outputs"]["QualitativeAnalysisAgent"][0]
                data["themes"] = qual.get("themes", [])
                data["patterns"] = qual.get("patterns", [])
        
        elif section_name == "discussion":
            # Gather synthesis and implications
            if "SynthesisAgent" in state["outputs"]:
                synthesis = state["outputs"]["SynthesisAgent"][0]
                data["integrated_findings"] = synthesis.get("integrated_findings", [])
                data["theoretical_contributions"] = synthesis.get("theoretical_contributions", [])
        
        elif section_name == "conclusion":
            # Gather summary and future directions
            if "SynthesisAgent" in state["outputs"]:
                synthesis = state["outputs"]["SynthesisAgent"][0]
                data["future_directions"] = synthesis.get("future_directions", [])
        
        return data
    
    def _get_section_length(self, section_name: str, state: AgentState) -> int:
        """Calculate target length for each section"""
        total_length = state.get("requirements", {}).get("target_length", 50000)
        
        # Approximate distribution of content
        section_percentages = {
            "abstract": 0.01,  # 1%
            "introduction": 0.10,  # 10%
            "literature_review": 0.25,  # 25%
            "methodology": 0.15,  # 15%
            "results": 0.20,  # 20%
            "discussion": 0.20,  # 20%
            "conclusion": 0.08,  # 8%
            "references": 0.01   # 1%
        }
        
        percentage = section_percentages.get(section_name, 0.10)
        return int(total_length * percentage)
    
    def _extract_subsections(self, content: str) -> List[str]:
        """Extract subsection headings"""
        subsections = []
        lines = content.split('\n')
        
        for line in lines:
            # Look for heading patterns
            if line.strip() and (
                line.startswith('#') or 
                line.isupper() or 
                (line.endswith(':') and len(line.split()) < 8)
            ):
                subsections.append(line.strip())
        
        return subsections[:10]
    
    def _extract_citations(self, content: str) -> List[str]:
        """Extract citations used in the section"""
        import re
        citations = []
        
        # Common citation patterns
        patterns = [
            r'\([A-Za-z\s&,]+,?\s*\d{4}\)',  # (Author, Year)
            r'\[[0-9]+\]',  # [1]
            r'[A-Za-z\s&,]+\s*\(\d{4}\)'  # Author (Year)
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            citations.extend(matches)
        
        return list(set(citations))[:20]
    
    def _get_improvement_guidelines(self, state: AgentState, section_name: str) -> str:
        """Get improvement guidelines for the current section"""
        guidelines_text = ""
        
        # Check if improvement guidelines exist in state
        if "improvement_guidelines" in state.get("outputs", {}):
            guidelines = state["outputs"]["improvement_guidelines"]
            
            # Add general guidelines
            if guidelines.get("general"):
                guidelines_text += f"GENERAL IMPROVEMENT GUIDELINES:\n{guidelines['general']}\n\n"
            
            # Add section-specific guidelines
            if section_name in guidelines.get("sections", {}):
                guidelines_text += f"SECTION-SPECIFIC IMPROVEMENTS FOR {section_name.upper()}:\n{guidelines['sections'][section_name]}\n\n"
            
            # Add citation guidelines
            if guidelines.get("citation"):
                guidelines_text += f"CITATION REQUIREMENTS:\n{guidelines['citation']}\n\n"
            
            # Add compliance guidelines
            if guidelines.get("compliance"):
                guidelines_text += f"COMPLIANCE REQUIREMENTS:\n{guidelines['compliance']}\n\n"
        
        return guidelines_text if guidelines_text else ""
    
    def _clean_section_content(self, content: str) -> str:
        """Clean section content of unwanted artifacts"""
        if not content:
            return content
            
        # Remove thinking tags
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove agent artifacts
        content = re.sub(r'AGENT.*?:', '', content, flags=re.IGNORECASE)
        content = re.sub(r'PROCESSING.*?:', '', content, flags=re.IGNORECASE)
        content = re.sub(r'DEBUG.*?:', '', content, flags=re.IGNORECASE)
        
        # Clean up multiple newlines
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        # Remove leading/trailing whitespace
        content = content.strip()
        
        return content


class CoherenceIntegrationAgent(BaseAgent):
    """Agent for ensuring coherence across sections"""
    
    def __init__(self, model):
        super().__init__(
            name="CoherenceIntegrationAgent",
            model=model,
            role_description="Ensure coherence, consistency, and smooth transitions across report sections"
        )
    
    async def _execute(self, messages: List[BaseMessage], state: AgentState) -> Dict[str, Any]:
        """Ensure coherence across sections"""
        # Gather all written sections
        sections = self._gather_sections(state)
        
        integration_prompt = f"""Review and improve coherence across report sections:

Sections available: {list(sections.keys())}
Total length: {sum(len(s['content'].split()) for s in sections.values())} words

Tasks:
1. Check for consistency in terminology and concepts
2. Ensure smooth transitions between sections
3. Verify cross-references are accurate
4. Maintain consistent academic tone
5. Identify and resolve contradictions
6. Suggest improvements for flow

Provide specific recommendations for each section."""
        
        messages.append(BaseMessage(content=integration_prompt, type="human"))
        
        response = await self.model.ainvoke(messages)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "coherence_report": response.content,
            "consistency_issues": self._identify_consistency_issues(response.content),
            "transition_improvements": self._suggest_transitions(response.content),
            "terminology_standardization": self._standardize_terminology(response.content),
            "cross_reference_fixes": self._fix_cross_references(response.content),
            "overall_coherence_score": self._calculate_coherence_score(response.content)
        }
    
    def _gather_sections(self, state: AgentState) -> Dict[str, Dict[str, Any]]:
        """Gather all written sections"""
        sections = {}
        
        if "SectionWritingAgent" in state["outputs"]:
            for output in state["outputs"]["SectionWritingAgent"]:
                section_name = output.get("section_name")
                if section_name:
                    sections[section_name] = output
        
        return sections
    
    def _identify_consistency_issues(self, content: str) -> List[str]:
        """Identify consistency issues"""
        issues = []
        lines = content.split('\n')
        
        for line in lines:
            if any(word in line.lower() for word in ['inconsistent', 'contradiction', 'mismatch', 'conflict']):
                issues.append(line.strip())
        
        return issues[:8]
    
    def _suggest_transitions(self, content: str) -> Dict[str, str]:
        """Suggest transition improvements"""
        transitions = {}
        lines = content.split('\n')
        
        current_section = None
        for line in lines:
            if "transition" in line.lower() and "section" in line.lower():
                # Try to extract section names
                words = line.split()
                for i, word in enumerate(words):
                    if word.lower() in ['from', 'between']:
                        if i + 1 < len(words):
                            current_section = words[i + 1].strip(',:')
            elif current_section and line.strip():
                transitions[current_section] = line.strip()
        
        return transitions
    
    def _standardize_terminology(self, content: str) -> Dict[str, str]:
        """Suggest terminology standardization"""
        terminology = {}
        lines = content.split('\n')
        
        for line in lines:
            if "term" in line.lower() and ("use" in line.lower() or "standardize" in line.lower()):
                # Simple extraction
                if ':' in line:
                    parts = line.split(':')
                    if len(parts) == 2:
                        terminology[parts[0].strip()] = parts[1].strip()
        
        return terminology
    
    def _fix_cross_references(self, content: str) -> List[str]:
        """Identify cross-reference fixes needed"""
        fixes = []
        lines = content.split('\n')
        
        for line in lines:
            if any(word in line.lower() for word in ['reference', 'section', 'figure', 'table']):
                if any(word in line.lower() for word in ['fix', 'update', 'correct', 'missing']):
                    fixes.append(line.strip())
        
        return fixes[:6]
    
    def _calculate_coherence_score(self, content: str) -> float:
        """Calculate overall coherence score"""
        # Simple scoring based on identified issues
        issues_count = content.lower().count('issue') + content.lower().count('problem')
        improvements_count = content.lower().count('improve') + content.lower().count('suggest')
        positive_count = content.lower().count('coherent') + content.lower().count('consistent')
        
        # Base score
        score = 7.0
        
        # Adjust based on findings
        score -= (issues_count * 0.3)
        score -= (improvements_count * 0.1)
        score += (positive_count * 0.5)
        
        return max(0.0, min(10.0, score))


class FinalAssemblyAgent(BaseAgent):
    """Agent for final report assembly and formatting"""
    
    def __init__(self, model):
        super().__init__(
            name="FinalAssemblyAgent",
            model=model,
            role_description="Assemble final research report with proper formatting and structure"
        )
    
    async def _execute(self, messages: List[BaseMessage], state: AgentState) -> Dict[str, Any]:
        """Assemble final report"""
        # Gather all components
        sections = self._gather_sections(state)
        coherence_report = state["outputs"].get("CoherenceIntegrationAgent", [{}])[0]
        qa_results = self._gather_qa_results(state)
        
        assembly_prompt = f"""Assemble the final research report:

Sections completed: {list(sections.keys())}
Coherence score: {coherence_report.get('overall_coherence_score', 'N/A')}
Quality score: {qa_results.get('quality_score', 'N/A')}

Create final report with:
1. Title page
2. Table of contents
3. Executive summary
4. All sections in proper order
5. Appendices if needed
6. Proper formatting and numbering

Ensure the report meets academic standards."""
        
        messages.append(BaseMessage(content=assembly_prompt, type="human"))
        
        response = await self.model.ainvoke(messages)
        
        # Assemble the actual report
        final_report = self._assemble_report(sections, state)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "assembly_notes": response.content,
            "final_report": final_report,
            "report_metadata": self._generate_metadata(sections, state),
            "quality_metrics": self._calculate_quality_metrics(sections, qa_results),
            "output_formats": ["markdown", "pdf", "docx"]
        }
    
    def _gather_sections(self, state: AgentState) -> Dict[str, Dict[str, Any]]:
        """Gather all written sections"""
        sections = {}
        
        if "SectionWritingAgent" in state["outputs"]:
            for output in state["outputs"]["SectionWritingAgent"]:
                section_name = output.get("section_name")
                if section_name:
                    sections[section_name] = output
        
        return sections
    
    def _gather_qa_results(self, state: AgentState) -> Dict[str, Any]:
        """Gather QA team results"""
        qa_results = {}
        
        if "PeerReviewAgent" in state["outputs"]:
            peer_review = state["outputs"]["PeerReviewAgent"][0]
            qa_results["quality_score"] = peer_review.get("quality_score", 0)
            qa_results["publication_ready"] = peer_review.get("publication_ready", False)
        
        if "AcademicStandardsComplianceAgent" in state["outputs"]:
            compliance = state["outputs"]["AcademicStandardsComplianceAgent"][0]
            qa_results["compliance"] = compliance.get("overall_compliance", "Unknown")
        
        return qa_results
    
    def _assemble_report(self, sections: Dict[str, Dict[str, Any]], state: AgentState) -> str:
        """Assemble the complete report"""
        report_parts = []
        
        # Title page
        report_parts.append(self._create_title_page(state))
        
        # Table of contents
        report_parts.append(self._create_table_of_contents(sections))
        
        # Executive summary
        if "abstract" in sections:
            report_parts.append("# Executive Summary\n\n" + sections["abstract"]["content"])
        
        # Main sections in order
        section_order = ["introduction", "literature_review", "methodology", 
                        "results", "discussion", "conclusion", "references"]
        
        for section_name in section_order:
            if section_name in sections:
                section_title = section_name.replace('_', ' ').title()
                report_parts.append(f"\n# {section_title}\n\n{sections[section_name]['content']}")
        
        # Appendices
        report_parts.append(self._create_appendices(state))
        
        return "\n\n".join(report_parts)
    
    def _create_title_page(self, state: AgentState) -> str:
        """Create title page"""
        topic = state.get("research_topic", "Research Report")
        date = datetime.now().strftime("%B %Y")
        
        return f"""# {topic}

## A Comprehensive Research Report

**Generated by:** HierarchicalResearchAI  
**Date:** {date}  
**Version:** 1.0

---
"""
    
    def _create_table_of_contents(self, sections: Dict[str, Dict[str, Any]]) -> str:
        """Create table of contents"""
        toc = ["# Table of Contents\n"]
        
        section_order = ["introduction", "literature_review", "methodology", 
                        "results", "discussion", "conclusion", "references"]
        
        for i, section_name in enumerate(section_order, 1):
            if section_name in sections:
                section_title = section_name.replace('_', ' ').title()
                toc.append(f"{i}. {section_title}")
                
                # Add subsections if available
                subsections = sections[section_name].get("subsections", [])
                for j, subsection in enumerate(subsections[:5], 1):
                    toc.append(f"   {i}.{j} {subsection}")
        
        return "\n".join(toc)
    
    def _create_appendices(self, state: AgentState) -> str:
        """Create appendices section"""
        appendices = ["# Appendices\n"]
        
        # Add research metadata
        appendices.append("## Appendix A: Research Metadata")
        appendices.append(f"- Total word count: {state.get('total_word_count', 0):,}")
        appendices.append(f"- Sources analyzed: {state.get('source_count', 0)}")
        appendices.append(f"- Citations: {state.get('citation_count', 0)}")
        
        return "\n".join(appendices)
    
    def _generate_metadata(self, sections: Dict[str, Dict[str, Any]], state: AgentState) -> Dict[str, Any]:
        """Generate report metadata"""
        total_words = sum(section["word_count"] for section in sections.values())
        total_citations = sum(len(section.get("citations_used", [])) for section in sections.values())
        
        return {
            "title": state.get("research_topic", "Research Report"),
            "date_generated": datetime.now().isoformat(),
            "total_word_count": total_words,
            "section_count": len(sections),
            "citation_count": total_citations,
            "target_audience": state.get("requirements", {}).get("audience", "Academic"),
            "citation_style": state.get("requirements", {}).get("citation_style", "APA")
        }
    
    def _calculate_quality_metrics(self, sections: Dict[str, Dict[str, Any]], 
                                 qa_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate final quality metrics"""
        return {
            "overall_quality_score": qa_results.get("quality_score", 0),
            "publication_ready": qa_results.get("publication_ready", False),
            "compliance_status": qa_results.get("compliance", "Unknown"),
            "completeness": len(sections) / 8 * 100,  # Percentage of expected sections
            "average_section_length": sum(s["word_count"] for s in sections.values()) / len(sections) if sections else 0
        }


class EditorAgent(BaseAgent):
    """Agent for improving content based on QA feedback"""
    
    def __init__(self, model):
        super().__init__(
            name="EditorAgent", 
            model=model,
            role_description="Edit and improve research content based on quality assurance feedback"
        )
    
    async def _execute(self, messages: List[BaseMessage], state: AgentState) -> Dict[str, Any]:
        """Generate improvement guidelines based on QA recommendations"""
        
        # Gather QA feedback
        qa_feedback = self._gather_qa_feedback(state)
        
        if not qa_feedback:
            return {
                "timestamp": datetime.now().isoformat(),
                "edit_action": "no_action",
                "reason": "No QA feedback found"
            }
        
        # Create improvement guidelines prompt
        guidelines_prompt = self._create_improvement_guidelines_prompt(qa_feedback)
        
        messages.append(BaseMessage(content=guidelines_prompt, type="human"))
        
        response = await self.model.ainvoke(messages)
        
        # Parse improvement guidelines
        improvement_guidelines = self._parse_improvement_guidelines(response.content)
        
        # Store guidelines in state for use during report assembly
        if "improvement_guidelines" not in state["outputs"]:
            state["outputs"]["improvement_guidelines"] = {}
        
        state["outputs"]["improvement_guidelines"] = improvement_guidelines
        
        return {
            "timestamp": datetime.now().isoformat(),
            "edit_action": "guidelines_generated",
            "improvement_guidelines": improvement_guidelines,
            "original_issues": qa_feedback.get("total_issues", 0),
            "guidelines_summary": self._extract_guidelines_summary(response.content)
        }
    
    def _gather_qa_feedback(self, state: AgentState) -> Dict[str, Any]:
        """Gather comprehensive feedback from all QA agents"""
        feedback = {
            "peer_review": {},
            "citation_issues": {},
            "compliance_issues": {},
            "total_issues": 0,
            "recommendations": []
        }
        
        # Peer review feedback
        if "PeerReviewAgent" in state["outputs"]:
            peer_review = state["outputs"]["PeerReviewAgent"][0] if isinstance(state["outputs"]["PeerReviewAgent"], list) else state["outputs"]["PeerReviewAgent"]
            feedback["peer_review"] = {
                "quality_score": peer_review.get("quality_score", 0),
                "weaknesses": peer_review.get("weaknesses", []),
                "recommendations": peer_review.get("recommendations", []),
                "strengths": peer_review.get("strengths", [])
            }
            feedback["recommendations"].extend(peer_review.get("recommendations", []))
            feedback["total_issues"] += len(peer_review.get("weaknesses", []))
        
        # Citation verification feedback
        if "CitationVerificationAgent" in state["outputs"]:
            citation = state["outputs"]["CitationVerificationAgent"][0] if isinstance(state["outputs"]["CitationVerificationAgent"], list) else state["outputs"]["CitationVerificationAgent"]
            feedback["citation_issues"] = {
                "format_issues": citation.get("format_issues", []),
                "missing_elements": citation.get("missing_elements", []),
                "recommendations": citation.get("recommendations", [])
            }
            feedback["recommendations"].extend(citation.get("recommendations", []))
            feedback["total_issues"] += len(citation.get("format_issues", [])) + len(citation.get("missing_elements", []))
        
        # Compliance feedback
        if "AcademicStandardsComplianceAgent" in state["outputs"]:
            compliance = state["outputs"]["AcademicStandardsComplianceAgent"][0] if isinstance(state["outputs"]["AcademicStandardsComplianceAgent"], list) else state["outputs"]["AcademicStandardsComplianceAgent"]
            feedback["compliance_issues"] = {
                "violations": compliance.get("violations", []),
                "recommendations": compliance.get("recommendations", [])
            }
            feedback["recommendations"].extend(compliance.get("recommendations", []))
            feedback["total_issues"] += len(compliance.get("violations", []))
        
        return feedback
    
    def _gather_analysis_content(self, state: AgentState) -> Dict[str, str]:
        """Gather current analysis content that needs improvement"""
        content = {}
        
        # Get analysis outputs
        if "QuantitativeAnalysisAgent" in state["outputs"]:
            quant = state["outputs"]["QuantitativeAnalysisAgent"][0] if isinstance(state["outputs"]["QuantitativeAnalysisAgent"], list) else state["outputs"]["QuantitativeAnalysisAgent"]
            content["quantitative_analysis"] = quant.get("analysis", "")
        
        if "QualitativeAnalysisAgent" in state["outputs"]:
            qual = state["outputs"]["QualitativeAnalysisAgent"][0] if isinstance(state["outputs"]["QualitativeAnalysisAgent"], list) else state["outputs"]["QualitativeAnalysisAgent"]
            content["qualitative_analysis"] = qual.get("analysis", "")
        
        if "SynthesisAgent" in state["outputs"]:
            synth = state["outputs"]["SynthesisAgent"][0] if isinstance(state["outputs"]["SynthesisAgent"], list) else state["outputs"]["SynthesisAgent"]
            content["synthesis"] = synth.get("synthesis", "")
        
        return content
    
    def _create_improvement_guidelines_prompt(self, qa_feedback: Dict[str, Any]) -> str:
        """Create prompt for generating improvement guidelines"""
        
        prompt = f"""You are an expert academic editorial advisor. Based on the quality assurance feedback below, create specific improvement guidelines that content-generating agents can follow during report assembly.

QUALITY ASSURANCE FEEDBACK:
Quality Score: {qa_feedback['peer_review'].get('quality_score', 'N/A')}/10 (Target: 8.0+)

IDENTIFIED WEAKNESSES:
{chr(10).join(f"- {w}" for w in qa_feedback['peer_review'].get('weaknesses', []))}

SPECIFIC RECOMMENDATIONS:
{chr(10).join(f"- {r}" for r in qa_feedback.get('recommendations', []))}

CITATION ISSUES:
{chr(10).join(f"- {issue}" for issue in qa_feedback['citation_issues'].get('format_issues', []))}

COMPLIANCE ISSUES:
{chr(10).join(f"- {violation}" for violation in qa_feedback['compliance_issues'].get('violations', []))}

TASK: Create specific improvement guidelines that section-writing agents should follow during report assembly to address these issues.

FORMAT YOUR RESPONSE AS:

GENERAL_GUIDELINES:
[Overall writing quality improvements needed]

SECTION_GUIDELINES:
Abstract: [Specific improvements for abstract writing]
Introduction: [Specific improvements for introduction writing]
Literature_Review: [Specific improvements for literature review writing]
Methodology: [Specific improvements for methodology writing]
Results: [Specific improvements for results writing]
Discussion: [Specific improvements for discussion writing]
Conclusion: [Specific improvements for conclusion writing]

CITATION_GUIDELINES:
[Specific citation formatting and quality requirements]

COMPLIANCE_GUIDELINES:
[Specific academic standards compliance requirements]

Focus on actionable guidelines that will raise the quality score above 6.0."""
        
        return prompt
    
    def _parse_improvement_guidelines(self, response_content: str) -> Dict[str, Any]:
        """Parse improvement guidelines from the model response"""
        guidelines = {
            "general": "",
            "sections": {},
            "citation": "",
            "compliance": ""
        }
        
        # Extract general guidelines
        general_match = re.search(r"GENERAL_GUIDELINES:(.*?)(?=SECTION_GUIDELINES:|$)", response_content, re.DOTALL | re.IGNORECASE)
        if general_match:
            guidelines["general"] = general_match.group(1).strip()
        
        # Extract section-specific guidelines
        section_match = re.search(r"SECTION_GUIDELINES:(.*?)(?=CITATION_GUIDELINES:|$)", response_content, re.DOTALL | re.IGNORECASE)
        if section_match:
            section_content = section_match.group(1)
            # Parse individual section guidelines
            section_patterns = {
                "abstract": r"Abstract:\s*(.*?)(?=Introduction:|Literature_Review:|$)",
                "introduction": r"Introduction:\s*(.*?)(?=Literature_Review:|Methodology:|$)",
                "literature_review": r"Literature_Review:\s*(.*?)(?=Methodology:|Results:|$)",
                "methodology": r"Methodology:\s*(.*?)(?=Results:|Discussion:|$)",
                "results": r"Results:\s*(.*?)(?=Discussion:|Conclusion:|$)",
                "discussion": r"Discussion:\s*(.*?)(?=Conclusion:|$)",
                "conclusion": r"Conclusion:\s*(.*?)$"
            }
            
            for section_name, pattern in section_patterns.items():
                match = re.search(pattern, section_content, re.DOTALL | re.IGNORECASE)
                if match:
                    guidelines["sections"][section_name] = match.group(1).strip()
        
        # Extract citation guidelines
        citation_match = re.search(r"CITATION_GUIDELINES:(.*?)(?=COMPLIANCE_GUIDELINES:|$)", response_content, re.DOTALL | re.IGNORECASE)
        if citation_match:
            guidelines["citation"] = citation_match.group(1).strip()
        
        # Extract compliance guidelines
        compliance_match = re.search(r"COMPLIANCE_GUIDELINES:(.*?)$", response_content, re.DOTALL | re.IGNORECASE)
        if compliance_match:
            guidelines["compliance"] = compliance_match.group(1).strip()
        
        return guidelines
    
    def _extract_guidelines_summary(self, response_content: str) -> str:
        """Extract summary of guidelines from the response"""
        if "GENERAL_GUIDELINES:" in response_content:
            return "Improvement guidelines generated for all report sections based on QA feedback"
        return "Basic improvement guidelines created"