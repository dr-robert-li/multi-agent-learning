"""
Memory Management

Handles conversation memory, context management, and session state persistence.
"""

import os
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import structlog
from collections import deque

logger = structlog.get_logger()


class MemoryManager:
    """Manages conversation memory and context for research sessions"""
    
    def __init__(self, max_context_length: int = 50000, max_conversation_turns: int = 100):
        self.max_context_length = max_context_length
        self.max_conversation_turns = max_conversation_turns
        
        # Memory components
        self.conversation_memory = deque(maxlen=max_conversation_turns)
        self.agent_memory = {}
        self.context_summary = ""
        self.key_findings = []
        self.important_facts = []
        
    def add_conversation_turn(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a conversation turn to memory"""
        turn = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.conversation_memory.append(turn)
        logger.debug("Added conversation turn", role=role, content_length=len(content))
    
    def add_agent_output(self, agent_name: str, output: Dict[str, Any]):
        """Add agent output to memory"""
        if agent_name not in self.agent_memory:
            self.agent_memory[agent_name] = []
        
        memory_entry = {
            'timestamp': datetime.now().isoformat(),
            'output': output,
            'summary': self._create_output_summary(output)
        }
        
        self.agent_memory[agent_name].append(memory_entry)
        
        # Extract key findings
        self._extract_key_findings(agent_name, output)
        
        logger.debug("Added agent output to memory", agent=agent_name)
    
    def get_conversation_context(self, last_n_turns: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get recent conversation context"""
        if last_n_turns is None:
            return list(self.conversation_memory)
        
        return list(self.conversation_memory)[-last_n_turns:]
    
    def get_agent_context(self, agent_name: str, last_n_outputs: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get context for a specific agent"""
        if agent_name not in self.agent_memory:
            return []
        
        outputs = self.agent_memory[agent_name]
        if last_n_outputs is None:
            return outputs
        
        return outputs[-last_n_outputs:]
    
    def get_relevant_context(self, query: str, max_items: int = 10) -> Dict[str, Any]:
        """Get context relevant to a query"""
        query_lower = query.lower()
        relevant_context = {
            'conversation_turns': [],
            'agent_outputs': {},
            'key_findings': [],
            'important_facts': []
        }
        
        # Search conversation turns
        for turn in self.conversation_memory:
            if query_lower in turn['content'].lower():
                relevant_context['conversation_turns'].append(turn)
        
        # Search agent outputs
        for agent_name, outputs in self.agent_memory.items():
            relevant_outputs = []
            for output_entry in outputs:
                if query_lower in str(output_entry['output']).lower():
                    relevant_outputs.append(output_entry)
            
            if relevant_outputs:
                relevant_context['agent_outputs'][agent_name] = relevant_outputs[-max_items:]
        
        # Search key findings
        relevant_context['key_findings'] = [
            finding for finding in self.key_findings
            if query_lower in finding['content'].lower()
        ]
        
        # Search important facts
        relevant_context['important_facts'] = [
            fact for fact in self.important_facts
            if query_lower in fact['content'].lower()
        ]
        
        return relevant_context
    
    def summarize_session(self) -> Dict[str, Any]:
        """Create a comprehensive session summary"""
        summary = {
            'conversation_summary': self._summarize_conversation(),
            'agent_summaries': self._summarize_agent_outputs(),
            'key_findings': self.key_findings,
            'important_facts': self.important_facts,
            'statistics': {
                'conversation_turns': len(self.conversation_memory),
                'agents_used': len(self.agent_memory),
                'total_agent_outputs': sum(len(outputs) for outputs in self.agent_memory.values()),
                'key_findings_count': len(self.key_findings),
                'important_facts_count': len(self.important_facts)
            }
        }
        
        return summary
    
    def compress_memory(self, compression_ratio: float = 0.5):
        """Compress memory by summarizing older content"""
        # Compress conversation memory
        current_size = len(self.conversation_memory)
        target_size = int(current_size * compression_ratio)
        
        if current_size > target_size:
            # Keep recent turns, summarize older ones
            recent_turns = list(self.conversation_memory)[-target_size:]
            older_turns = list(self.conversation_memory)[:-target_size]
            
            # Create summary of older turns
            older_summary = self._create_conversation_summary(older_turns)
            
            # Reset conversation memory with summary + recent turns
            self.conversation_memory.clear()
            self.conversation_memory.append({
                'role': 'system',
                'content': f"[Previous conversation summary: {older_summary}]",
                'timestamp': datetime.now().isoformat(),
                'metadata': {'type': 'compression_summary'}
            })
            
            for turn in recent_turns:
                self.conversation_memory.append(turn)
        
        # Compress agent memory
        for agent_name in self.agent_memory:
            outputs = self.agent_memory[agent_name]
            if len(outputs) > 10:  # Keep only recent 10 outputs per agent
                self.agent_memory[agent_name] = outputs[-10:]
        
        logger.info("Compressed memory", original_turns=current_size, compressed_turns=len(self.conversation_memory))
    
    def export_memory(self) -> Dict[str, Any]:
        """Export memory state for persistence"""
        return {
            'conversation_memory': list(self.conversation_memory),
            'agent_memory': self.agent_memory,
            'context_summary': self.context_summary,
            'key_findings': self.key_findings,
            'important_facts': self.important_facts,
            'export_timestamp': datetime.now().isoformat()
        }
    
    def import_memory(self, memory_data: Dict[str, Any]):
        """Import memory state from persistence"""
        self.conversation_memory.clear()
        for turn in memory_data.get('conversation_memory', []):
            self.conversation_memory.append(turn)
        
        self.agent_memory = memory_data.get('agent_memory', {})
        self.context_summary = memory_data.get('context_summary', '')
        self.key_findings = memory_data.get('key_findings', [])
        self.important_facts = memory_data.get('important_facts', [])
        
        logger.info("Imported memory state", 
                   conversation_turns=len(self.conversation_memory),
                   agents=len(self.agent_memory))
    
    def clear_memory(self):
        """Clear all memory"""
        self.conversation_memory.clear()
        self.agent_memory.clear()
        self.context_summary = ""
        self.key_findings.clear()
        self.important_facts.clear()
        
        logger.info("Cleared all memory")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        # Calculate memory usage
        conversation_size = sum(len(str(turn)) for turn in self.conversation_memory)
        agent_memory_size = sum(len(str(outputs)) for outputs in self.agent_memory.values())
        
        return {
            'conversation_turns': len(self.conversation_memory),
            'agent_outputs_count': sum(len(outputs) for outputs in self.agent_memory.values()),
            'agents_used': len(self.agent_memory),
            'key_findings_count': len(self.key_findings),
            'important_facts_count': len(self.important_facts),
            'estimated_memory_size_bytes': conversation_size + agent_memory_size,
            'max_context_length': self.max_context_length,
            'max_conversation_turns': self.max_conversation_turns
        }
    
    def _create_output_summary(self, output: Dict[str, Any]) -> str:
        """Create a summary of agent output"""
        summary_parts = []
        
        # Common output fields to summarize
        if 'analysis' in output:
            summary_parts.append(f"Analysis: {str(output['analysis'])[:200]}...")
        
        if 'findings' in output:
            summary_parts.append(f"Findings: {len(output['findings'])} items")
        
        if 'recommendations' in output:
            summary_parts.append(f"Recommendations: {len(output['recommendations'])} items")
        
        if 'key_findings' in output:
            summary_parts.append(f"Key findings: {len(output['key_findings'])} items")
        
        return "; ".join(summary_parts) if summary_parts else "Agent output recorded"
    
    def _extract_key_findings(self, agent_name: str, output: Dict[str, Any]):
        """Extract key findings from agent output"""
        findings_fields = ['key_findings', 'findings', 'insights', 'important_points']
        
        for field in findings_fields:
            if field in output and isinstance(output[field], list):
                for finding in output[field]:
                    finding_entry = {
                        'content': str(finding),
                        'source_agent': agent_name,
                        'timestamp': datetime.now().isoformat(),
                        'importance': self._assess_importance(str(finding))
                    }
                    
                    self.key_findings.append(finding_entry)
        
        # Keep only top findings (by importance)
        self.key_findings.sort(key=lambda x: x['importance'], reverse=True)
        self.key_findings = self.key_findings[:50]  # Keep top 50
    
    def _assess_importance(self, content: str) -> float:
        """Assess the importance of a finding (simple heuristic)"""
        importance_keywords = [
            'significant', 'important', 'critical', 'key', 'major', 'primary',
            'conclusion', 'result', 'finding', 'discovery', 'insight'
        ]
        
        content_lower = content.lower()
        score = 0.0
        
        # Keyword-based scoring
        for keyword in importance_keywords:
            if keyword in content_lower:
                score += 1.0
        
        # Length-based scoring (longer findings might be more detailed)
        score += min(len(content) / 1000, 2.0)
        
        # Numbers and data (findings with numbers might be more concrete)
        import re
        if re.search(r'\d+', content):
            score += 0.5
        
        return score
    
    def _summarize_conversation(self) -> str:
        """Create a summary of the conversation"""
        if not self.conversation_memory:
            return "No conversation recorded"
        
        # Simple summarization by extracting key topics
        topics = set()
        user_questions = []
        
        for turn in self.conversation_memory:
            content = turn['content'].lower()
            
            # Extract questions
            if turn['role'] == 'user' and '?' in content:
                user_questions.append(turn['content'])
            
            # Extract potential topics (simple keyword extraction)
            words = content.split()
            for word in words:
                if len(word) > 5 and word.isalpha():
                    topics.add(word)
        
        summary_parts = [
            f"Conversation with {len(self.conversation_memory)} turns",
            f"Key topics discussed: {', '.join(list(topics)[:10])}",
            f"User questions: {len(user_questions)}"
        ]
        
        return "; ".join(summary_parts)
    
    def _summarize_agent_outputs(self) -> Dict[str, str]:
        """Create summaries for each agent's outputs"""
        summaries = {}
        
        for agent_name, outputs in self.agent_memory.items():
            if outputs:
                summary_parts = [
                    f"{len(outputs)} outputs from {agent_name}",
                    f"Latest: {outputs[-1]['summary']}"
                ]
                summaries[agent_name] = "; ".join(summary_parts)
        
        return summaries
    
    def _create_conversation_summary(self, turns: List[Dict[str, Any]]) -> str:
        """Create a summary of specific conversation turns"""
        if not turns:
            return "No conversation turns"
        
        user_messages = [turn['content'] for turn in turns if turn['role'] == 'user']
        assistant_messages = [turn['content'] for turn in turns if turn['role'] == 'assistant']
        
        summary = f"Summary of {len(turns)} conversation turns: "
        summary += f"{len(user_messages)} user messages, {len(assistant_messages)} assistant responses. "
        
        # Key topics (simplified)
        all_content = " ".join(turn['content'] for turn in turns)
        words = all_content.lower().split()
        common_words = [w for w in words if len(w) > 5][:10]
        
        if common_words:
            summary += f"Key topics: {', '.join(common_words)}"
        
        return summary