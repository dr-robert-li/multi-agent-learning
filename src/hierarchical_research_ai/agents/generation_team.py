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
        """Write report sections"""
        # Determine which section to write
        section_name = state.get("current_section", "introduction")
        
        # Gather relevant data for the section
        section_data = self._gather_section_data(state, section_name)
        
        writing_prompt = f"""Write the {section_name} section of the research report.

Section guidelines: {self.section_templates.get(section_name, '')}
Relevant data: {json.dumps(section_data, indent=2)[:2000]}...

Requirements:
1. Academic writing style
2. Clear structure with subsections if needed
3. Proper citations and references
4. Target length: {self._get_section_length(section_name, state)} words
5. Coherent flow and logical progression

Write a complete {section_name} section."""
        
        messages.append(BaseMessage(content=writing_prompt, type="human"))
        
        response = await self.model.ainvoke(messages)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "section_name": section_name,
            "content": response.content,
            "word_count": len(response.content.split()),
            "subsections": self._extract_subsections(response.content),
            "citations_used": self._extract_citations(response.content)
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
        """Edit content based on QA recommendations"""
        
        # Gather QA feedback
        qa_feedback = self._gather_qa_feedback(state)
        
        # Get current analysis content that needs improvement
        analysis_content = self._gather_analysis_content(state)
        
        if not qa_feedback or not analysis_content:
            return {
                "timestamp": datetime.now().isoformat(),
                "edit_action": "no_action",
                "reason": "No QA feedback or analysis content found"
            }
        
        # Create editing prompt
        edit_prompt = self._create_edit_prompt(analysis_content, qa_feedback)
        
        messages.append(BaseMessage(content=edit_prompt, type="human"))
        
        response = await self.model.ainvoke(messages)
        
        # Parse the edited content
        edited_content = self._parse_edited_content(response.content)
        
        # Apply improvements to state
        improvements_applied = self._apply_improvements(state, edited_content)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "edit_action": "content_improved",
            "improvements_applied": improvements_applied,
            "original_issues": qa_feedback.get("total_issues", 0),
            "editing_summary": self._extract_editing_summary(response.content),
            "revised_sections": list(edited_content.keys())
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
    
    def _create_edit_prompt(self, analysis_content: Dict[str, str], qa_feedback: Dict[str, Any]) -> str:
        """Create comprehensive editing prompt for substantial content rewriting"""
        
        prompt = f"""You are an expert academic editor tasked with completely rewriting research content to professional publication standards.

QUALITY ASSURANCE FEEDBACK:
Quality Score: {qa_feedback['peer_review'].get('quality_score', 'N/A')}/10 (Target: 8.0+)

CRITICAL WEAKNESSES TO FIX:
{chr(10).join(f"- {w}" for w in qa_feedback['peer_review'].get('weaknesses', []))}

MANDATORY IMPROVEMENTS:
{chr(10).join(f"- {r}" for r in qa_feedback.get('recommendations', []))}

CITATION REQUIREMENTS:
{chr(10).join(f"- {issue}" for issue in qa_feedback['citation_issues'].get('format_issues', []))}

COMPLIANCE REQUIREMENTS:
{chr(10).join(f"- {violation}" for violation in qa_feedback['compliance_issues'].get('violations', []))}

CONTENT TO COMPLETELY REWRITE:

"""
        
        for section_name, content in analysis_content.items():
            if content.strip():
                prompt += f"\n--- {section_name.upper().replace('_', ' ')} ---\n{content[:1500]}{'...' if len(content) > 1500 else ''}\n"
        
        prompt += """

REWRITING REQUIREMENTS:
1. COMPLETELY REWRITE each section - do not just edit, create entirely new professional content
2. Remove all thinking tags, agent artifacts, and test content
3. Write in polished academic prose with clear argumentation
4. Add proper citations and evidence-based claims
5. Ensure logical flow and coherent structure
6. Address every weakness identified in QA feedback
7. Meet publication-quality standards

OUTPUT FORMAT:
Provide completely rewritten sections that are ready for publication. No editing notes or suggestions - only the final polished content.

EDITING_SUMMARY:
[Brief summary of major rewrites completed]

QUANTITATIVE_ANALYSIS:
[Completely rewritten quantitative analysis section in polished academic prose]

QUALITATIVE_ANALYSIS:
[Completely rewritten qualitative analysis section in polished academic prose]

SYNTHESIS:
[Completely rewritten synthesis section in polished academic prose]

Requirements: Each rewritten section must be publication-ready, coherent, and address all QA feedback."""
        
        return prompt
    
    def _parse_edited_content(self, response_content: str) -> Dict[str, str]:
        """Parse the edited content from the model response"""
        edited_content = {}
        
        # Extract sections using markers
        sections = {
            "quantitative_analysis": r"QUANTITATIVE_ANALYSIS:(.*?)(?=QUALITATIVE_ANALYSIS:|SYNTHESIS:|$)",
            "qualitative_analysis": r"QUALITATIVE_ANALYSIS:(.*?)(?=SYNTHESIS:|$)", 
            "synthesis": r"SYNTHESIS:(.*?)$"
        }
        
        for section_name, pattern in sections.items():
            match = re.search(pattern, response_content, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                if content:
                    edited_content[section_name] = content
        
        return edited_content
    
    def _apply_improvements(self, state: AgentState, edited_content: Dict[str, str]) -> List[str]:
        """Apply improvements to the state"""
        improvements_applied = []
        
        # Update analysis outputs with improved content
        for section_name, improved_content in edited_content.items():
            if section_name == "quantitative_analysis" and "QuantitativeAnalysisAgent" in state["outputs"]:
                if isinstance(state["outputs"]["QuantitativeAnalysisAgent"], list):
                    state["outputs"]["QuantitativeAnalysisAgent"][0]["analysis"] = improved_content
                else:
                    state["outputs"]["QuantitativeAnalysisAgent"]["analysis"] = improved_content
                improvements_applied.append("quantitative_analysis")
                
            elif section_name == "qualitative_analysis" and "QualitativeAnalysisAgent" in state["outputs"]:
                if isinstance(state["outputs"]["QualitativeAnalysisAgent"], list):
                    state["outputs"]["QualitativeAnalysisAgent"][0]["analysis"] = improved_content
                else:
                    state["outputs"]["QualitativeAnalysisAgent"]["analysis"] = improved_content
                improvements_applied.append("qualitative_analysis")
                
            elif section_name == "synthesis" and "SynthesisAgent" in state["outputs"]:
                if isinstance(state["outputs"]["SynthesisAgent"], list):
                    state["outputs"]["SynthesisAgent"][0]["synthesis"] = improved_content
                else:
                    state["outputs"]["SynthesisAgent"]["synthesis"] = improved_content
                improvements_applied.append("synthesis")
        
        return improvements_applied
    
    def _extract_editing_summary(self, response_content: str) -> str:
        """Extract the editing summary from the response"""
        summary_match = re.search(r"EDITING_SUMMARY:(.*?)(?=QUANTITATIVE_ANALYSIS:|$)", response_content, re.DOTALL | re.IGNORECASE)
        if summary_match:
            return summary_match.group(1).strip()
        return "Content improvements applied based on QA feedback"