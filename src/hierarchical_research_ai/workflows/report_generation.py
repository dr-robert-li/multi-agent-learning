"""
Report Generation System

Handles the final assembly and formatting of research reports.
"""

import os
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import structlog

from ..config.models import ModelConfig
from ..tools.research_tools import ResearchToolkit

logger = structlog.get_logger()


class ReportGenerator:
    """Generates final research reports from agent outputs"""
    
    def __init__(self, model_config: ModelConfig, research_toolkit: ResearchToolkit):
        self.model_config = model_config
        self.research_toolkit = research_toolkit
        
        # Create logs directory for structured agent output
        self.agent_logs_dir = Path("./logs/agent_outputs")
        self.agent_logs_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_final_report(self, 
                                  agent_outputs: Dict[str, Any],
                                  requirements: Dict[str, Any],
                                  research_topic: str) -> Dict[str, Any]:
        """
        Generate the final research report
        
        Args:
            agent_outputs: Outputs from all research agents
            requirements: Research requirements
            research_topic: Research topic
            
        Returns:
            Dictionary containing report metadata and paths
        """
        logger.info("Starting final report generation")
        
        try:
            # Save structured agent logs
            await self._save_agent_logs(agent_outputs, research_topic)
            
            # Assemble report content with cleaning
            report_content = await self._assemble_report_content(
                agent_outputs, requirements, research_topic
            )
            
            # Format report
            formatted_report = self._format_report(report_content, requirements)
            
            # Save report
            output_paths = await self._save_report(
                formatted_report, research_topic, requirements
            )
            
            # Generate metadata
            metadata = self._generate_report_metadata(
                report_content, formatted_report, agent_outputs, requirements
            )
            
            result = {
                "status": "completed",
                "output_path": output_paths["markdown"],
                "output_paths": output_paths,
                "metadata": metadata,
                "word_count": metadata["word_count"],
                "section_count": metadata["section_count"],
                "citation_count": metadata["citation_count"]
            }
            
            logger.info("Final report generation completed", 
                       word_count=result["word_count"],
                       output_path=result["output_path"])
            
            return result
            
        except Exception as e:
            logger.error("Final report generation failed", error=str(e))
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _assemble_report_content(self, 
                                     agent_outputs: Dict[str, Any],
                                     requirements: Dict[str, Any],
                                     research_topic: str) -> Dict[str, Any]:
        """Assemble content from agent outputs"""
        
        # Debug: Log agent outputs structure
        logger.info("Assembling report content", 
                   agent_output_keys=list(agent_outputs.keys()),
                   total_agents=len(agent_outputs))
        
        for agent_name, outputs in agent_outputs.items():
            if outputs:
                logger.info(f"Agent {agent_name} outputs", 
                           count=len(outputs) if isinstance(outputs, list) else 1,
                           type=type(outputs).__name__)
        
        # Get user content
        user_content = self.research_toolkit.get_all_user_content()
        
        # Extract content from agent outputs
        content = {
            "title": research_topic,
            "abstract": self._extract_abstract(agent_outputs),
            "introduction": self._extract_introduction(agent_outputs, user_content),
            "literature_review": self._extract_literature_review(agent_outputs, user_content),
            "methodology": self._extract_methodology(agent_outputs, requirements),
            "results": self._extract_results(agent_outputs, user_content),
            "discussion": self._extract_discussion(agent_outputs),
            "conclusion": self._extract_conclusion(agent_outputs),
            "references": self._extract_references(agent_outputs, user_content),
            "appendices": self._extract_appendices(agent_outputs, user_content)
        }
        
        return content
    
    def _extract_abstract(self, agent_outputs: Dict[str, Any]) -> str:
        """Extract abstract from agent outputs"""
        return self._create_polished_abstract(agent_outputs)
    
    def _extract_introduction(self, agent_outputs: Dict[str, Any], user_content: Dict[str, Any]) -> str:
        """Extract introduction section"""
        content_parts = []
        
        # Research questions
        if "ResearchQuestionFormulationAgent" in agent_outputs:
            questions = agent_outputs["ResearchQuestionFormulationAgent"][0]
            primary_question = questions.get("primary_question", "")
            if primary_question:
                content_parts.append(f"## Research Question\n\n{primary_question}")
            
            sub_questions = questions.get("sub_questions", [])
            if sub_questions:
                content_parts.append("### Sub-questions\n\n" + "\n".join([f"- {q}" for q in sub_questions]))
        
        # Domain analysis context with safe access
        if "DomainAnalysisAgent" in agent_outputs and agent_outputs["DomainAnalysisAgent"]:
            domain_outputs = agent_outputs["DomainAnalysisAgent"]
            if isinstance(domain_outputs, list) and domain_outputs:
                domain = domain_outputs[0]
                analysis = domain.get("analysis", "")
                if analysis:
                    content_parts.append(f"## Background\n\n{analysis[:1000]}...")
        
        # User context
        if user_content.get("documents"):
            content_parts.append(f"## Research Context\n\nThis research incorporates {len(user_content['documents'])} user-provided documents and {len(user_content.get('datasets', []))} datasets to provide comprehensive analysis.")
        
        return "\n\n".join(content_parts) if content_parts else "Introduction section to be completed."
    
    def _extract_literature_review(self, agent_outputs: Dict[str, Any], user_content: Dict[str, Any]) -> str:
        """Extract literature review section"""
        content_parts = []
        
        if "LiteratureSurveyAgent" in agent_outputs and agent_outputs["LiteratureSurveyAgent"]:
            survey_outputs = agent_outputs["LiteratureSurveyAgent"]
            if isinstance(survey_outputs, list) and survey_outputs:
                survey = survey_outputs[0]
                
                # Main survey content - clean it first
                survey_content = survey.get("survey", "")
                if survey_content:
                    cleaned_content = self._clean_content(survey_content)
                    if cleaned_content:
                        content_parts.append(f"## Literature Overview\n\n{cleaned_content}")
                
                # Key papers
                key_papers = survey.get("key_papers", [])
                if key_papers:
                    content_parts.append("## Key Publications\n\n" + 
                                       "\n".join([f"- {paper.get('citation', 'Unknown citation')}" 
                                                 for paper in key_papers[:10]]))
                
                # Themes
                themes = survey.get("themes", [])
                if themes:
                    content_parts.append("## Research Themes\n\n" + 
                                       "\n".join([f"- {theme}" for theme in themes[:8]]))
        
        # User documents analysis
        if user_content.get("documents"):
            content_parts.append("## User-Provided Sources\n\nThis review incorporates analysis of user-provided documents:")
            for doc in user_content["documents"][:5]:
                content_parts.append(f"- {doc.get('metadata', {}).get('description', 'User document')}")
        
        final_content = "\n\n".join(content_parts) if content_parts else "Literature review section to be completed."
        return self._clean_content(final_content)
    
    def _extract_methodology(self, agent_outputs: Dict[str, Any], requirements: Dict[str, Any]) -> str:
        """Extract methodology section"""
        content_parts = []
        
        if "ResearchQuestionFormulationAgent" in agent_outputs:
            questions = agent_outputs["ResearchQuestionFormulationAgent"][0]
            methodology = questions.get("methodology", "")
            if methodology:
                content_parts.append(f"## Research Approach\n\n{methodology}")
        
        # Analysis methodology
        if "QuantitativeAnalysisAgent" in agent_outputs or "QualitativeAnalysisAgent" in agent_outputs:
            content_parts.append("## Analysis Methods\n\n")
            
            if "QuantitativeAnalysisAgent" in agent_outputs:
                content_parts.append("### Quantitative Analysis\nStatistical analysis and data-driven evaluation methods were employed.")
            
            if "QualitativeAnalysisAgent" in agent_outputs:
                content_parts.append("### Qualitative Analysis\nThematic analysis and interpretive methods were used for qualitative data.")
        
        # Research parameters
        content_parts.append(f"## Research Parameters\n\n")
        content_parts.append(f"- Target scope: {requirements.get('target_length', 50000):,} words")
        content_parts.append(f"- Citation style: {requirements.get('citation_style', 'APA')}")
        content_parts.append(f"- Quality level: {requirements.get('quality_level', 'Academic')}")
        
        return "\n\n".join(content_parts) if content_parts else "Methodology section to be completed."
    
    def _extract_results(self, agent_outputs: Dict[str, Any], user_content: Dict[str, Any]) -> str:
        """Extract results section"""
        content_parts = []
        
        # Quantitative results
        if "QuantitativeAnalysisAgent" in agent_outputs:
            quant = agent_outputs["QuantitativeAnalysisAgent"][0]
            
            analysis = quant.get("analysis", "")
            if analysis:
                cleaned_analysis = self._clean_content(analysis)
                if cleaned_analysis:
                    content_parts.append(f"## Quantitative Findings\n\n{cleaned_analysis}")
            
            key_findings = quant.get("key_findings", [])
            if key_findings:
                content_parts.append("### Key Statistical Results\n\n" + 
                                   "\n".join([f"- {finding}" for finding in key_findings]))
        
        # Qualitative results
        if "QualitativeAnalysisAgent" in agent_outputs:
            qual = agent_outputs["QualitativeAnalysisAgent"][0]
            
            analysis = qual.get("analysis", "")
            if analysis:
                cleaned_analysis = self._clean_content(analysis)
                if cleaned_analysis:
                    content_parts.append(f"## Qualitative Findings\n\n{cleaned_analysis}")
            
            themes = qual.get("themes", [])
            if themes:
                content_parts.append("### Identified Themes\n\n")
                for theme in themes:
                    if isinstance(theme, dict):
                        content_parts.append(f"**{theme.get('name', 'Theme')}**: {theme.get('description', '')}")
                    else:
                        content_parts.append(f"- {theme}")
        
        # User data results
        if user_content.get("datasets"):
            content_parts.append("## User Data Analysis\n\nAnalysis of user-provided datasets revealed:")
            for dataset in user_content["datasets"][:3]:
                summary = dataset.get("summary", "")
                if summary:
                    content_parts.append(f"- {summary[:200]}...")
        
        final_content = "\n\n".join(content_parts) if content_parts else "Results section to be completed."
        return self._clean_content(final_content)
    
    def _extract_discussion(self, agent_outputs: Dict[str, Any]) -> str:
        """Extract discussion section"""
        content_parts = []
        
        if "SynthesisAgent" in agent_outputs:
            synthesis = agent_outputs["SynthesisAgent"][0]
            
            # Check for synthesis content and clean it
            synthesis_content = synthesis.get("synthesis", "")
            if synthesis_content:
                cleaned_synthesis = self._clean_content(synthesis_content)
                if cleaned_synthesis:
                    content_parts.append(f"## Synthesis Overview\n\n{cleaned_synthesis}")
            
            # Integrated findings
            integrated_findings = synthesis.get("integrated_findings", [])
            if integrated_findings:
                content_parts.append("## Integrated Analysis\n\n" + 
                                   "\n".join([f"- {finding}" for finding in integrated_findings]))
            
            # Theoretical contributions
            theoretical = synthesis.get("theoretical_contributions", [])
            if theoretical:
                content_parts.append("## Theoretical Implications\n\n" + 
                                   "\n".join([f"- {contrib}" for contrib in theoretical]))
            
            # Practical implications
            practical = synthesis.get("practical_implications", [])
            if practical:
                content_parts.append("## Practical Implications\n\n" + 
                                   "\n".join([f"- {impl}" for impl in practical]))
        
        # Quality assessment
        if "PeerReviewAgent" in agent_outputs:
            review = agent_outputs["PeerReviewAgent"][0]
            strengths = review.get("strengths", [])
            if strengths:
                content_parts.append("## Research Strengths\n\n" + 
                                   "\n".join([f"- {strength}" for strength in strengths]))
        
        final_content = "\n\n".join(content_parts) if content_parts else "Discussion section to be completed."
        return self._clean_content(final_content)
    
    def _extract_conclusion(self, agent_outputs: Dict[str, Any]) -> str:
        """Extract conclusion section"""
        content_parts = []
        
        if "SynthesisAgent" in agent_outputs:
            synthesis = agent_outputs["SynthesisAgent"][0]
            
            # Future directions
            future_directions = synthesis.get("future_directions", [])
            if future_directions:
                content_parts.append("## Future Research Directions\n\n" + 
                                   "\n".join([f"- {direction}" for direction in future_directions]))
        
        # Quality assessment summary
        if "PeerReviewAgent" in agent_outputs:
            review = agent_outputs["PeerReviewAgent"][0]
            quality_score = review.get("quality_score", 0)
            content_parts.append(f"## Research Quality Assessment\n\nThis research achieved a quality score of {quality_score}/10.")
        
        # Compliance summary
        if "AcademicStandardsComplianceAgent" in agent_outputs:
            compliance = agent_outputs["AcademicStandardsComplianceAgent"][0]
            overall_compliance = compliance.get("overall_compliance", "Unknown")
            content_parts.append(f"## Academic Standards Compliance\n\nCompliance status: {overall_compliance}")
        
        return "\n\n".join(content_parts) if content_parts else "Conclusion section to be completed."
    
    def _extract_references(self, agent_outputs: Dict[str, Any], user_content: Dict[str, Any]) -> str:
        """Extract references section"""
        references = []
        
        # Extract citations from various agents
        for agent_name, outputs in agent_outputs.items():
            for output in outputs:
                if "citations_used" in output:
                    references.extend(output["citations_used"])
                elif "key_papers" in output:
                    for paper in output["key_papers"]:
                        if "citation" in paper:
                            references.append(paper["citation"])
        
        # Add user document references
        if user_content.get("documents"):
            references.append("\n## User-Provided Sources\n")
            for doc in user_content["documents"]:
                source = doc.get("original_source", "Unknown source")
                description = doc.get("metadata", {}).get("description", "")
                references.append(f"- {source}: {description}")
        
        # Deduplicate
        unique_references = list(set(ref for ref in references if ref and len(ref) > 10))
        
        if unique_references:
            return "# References\n\n" + "\n".join(unique_references)
        else:
            return "# References\n\nReferences to be compiled from research sources."
    
    def _extract_appendices(self, agent_outputs: Dict[str, Any], user_content: Dict[str, Any]) -> str:
        """Extract appendices section"""
        appendices = []
        
        # Research metadata
        appendices.append("## Appendix A: Research Metadata")
        appendices.append(f"- Research conducted: {datetime.now().strftime('%B %Y')}")
        appendices.append(f"- Agents involved: {len(agent_outputs)}")
        appendices.append(f"- User sources: {len(user_content.get('documents', [])) + len(user_content.get('datasets', []))}")
        
        # Agent summaries
        appendices.append("\n## Appendix B: Agent Contributions")
        for agent_name in agent_outputs.keys():
            appendices.append(f"- {agent_name}: Research analysis completed")
        
        return "\n\n".join(appendices)
    
    def _format_report(self, content: Dict[str, Any], requirements: Dict[str, Any]) -> str:
        """Format the complete report"""
        formatted_parts = []
        
        # Title page
        formatted_parts.append(f"# {content['title']}")
        formatted_parts.append(f"## A Comprehensive Research Report")
        formatted_parts.append(f"**Generated:** {datetime.now().strftime('%B %d, %Y')}")
        formatted_parts.append(f"**Style:** {requirements.get('citation_style', 'APA')}")
        formatted_parts.append("---")
        
        # Table of contents
        formatted_parts.append("# Table of Contents")
        formatted_parts.append("1. Abstract")
        formatted_parts.append("2. Introduction")
        formatted_parts.append("3. Literature Review")
        formatted_parts.append("4. Methodology")
        formatted_parts.append("5. Results")
        formatted_parts.append("6. Discussion")
        formatted_parts.append("7. Conclusion")
        formatted_parts.append("8. References")
        formatted_parts.append("9. Appendices")
        formatted_parts.append("---")
        
        # Main sections
        sections = [
            ("Abstract", content["abstract"]),
            ("Introduction", content["introduction"]),
            ("Literature Review", content["literature_review"]),
            ("Methodology", content["methodology"]),
            ("Results", content["results"]),
            ("Discussion", content["discussion"]),
            ("Conclusion", content["conclusion"]),
            ("References", content["references"]),
            ("Appendices", content["appendices"])
        ]
        
        for section_title, section_content in sections:
            formatted_parts.append(f"# {section_title}")
            formatted_parts.append(section_content)
            formatted_parts.append("---")
        
        return "\n\n".join(formatted_parts)
    
    async def _save_report(self, 
                         formatted_report: str, 
                         research_topic: str, 
                         requirements: Dict[str, Any]) -> Dict[str, str]:
        """Save the report in multiple formats"""
        
        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = "".join(c for c in research_topic if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
        
        output_dir = Path("./output/reports")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        base_filename = f"{safe_topic}_{timestamp}"
        
        # Save markdown
        markdown_path = output_dir / f"{base_filename}.md"
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(formatted_report)
        
        # Save JSON metadata
        json_path = output_dir / f"{base_filename}_metadata.json"
        metadata = {
            "topic": research_topic,
            "generated_at": datetime.now().isoformat(),
            "requirements": requirements,
            "word_count": len(formatted_report.split()),
            "char_count": len(formatted_report)
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info("Report saved", markdown_path=str(markdown_path))
        
        return {
            "markdown": str(markdown_path),
            "metadata": str(json_path),
            "directory": str(output_dir)
        }
    
    def _generate_report_metadata(self, 
                                report_content: Dict[str, Any],
                                formatted_report: str,
                                agent_outputs: Dict[str, Any],
                                requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive report metadata"""
        
        word_count = len(formatted_report.split())
        char_count = len(formatted_report)
        
        # Count sections
        section_count = formatted_report.count("# ") - 1  # Subtract title
        
        # Count citations (rough estimate)
        citation_count = formatted_report.count("(") + formatted_report.count("[")
        
        # Agent statistics
        agent_stats = {}
        for agent_name, outputs in agent_outputs.items():
            agent_stats[agent_name] = {
                "outputs_count": len(outputs),
                "last_execution": outputs[-1].get("timestamp") if outputs else None
            }
        
        return {
            "word_count": word_count,
            "char_count": char_count,
            "section_count": section_count,
            "citation_count": citation_count,
            "agent_stats": agent_stats,
            "generation_timestamp": datetime.now().isoformat(),
            "target_length": requirements.get("target_length", 50000),
            "completion_ratio": word_count / requirements.get("target_length", 50000),
            "quality_metrics": {
                "sections_completed": section_count,
                "agents_executed": len(agent_outputs),
                "user_sources_integrated": bool(report_content.get("user_sources"))
            }
        }
    
    async def _save_agent_logs(self, agent_outputs: Dict[str, Any], research_topic: str):
        """Save structured agent outputs to separate log files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = "".join(c for c in research_topic if c.isalnum() or c in (' ', '-', '_')).rstrip()[:30]
        
        try:
            # Save detailed agent outputs
            agent_log_file = self.agent_logs_dir / f"{safe_topic}_{timestamp}_agent_outputs.json"
            with open(agent_log_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "research_topic": research_topic,
                    "agent_outputs": agent_outputs
                }, f, indent=2, default=str)
            
            # Save activity summary
            activity_log_file = self.agent_logs_dir / f"{safe_topic}_{timestamp}_activity_summary.json"
            activity_summary = {
                "timestamp": datetime.now().isoformat(),
                "research_topic": research_topic,
                "agents_executed": list(agent_outputs.keys()),
                "total_agents": len(agent_outputs),
                "agent_summary": {}
            }
            
            for agent_name, outputs in agent_outputs.items():
                if outputs:
                    output_list = outputs if isinstance(outputs, list) else [outputs]
                    activity_summary["agent_summary"][agent_name] = {
                        "output_count": len(output_list),
                        "last_timestamp": output_list[-1].get("timestamp") if output_list else None,
                        "status": "completed"
                    }
            
            with open(activity_log_file, 'w', encoding='utf-8') as f:
                json.dump(activity_summary, f, indent=2)
            
            logger.info("Agent logs saved", 
                       agent_log_file=str(agent_log_file),
                       activity_log_file=str(activity_log_file))
                       
        except Exception as e:
            logger.error("Failed to save agent logs", error=str(e))
    
    def _clean_content(self, content: str) -> str:
        """Clean content of agent artifacts, thinking tags, and test sections"""
        if not content:
            return content
            
        # Remove thinking tags and their content
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove agent artifact headers
        artifact_patterns = [
            r'RESEARCH SYNTHESIS REPORT:.*?(?=\n\n|\n[A-Z])',
            r'DOMAIN ANALYSIS REPORT:.*?(?=\n\n|\n[A-Z])',
            r'LITERATURE SURVEY REPORT:.*?(?=\n\n|\n[A-Z])',
            r'QUALITY ASSURANCE REPORT:.*?(?=\n\n|\n[A-Z])',
            r'AGENT PROCESSING:.*?(?=\n\n|\n[A-Z])',
            r'WORKFLOW STATUS:.*?(?=\n\n|\n[A-Z])',
        ]
        
        for pattern in artifact_patterns:
            content = re.sub(pattern, '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove test sections and debugging content
        test_patterns = [
            r'TEST(ING)?.*?(?=\n\n|\n[A-Z])',
            r'DEBUG.*?(?=\n\n|\n[A-Z])',
            r'LOG.*?(?=\n\n|\n[A-Z])',
            r'INTERNAL.*?(?=\n\n|\n[A-Z])',
        ]
        
        for pattern in test_patterns:
            content = re.sub(pattern, '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Clean up multiple newlines and whitespace
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        content = re.sub(r'^\s+|\s+$', '', content, flags=re.MULTILINE)
        
        # Remove empty sections
        content = re.sub(r'##\s*\n\n', '', content)
        content = re.sub(r'###\s*\n\n', '', content)
        
        return content.strip()
    
    def _create_polished_abstract(self, agent_outputs: Dict[str, Any]) -> str:
        """Create a polished abstract from synthesis output"""
        if "SynthesisAgent" not in agent_outputs:
            return "This research provides a comprehensive analysis of the specified topic, integrating multiple perspectives and methodologies to deliver actionable insights."
        
        synthesis_outputs = agent_outputs["SynthesisAgent"]
        if not synthesis_outputs:
            return "This research provides a comprehensive analysis of the specified topic, integrating multiple perspectives and methodologies to deliver actionable insights."
        
        synthesis = synthesis_outputs[0] if isinstance(synthesis_outputs, list) else synthesis_outputs
        raw_synthesis = synthesis.get("synthesis", "")
        
        # Clean the synthesis content
        cleaned_synthesis = self._clean_content(raw_synthesis)
        
        # Extract key findings for abstract
        key_findings = synthesis.get("integrated_findings", [])
        practical_implications = synthesis.get("practical_implications", [])
        
        # Construct polished abstract
        abstract_parts = []
        
        if cleaned_synthesis:
            # Take first meaningful paragraph
            paragraphs = [p.strip() for p in cleaned_synthesis.split('\n\n') if p.strip() and len(p.strip()) > 50]
            if paragraphs:
                abstract_parts.append(paragraphs[0])
        
        if key_findings:
            findings_text = "Key findings include: " + "; ".join(key_findings[:3]) + "."
            abstract_parts.append(findings_text)
        
        if practical_implications:
            implications_text = "The research demonstrates " + "; ".join(practical_implications[:2]) + "."
            abstract_parts.append(implications_text)
        
        if not abstract_parts:
            return "This research provides a comprehensive analysis of the specified topic, integrating multiple perspectives and methodologies to deliver actionable insights."
        
        return " ".join(abstract_parts)