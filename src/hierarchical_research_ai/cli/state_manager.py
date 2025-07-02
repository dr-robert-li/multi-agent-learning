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
            "depth": "comprehensive",
            # Strategic Analysis Template fields
            "strategic_analysis": {
                "organization_name": "",
                "organization_type": "",
                "industry_sector": "",
                "organization_size": "",
                "business_model": "",
                "strategic_challenge": "",
                "time_horizon": "",
                "urgency_level": "",
                "decision_context": "",
                "current_performance": "",
                "known_challenges": "",
                "stakeholder_context": "",
                "technology_relevance": "",
                "market_evolution": "",
                "transformation_scope": "",
                "resource_constraints": "",
                "risk_tolerance": "",
                "success_metrics": "",
                "implementation_capacity": ""
            }
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
    
    def update_requirements(self, category: str, updates: Any):
        """Update requirements based on user responses"""
        if category in self.requirements:
            if isinstance(self.requirements[category], dict) and isinstance(updates, dict):
                # Both are dicts, merge them
                self.requirements[category].update(updates)
            else:
                # Direct assignment for non-dict values or when types don't match
                self.requirements[category] = updates
        else:
            # Add new category if it doesn't exist
            self.requirements[category] = updates
        
        self.update_completeness()
    
    def update_completeness(self):
        """Calculate requirement completeness score"""
        # Check if this is a strategic analysis project
        is_strategic = self._is_strategic_analysis()
        
        if is_strategic:
            self._calculate_strategic_completeness()
        else:
            self._calculate_standard_completeness()
    
    def _is_strategic_analysis(self) -> bool:
        """Determine if this is a strategic business analysis"""
        topic = self.requirements.get("topic", "").lower()
        
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
        
        # Check primary keywords
        if any(keyword in topic for keyword in primary_keywords):
            return True
        
        # Check strategic combinations
        for combo in strategic_combinations:
            if all(word in topic for word in combo):
                return True
        
        return False
    
    def _calculate_strategic_completeness(self):
        """Calculate completeness for strategic analysis projects"""
        # Essential strategic categories (weighted)
        essential_categories = [
            ("topic", 1.0),
            ("strategic_analysis.organization_type", 0.8),
            ("strategic_analysis.strategic_challenge", 1.0),
            ("strategic_analysis.time_horizon", 0.6),
            ("scope", 0.7),
            ("constraints", 0.6)
        ]
        
        # Optional categories
        optional_categories = [
            ("strategic_analysis.organization_name", 0.3),
            ("strategic_analysis.industry_sector", 0.5),
            ("strategic_analysis.decision_context", 0.4),
            ("methodology", 0.4),
            ("output_preferences", 0.3),
            ("strategic_analysis.success_metrics", 0.5)
        ]
        
        total_weight = sum(weight for _, weight in essential_categories + optional_categories)
        completed_weight = 0.0
        
        # Check essential categories
        for category_path, weight in essential_categories:
            if self._check_category_completion(category_path):
                completed_weight += weight
        
        # Check optional categories
        for category_path, weight in optional_categories:
            if self._check_category_completion(category_path):
                completed_weight += weight
        
        self.completeness_score = completed_weight / total_weight
    
    def _calculate_standard_completeness(self):
        """Calculate completeness for standard research projects"""
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
    
    def _check_category_completion(self, category_path: str) -> bool:
        """Check if a nested category is completed"""
        if '.' in category_path:
            main_cat, sub_cat = category_path.split('.', 1)
            return (self.requirements.get(main_cat, {}).get(sub_cat, "") != "")
        else:
            value = self.requirements.get(category_path, "")
            return bool(value) if not isinstance(value, dict) else bool(value)
    
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