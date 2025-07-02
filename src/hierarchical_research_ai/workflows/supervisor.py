"""
Hierarchical Supervisor System

Implements LangGraph-based supervisors for coordinating multi-agent research workflows.
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable, TypedDict
from datetime import datetime
import structlog

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ..agents.base_agent import BaseAgent, AgentState
from ..agents.research_team import DomainAnalysisAgent, LiteratureSurveyAgent, ResearchQuestionFormulationAgent
from ..agents.analysis_team import QuantitativeAnalysisAgent, QualitativeAnalysisAgent, SynthesisAgent
from ..agents.qa_team import PeerReviewAgent, CitationVerificationAgent, AcademicStandardsComplianceAgent
from ..agents.generation_team import SectionWritingAgent, CoherenceIntegrationAgent, FinalAssemblyAgent, EditorAgent
from ..config.models import ModelConfig
from ..tools.research_tools import ResearchToolkit

logger = structlog.get_logger()


class SupervisorState(TypedDict):
    """State for supervisor workflows"""
    messages: List[Dict[str, Any]]
    research_topic: str
    current_phase: str
    agent_outputs: Dict[str, Any]
    next_agent: str
    completed_agents: List[str]
    requirements: Dict[str, Any]
    user_sources: Dict[str, Any]
    progress: Dict[str, Any]
    errors: List[str]
    qa_retry_count: int


class HierarchicalSupervisor:
    """Base supervisor for coordinating agent workflows"""
    
    def __init__(self, model_config: ModelConfig, research_toolkit: ResearchToolkit):
        self.model_config = model_config
        self.research_toolkit = research_toolkit
        self.checkpointer = MemorySaver()
        
        # Initialize agents
        self._initialize_agents()
        
        # Create workflow graph
        self.workflow = self._create_workflow()
    
    def _initialize_agents(self):
        """Initialize all agents with appropriate models"""
        # Research team agents
        self.domain_analysis_agent = DomainAnalysisAgent(self.model_config.get_analysis_model())
        self.literature_survey_agent = LiteratureSurveyAgent(self.model_config.get_research_model())
        self.research_question_agent = ResearchQuestionFormulationAgent(self.model_config.get_analysis_model())
        
        # Analysis team agents
        self.quantitative_analysis_agent = QuantitativeAnalysisAgent(self.model_config.get_analysis_model())
        self.qualitative_analysis_agent = QualitativeAnalysisAgent(self.model_config.get_analysis_model())
        self.synthesis_agent = SynthesisAgent(self.model_config.get_analysis_model())
        
        # Quality assurance agents
        self.peer_review_agent = PeerReviewAgent(self.model_config.get_analysis_model())
        self.citation_verification_agent = CitationVerificationAgent(self.model_config.get_routine_model())
        self.compliance_agent = AcademicStandardsComplianceAgent(self.model_config.get_analysis_model())
        
        # Report generation agents
        self.section_writing_agent = SectionWritingAgent(self.model_config.get_analysis_model())
        self.coherence_agent = CoherenceIntegrationAgent(self.model_config.get_analysis_model())
        self.final_assembly_agent = FinalAssemblyAgent(self.model_config.get_analysis_model())
        
        # Editor agent for improving content based on QA feedback
        self.editor_agent = EditorAgent(self.model_config.get_analysis_model())
    
    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow"""
        workflow = StateGraph(SupervisorState)
        
        # Add nodes for each phase
        workflow.add_node("research_planning", self._research_planning_supervisor)
        workflow.add_node("data_collection", self._data_collection_supervisor)
        workflow.add_node("analysis", self._analysis_supervisor)
        workflow.add_node("quality_assurance", self._quality_assurance_supervisor)
        workflow.add_node("editing", self._editing_supervisor)
        workflow.add_node("report_generation", self._report_generation_supervisor)
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "research_planning",
            self._should_continue_to_data_collection,
            {
                "continue": "data_collection",
                "retry": "research_planning",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "data_collection",
            self._should_continue_to_analysis,
            {
                "continue": "analysis",
                "retry": "data_collection",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "analysis",
            self._should_continue_to_qa,
            {
                "continue": "quality_assurance",
                "retry": "analysis",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "quality_assurance",
            self._should_continue_to_generation,
            {
                "continue": "report_generation",
                "edit": "editing",
                "end": END
            }
        )
        
        # Add edge from editing back to analysis
        workflow.add_edge("editing", "analysis")
        
        workflow.add_edge("report_generation", END)
        
        # Set entry point
        workflow.set_entry_point("research_planning")
        
        return workflow.compile(checkpointer=self.checkpointer)
    
    async def _research_planning_supervisor(self, state: SupervisorState) -> SupervisorState:
        """Supervise the research planning phase"""
        logger.info("Starting research planning phase")
        
        state["current_phase"] = "research_planning"
        state["progress"]["current_phase"] = "research_planning"
        
        # Initialize phase-specific tracking
        phase_start_agents = len(state["completed_agents"])
        
        # Prepare context for agents
        agent_context = self.research_toolkit.prepare_context_for_agent(
            "ResearchPlanningTeam",
            source_types=["document"],
            keywords=[state["research_topic"]]
        )
        
        # Execute agents in sequence
        agents_to_run = [
            ("domain_analysis", self.domain_analysis_agent),
            ("literature_survey", self.literature_survey_agent),
            ("research_questions", self.research_question_agent)
        ]
        
        for agent_name, agent in agents_to_run:
            try:
                # Prepare agent state
                agent_state = AgentState(
                    messages=state["messages"],
                    research_topic=state["research_topic"],
                    current_task=f"Research planning: {agent_name}",
                    outputs=state["agent_outputs"],
                    metadata={"user_context": agent_context},
                    errors=state["errors"]
                )
                
                # Execute agent
                result_state = await agent.process(agent_state)
                
                # Update supervisor state
                state["agent_outputs"].update(result_state["outputs"])
                state["messages"].extend(result_state["messages"])
                state["completed_agents"].append(agent_name)
                
                logger.info(f"Completed {agent_name}")
                
            except Exception as e:
                logger.error(f"Error in {agent_name}", error=str(e))
                state["errors"].append(f"Research planning error in {agent_name}: {str(e)}")
        
        # Update progress
        state["progress"]["phases_completed"] = state.get("progress", {}).get("phases_completed", [])
        if "research_planning" not in state["progress"]["phases_completed"]:
            state["progress"]["phases_completed"].append("research_planning")
        
        state["progress"]["completion_percentage"] = len(state["progress"]["phases_completed"]) * 20
        
        # Log phase completion
        phase_completed_agents = len(state["completed_agents"]) - phase_start_agents
        logger.info("Research planning phase completed", 
                   phase_agents_completed=phase_completed_agents,
                   total_agents_completed=len(state["completed_agents"]))
        
        return state
    
    async def _data_collection_supervisor(self, state: SupervisorState) -> SupervisorState:
        """Supervise the data collection phase"""
        logger.info("Starting data collection phase")
        
        state["current_phase"] = "data_collection"
        state["progress"]["current_phase"] = "data_collection"
        
        # For now, data collection is primarily handled by research planning
        # In a full implementation, this would coordinate additional data gathering
        
        # Integrate user sources
        user_content = self.research_toolkit.get_all_user_content()
        state["user_sources"] = user_content
        
        # Update progress
        if "data_collection" not in state["progress"]["phases_completed"]:
            state["progress"]["phases_completed"].append("data_collection")
        
        state["progress"]["completion_percentage"] = len(state["progress"]["phases_completed"]) * 20
        
        logger.info("Completed data collection phase")
        return state
    
    async def _analysis_supervisor(self, state: SupervisorState) -> SupervisorState:
        """Supervise the analysis phase"""
        current_retry_count = state.get("qa_retry_count", 0)
        logger.info("Starting analysis phase", qa_retry_count=current_retry_count)
        
        state["current_phase"] = "analysis"
        state["progress"]["current_phase"] = "analysis"
        
        # Track phase-specific completion (important for retries)
        phase_start_agents = len(state["completed_agents"])
        
        # Clear any previous analysis results if this is a retry
        analysis_agent_names = ["quantitative_analysis", "qualitative_analysis", "synthesis"]
        for agent_name in analysis_agent_names:
            if agent_name in state["completed_agents"]:
                state["completed_agents"].remove(agent_name)
        
        # Prepare context for analysis agents
        agent_context = self.research_toolkit.prepare_context_for_agent(
            "AnalysisTeam",
            keywords=[state["research_topic"]]
        )
        
        # Execute analysis agents
        agents_to_run = [
            ("quantitative_analysis", self.quantitative_analysis_agent),
            ("qualitative_analysis", self.qualitative_analysis_agent),
            ("synthesis", self.synthesis_agent)
        ]
        
        for agent_name, agent in agents_to_run:
            try:
                agent_state = AgentState(
                    messages=state["messages"],
                    research_topic=state["research_topic"],
                    current_task=f"Analysis: {agent_name}",
                    outputs=state["agent_outputs"],
                    metadata={
                        "user_context": agent_context,
                        "user_sources": state["user_sources"]
                    },
                    errors=state["errors"]
                )
                
                result_state = await agent.process(agent_state)
                
                state["agent_outputs"].update(result_state["outputs"])
                state["messages"].extend(result_state["messages"])
                state["completed_agents"].append(agent_name)
                
                logger.info(f"Completed {agent_name}")
                
            except Exception as e:
                logger.error(f"Error in {agent_name}", error=str(e))
                state["errors"].append(f"Analysis error in {agent_name}: {str(e)}")
        
        # Update progress
        if "analysis" not in state["progress"]["phases_completed"]:
            state["progress"]["phases_completed"].append("analysis")
        
        state["progress"]["completion_percentage"] = len(state["progress"]["phases_completed"]) * 20
        
        # Log phase completion
        current_analysis_agents = len([a for a in state["completed_agents"] if a in analysis_agent_names])
        logger.info("Analysis phase completed", 
                   phase_agents_completed=current_analysis_agents,
                   total_agents_completed=len(state["completed_agents"]))
        
        return state
    
    async def _quality_assurance_supervisor(self, state: SupervisorState) -> SupervisorState:
        """Supervise the quality assurance phase"""
        current_retry_count = state.get("qa_retry_count", 0)
        logger.info("Starting quality assurance phase", qa_retry_count=current_retry_count)
        
        state["current_phase"] = "quality_assurance"
        state["progress"]["current_phase"] = "quality_assurance"
        
        # Track phase-specific completion
        phase_start_agents = len(state["completed_agents"])
        
        # Clear any previous QA results if this is running again
        qa_agent_names = ["peer_review", "citation_verification", "compliance_check"]
        for agent_name in qa_agent_names:
            if agent_name in state["completed_agents"]:
                state["completed_agents"].remove(agent_name)
        
        # Execute QA agents
        agents_to_run = [
            ("peer_review", self.peer_review_agent),
            ("citation_verification", self.citation_verification_agent),
            ("compliance_check", self.compliance_agent)
        ]
        
        for agent_name, agent in agents_to_run:
            try:
                agent_state = AgentState(
                    messages=state["messages"],
                    research_topic=state["research_topic"],
                    current_task=f"Quality assurance: {agent_name}",
                    outputs=state["agent_outputs"],
                    metadata={"requirements": state["requirements"]},
                    errors=state["errors"]
                )
                
                result_state = await agent.process(agent_state)
                
                state["agent_outputs"].update(result_state["outputs"])
                state["messages"].extend(result_state["messages"])
                state["completed_agents"].append(agent_name)
                
                logger.info(f"Completed {agent_name}")
                
            except Exception as e:
                logger.error(f"Error in {agent_name}", error=str(e))
                state["errors"].append(f"QA error in {agent_name}: {str(e)}")
        
        # Update progress
        if "quality_assurance" not in state["progress"]["phases_completed"]:
            state["progress"]["phases_completed"].append("quality_assurance")
        
        state["progress"]["completion_percentage"] = len(state["progress"]["phases_completed"]) * 20
        
        # Log phase completion
        current_qa_agents = len([a for a in state["completed_agents"] if a in qa_agent_names])
        logger.info("Quality assurance phase completed", 
                   phase_agents_completed=current_qa_agents,
                   total_agents_completed=len(state["completed_agents"]))
        
        # Check quality score and update retry count HERE in the supervisor
        # This ensures the state mutation happens in the main workflow, not the conditional edge
        if "PeerReviewAgent" in state["agent_outputs"]:
            try:
                peer_review_output = state["agent_outputs"]["PeerReviewAgent"]
                if isinstance(peer_review_output, dict):
                    peer_review = peer_review_output
                elif isinstance(peer_review_output, list) and peer_review_output:
                    peer_review = peer_review_output[0]
                else:
                    peer_review = {}
                
                quality_score = peer_review.get("quality_score", 7.0)
                current_retry_count = state.get("qa_retry_count", 0)
                
                if quality_score < 6.0 and current_retry_count < 3:
                    # Increment retry count in the main state
                    state["qa_retry_count"] = current_retry_count + 1
                    logger.info("Quality score below threshold, retry count updated", 
                               quality_score=quality_score, 
                               new_retry_count=state["qa_retry_count"])
                else:
                    logger.info("Quality score acceptable or max retries reached",
                               quality_score=quality_score,
                               retry_count=current_retry_count)
                    
            except Exception as e:
                logger.error("Error checking quality score in QA supervisor", error=str(e))
        
        return state
    
    async def _editing_supervisor(self, state: SupervisorState) -> SupervisorState:
        """Supervise the content editing phase based on QA feedback"""
        current_retry_count = state.get("qa_retry_count", 0)
        logger.info("Starting editing phase", qa_retry_count=current_retry_count)
        
        state["current_phase"] = "editing"
        state["progress"]["current_phase"] = "editing"
        
        try:
            # Execute editor agent
            agent_state = AgentState(
                messages=state["messages"],
                research_topic=state["research_topic"],
                current_task="Content editing based on QA feedback",
                outputs=state["agent_outputs"],
                metadata={
                    "requirements": state["requirements"],
                    "retry_count": current_retry_count
                },
                errors=state["errors"]
            )
            
            result_state = await self.editor_agent.process(agent_state)
            
            # Update state with editing results
            state["agent_outputs"].update(result_state["outputs"])
            state["messages"].extend(result_state["messages"])
            state["completed_agents"].append("editor")
            
            logger.info("Content editing completed", 
                       improvements_applied=result_state["outputs"].get("EditorAgent", {}).get("improvements_applied", []),
                       editing_action=result_state["outputs"].get("EditorAgent", {}).get("edit_action", "unknown"))
            
        except Exception as e:
            logger.error("Error in editing phase", error=str(e))
            state["errors"].append(f"Editing error: {str(e)}")
        
        # Update progress
        state["progress"]["completion_percentage"] = len(state["progress"]["phases_completed"]) * 20
        
        return state
    
    async def _report_generation_supervisor(self, state: SupervisorState) -> SupervisorState:
        """Supervise the report generation phase"""
        logger.info("Starting report generation phase")
        
        state["current_phase"] = "report_generation"
        state["progress"]["current_phase"] = "report_generation"
        
        # Generate report sections
        sections_to_write = ["introduction", "literature_review", "methodology", 
                           "results", "discussion", "conclusion"]
        
        for section_name in sections_to_write:
            try:
                # Set current section for the agent
                state["current_section"] = section_name
                
                agent_state = AgentState(
                    messages=state["messages"],
                    research_topic=state["research_topic"],
                    current_task=f"Writing {section_name} section",
                    outputs=state["agent_outputs"],
                    metadata={
                        "requirements": state["requirements"],
                        "current_section": section_name
                    },
                    errors=state["errors"]
                )
                
                result_state = await self.section_writing_agent.process(agent_state)
                
                state["agent_outputs"].update(result_state["outputs"])
                state["messages"].extend(result_state["messages"])
                
                logger.info(f"Completed {section_name} section")
                
            except Exception as e:
                logger.error(f"Error writing {section_name}", error=str(e))
                state["errors"].append(f"Report generation error in {section_name}: {str(e)}")
        
        # Ensure coherence
        try:
            agent_state = AgentState(
                messages=state["messages"],
                research_topic=state["research_topic"],
                current_task="Ensuring report coherence",
                outputs=state["agent_outputs"],
                metadata={"requirements": state["requirements"]},
                errors=state["errors"]
            )
            
            result_state = await self.coherence_agent.process(agent_state)
            state["agent_outputs"].update(result_state["outputs"])
            
            logger.info("Completed coherence integration")
            
        except Exception as e:
            logger.error("Error in coherence integration", error=str(e))
            state["errors"].append(f"Coherence integration error: {str(e)}")
        
        # Final assembly
        try:
            agent_state = AgentState(
                messages=state["messages"],
                research_topic=state["research_topic"],
                current_task="Final report assembly",
                outputs=state["agent_outputs"],
                metadata={"requirements": state["requirements"]},
                errors=state["errors"]
            )
            
            result_state = await self.final_assembly_agent.process(agent_state)
            state["agent_outputs"].update(result_state["outputs"])
            
            logger.info("Completed final assembly")
            
        except Exception as e:
            logger.error("Error in final assembly", error=str(e))
            state["errors"].append(f"Final assembly error: {str(e)}")
        
        # Update progress
        if "report_generation" not in state["progress"]["phases_completed"]:
            state["progress"]["phases_completed"].append("report_generation")
        
        state["progress"]["completion_percentage"] = 100
        state["progress"]["completed_at"] = datetime.now().isoformat()
        
        return state
    
    def _should_continue_to_data_collection(self, state: SupervisorState) -> str:
        """Decide whether to continue to data collection"""
        if state["errors"]:
            if len(state["errors"]) > 3:  # Too many errors
                return "end"
            return "retry"
        
        # Check if research planning completed successfully
        required_outputs = ["DomainAnalysisAgent", "LiteratureSurveyAgent", "ResearchQuestionFormulationAgent"]
        if all(agent in state["agent_outputs"] for agent in required_outputs):
            return "continue"
        
        return "retry"
    
    def _should_continue_to_analysis(self, state: SupervisorState) -> str:
        """Decide whether to continue to analysis"""
        if state["errors"] and len(state["errors"]) > 5:
            return "end"
        
        # Data collection is successful if we reach this point
        return "continue"
    
    def _should_continue_to_qa(self, state: SupervisorState) -> str:
        """Decide whether to continue to quality assurance"""
        if state["errors"] and len(state["errors"]) > 7:
            return "end"
        
        # Check if analysis completed
        required_outputs = ["QuantitativeAnalysisAgent", "QualitativeAnalysisAgent", "SynthesisAgent"]
        if all(agent in state["agent_outputs"] for agent in required_outputs):
            return "continue"
        
        return "retry"
    
    def _should_continue_to_generation(self, state: SupervisorState) -> str:
        """Decide whether to continue to report generation"""
        if state["errors"] and len(state["errors"]) > 10:
            return "end"
        
        # Check retry limit to prevent infinite loops
        retry_count = state.get("qa_retry_count", 0)
        logger.info("Checking retry count in conditional edge", current_retry_count=retry_count)
        
        if retry_count >= 3:  # Maximum 3 retries
            logger.warning("Maximum quality assurance retries reached, proceeding to generation")
            return "continue"
        
        # Check quality score from peer review (logic moved to QA supervisor)
        if "PeerReviewAgent" in state["agent_outputs"]:
            try:
                # Handle both list and dict formats
                peer_review_output = state["agent_outputs"]["PeerReviewAgent"]
                if isinstance(peer_review_output, list) and peer_review_output:
                    peer_review = peer_review_output[0]
                elif isinstance(peer_review_output, dict):
                    peer_review = peer_review_output
                else:
                    logger.warning("Unexpected PeerReviewAgent output format, proceeding to generation")
                    return "continue"
                
                quality_score = peer_review.get("quality_score", 7.0)  # Default to passing score
                logger.info("Quality score evaluation in conditional edge", quality_score=quality_score, retry_count=retry_count)
                
                if quality_score < 6.0 and retry_count < 3:  # Below acceptable threshold and not at max retries
                    logger.info("Quality score below threshold, will edit content", 
                               quality_score=quality_score, 
                               current_retry_count=retry_count)
                    return "edit"
            except Exception as e:
                logger.error("Error evaluating quality score, proceeding to generation", error=str(e))
                return "continue"
        
        return "continue"
    
    async def execute_workflow(self, 
                             research_topic: str,
                             requirements: Dict[str, Any],
                             progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Execute the complete research workflow"""
        
        # Initialize state
        initial_state = SupervisorState(
            messages=[],
            research_topic=research_topic,
            current_phase="initialization",
            agent_outputs={},
            next_agent="",
            completed_agents=[],
            requirements=requirements,
            user_sources={},
            progress={
                "current_phase": "initialization",
                "completion_percentage": 0,
                "phases_completed": [],
                "start_time": datetime.now().isoformat()
            },
            errors=[],
            qa_retry_count=0  # Track quality assurance retry attempts
        )
        
        # Create a thread for this workflow execution
        thread_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Execute workflow
            config = {"configurable": {"thread_id": thread_id}}
            
            async for state in self.workflow.astream(initial_state, config):
                # Call progress callback if provided
                if progress_callback and "progress" in state:
                    progress_info = state["progress"]
                    phase = progress_info.get("current_phase", "unknown")
                    percentage = progress_info.get("completion_percentage", 0)
                    progress_callback(phase, percentage)
                
                # Log progress only for meaningful state changes
                current_phase = state.get("current_phase")
                completed_agents = state.get("completed_agents", [])
                
                # Only log if we have actual progress (not intermediate/empty states)
                if current_phase and current_phase != "unknown" and current_phase != "initialization":
                    logger.info("Workflow progress", 
                               phase=current_phase, 
                               completed_agents=len(completed_agents))
            
            # Get final state
            final_state = state
            
            # Log final workflow completion
            if final_state:
                total_completed = len(final_state.get("completed_agents", []))
                final_phase = final_state.get("current_phase", "completed")
                logger.info("Workflow completed", 
                           phase=final_phase, 
                           total_completed_agents=total_completed)
            
            # Prepare result with safe access to potentially missing keys
            errors = final_state.get("errors", [])
            agent_outputs = final_state.get("agent_outputs", {})
            progress = final_state.get("progress", {"completion_percentage": 0})
            completed_agents = final_state.get("completed_agents", [])
            
            result = {
                "status": "completed" if not errors else "completed_with_errors",
                "research_topic": research_topic,
                "agent_outputs": agent_outputs,
                "progress": progress,
                "errors": errors,
                "completed_agents": completed_agents,
                "thread_id": thread_id
            }
            
            logger.info("Workflow execution completed", 
                       status=result["status"],
                       completed_agents=len(result["completed_agents"]))
            
            return result
            
        except Exception as e:
            logger.error("Workflow execution failed", error=str(e))
            return {
                "status": "failed",
                "error": str(e),
                "research_topic": research_topic,
                "agent_outputs": {},
                "progress": initial_state["progress"],
                "errors": [str(e)],
                "thread_id": thread_id
            }