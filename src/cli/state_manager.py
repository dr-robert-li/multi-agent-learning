"""
Conversation State Manager

Manages the state of CLI conversations and requirement gathering.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class ConversationStateManager:
    """Manages conversation state and requirement completeness"""
    
    def __init__(self):
        self.requirements = {
            "topic": "",
            "scope": {},
            "methodology": {},
            "constraints": {},
            "output_preferences": {},
            "quality_standards": {},
            "privacy_mode": False,
            "budget_limit": 50.0,
            "target_length": 50000,
            "citation_style": "APA",
            "audience": "",
            "depth": "comprehensive"
        }
        self.conversation_history = []
        self.clarification_count = 0
        self.completeness_score = 0.0
        self.start_time = datetime.now()
    
    def add_to_history(self, role: str, content: str):
        """Add a message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def update_requirements(self, category: str, updates: Dict[str, Any]):
        """Update requirements based on user responses"""
        if category in self.requirements:
            if isinstance(self.requirements[category], dict):
                self.requirements[category].update(updates)
            else:
                self.requirements[category] = updates
        
        self.update_completeness()
    
    def update_completeness(self):
        """Calculate requirement completeness score"""
        total_categories = 10  # Number of requirement categories
        completed_categories = 0
        
        # Check each category for completeness
        if self.requirements["topic"]:
            completed_categories += 1
        if self.requirements["scope"]:
            completed_categories += 1
        if self.requirements["methodology"]:
            completed_categories += 1
        if self.requirements["constraints"]:
            completed_categories += 1
        if self.requirements["output_preferences"]:
            completed_categories += 1
        if self.requirements["quality_standards"]:
            completed_categories += 1
        if self.requirements.get("budget_limit"):
            completed_categories += 1
        if self.requirements.get("target_length"):
            completed_categories += 1
        if self.requirements.get("audience"):
            completed_categories += 1
        if self.requirements.get("citation_style"):
            completed_categories += 1
            
        self.completeness_score = completed_categories / total_categories
    
    def assess_readiness(self) -> bool:
        """Determine if enough information has been gathered"""
        return self.completeness_score >= 0.75  # 75% completeness threshold
    
    def get_missing_requirements(self) -> List[str]:
        """Get list of missing requirement categories"""
        missing = []
        
        if not self.requirements["topic"]:
            missing.append("research topic")
        if not self.requirements["scope"]:
            missing.append("scope definition")
        if not self.requirements["audience"]:
            missing.append("target audience")
        if not self.requirements["methodology"]:
            missing.append("research methodology")
        if not self.requirements["output_preferences"]:
            missing.append("output preferences")
        
        return missing
    
    def generate_research_config(self) -> Dict[str, Any]:
        """Convert conversation state to research system configuration"""
        return {
            "topic": self.requirements["topic"],
            "target_length": self.requirements.get("target_length", 50000),
            "citation_style": self.requirements.get("citation_style", "APA"),
            "privacy_mode": self.requirements.get("privacy_mode", False),
            "budget_limit": self.requirements.get("budget_limit", 50.0),
            "quality_level": "academic_thesis",
            "research_depth": self.requirements.get("depth", "comprehensive"),
            "source_constraints": self.requirements.get("constraints", {}),
            "scope_definition": self.requirements.get("scope", {}),
            "audience": self.requirements.get("audience", "academic"),
            "methodology_preferences": self.requirements.get("methodology", {})
        }
    
    def export_state(self) -> str:
        """Export current state as JSON"""
        state = {
            "requirements": self.requirements,
            "conversation_history": self.conversation_history,
            "clarification_count": self.clarification_count,
            "completeness_score": self.completeness_score,
            "start_time": self.start_time.isoformat(),
            "duration": str(datetime.now() - self.start_time)
        }
        return json.dumps(state, indent=2)
    
    def import_state(self, state_json: str):
        """Import state from JSON"""
        state = json.loads(state_json)
        self.requirements = state["requirements"]
        self.conversation_history = state["conversation_history"]
        self.clarification_count = state["clarification_count"]
        self.completeness_score = state["completeness_score"]
        self.start_time = datetime.fromisoformat(state["start_time"])