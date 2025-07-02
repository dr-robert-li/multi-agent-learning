"""
Response Parser for CLI Conversations

Parses and interprets user responses to update research requirements.
"""

import re
from typing import Dict, Any, Tuple, Optional
from datetime import datetime


class ResponseParser:
    """Parses user responses and extracts requirement updates"""
    
    # Keywords for different requirement categories
    CATEGORY_KEYWORDS = {
        "scope": ["focus", "include", "exclude", "boundaries", "limit", "scope", "cover", "aspect"],
        "methodology": ["method", "approach", "empirical", "theoretical", "qualitative", "quantitative", "mixed"],
        "constraints": ["avoid", "don't", "exclude", "sensitive", "confidential", "restrict", "limitation"],
        "output_preferences": ["format", "structure", "sections", "length", "style", "report", "document"],
        "quality_standards": ["quality", "rigor", "peer-review", "academic", "professional", "standard"],
        "audience": ["audience", "readers", "for", "aimed at", "targeted", "level"],
        "timeline": ["deadline", "by", "when", "timeline", "urgent", "asap", "timeframe"],
        "sources": ["sources", "references", "cite", "papers", "journals", "databases", "evidence"]
    }
    
    # Patterns for extracting specific values
    PATTERNS = {
        "word_count": r'\b(\d{1,3}(?:,?\d{3})*)\s*(?:words?|word\s*count)\b',
        "page_count": r'\b(\d+)\s*(?:pages?)\b',
        "budget": r'\$?\s*(\d+(?:\.\d{2})?)\s*(?:dollars?|usd|budget)?',
        "citation_style": r'\b(APA|MLA|Chicago|IEEE|Harvard|Vancouver)\b',
        "date": r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b'
    }
    
    def parse_response(self, user_response: str, context: str = "") -> Dict[str, Any]:
        """Parse user response and extract requirement updates"""
        response_lower = user_response.lower()
        updates = {}
        
        # First, check if this is answering a specific question about the context
        updates_from_context = self._parse_contextual_response(user_response, context)
        if updates_from_context:
            return updates_from_context
        
        # Determine which categories the response addresses
        categories = self._identify_categories(response_lower)
        
        # Extract specific values
        extracted_values = self._extract_values(user_response)
        updates.update(extracted_values)
        
        # Parse based on identified categories
        for category in categories:
            category_updates = self._parse_category(category, user_response, context)
            if category_updates:
                updates[category] = category_updates
        
        # Parse yes/no responses
        if self._is_affirmative(response_lower):
            updates["confirmed"] = True
        elif self._is_negative(response_lower):
            updates["confirmed"] = False
        
        return updates
    
    def _identify_categories(self, response_lower: str) -> list:
        """Identify which requirement categories the response addresses"""
        categories = []
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(keyword in response_lower for keyword in keywords):
                categories.append(category)
        
        return categories
    
    def _extract_values(self, response: str) -> Dict[str, Any]:
        """Extract specific values from response using patterns"""
        extracted = {}
        
        # Extract word count
        word_match = re.search(self.PATTERNS["word_count"], response, re.I)
        if word_match:
            word_count = int(word_match.group(1).replace(',', ''))
            extracted["target_length"] = word_count
        
        # Extract page count and convert to words (approx 250 words per page)
        page_match = re.search(self.PATTERNS["page_count"], response, re.I)
        if page_match and "target_length" not in extracted:
            page_count = int(page_match.group(1))
            extracted["target_length"] = page_count * 250
        
        # Extract budget
        budget_match = re.search(self.PATTERNS["budget"], response, re.I)
        if budget_match:
            extracted["budget_limit"] = float(budget_match.group(1))
        
        # Extract citation style
        citation_match = re.search(self.PATTERNS["citation_style"], response, re.I)
        if citation_match:
            extracted["citation_style"] = citation_match.group(1).upper()
        
        return extracted
    
    def _parse_category(self, category: str, response: str, context: str) -> Dict[str, Any]:
        """Parse response for a specific category"""
        category_data = {}
        
        if category == "scope":
            # Extract what to include/exclude
            include_match = re.search(r'(?:include|focus on|cover)\s+(.+?)(?:\.|,|$)', response, re.I)
            if include_match:
                category_data["include"] = include_match.group(1).strip()
            
            exclude_match = re.search(r'(?:exclude|avoid|don\'t include)\s+(.+?)(?:\.|,|$)', response, re.I)
            if exclude_match:
                category_data["exclude"] = exclude_match.group(1).strip()
        
        elif category == "methodology":
            # Identify methodology preferences
            if any(word in response.lower() for word in ["empirical", "data", "experiment"]):
                category_data["type"] = "empirical"
            elif any(word in response.lower() for word in ["theoretical", "conceptual", "framework"]):
                category_data["type"] = "theoretical"
            elif any(word in response.lower() for word in ["mixed", "both", "combination"]):
                category_data["type"] = "mixed"
        
        elif category == "audience":
            # Extract audience information
            audience_match = re.search(r'(?:for|aimed at|targeted at)\s+(.+?)(?:\.|,|$)', response, re.I)
            if audience_match:
                category_data["target"] = audience_match.group(1).strip()
            
            # Determine complexity level
            if any(word in response.lower() for word in ["expert", "professional", "academic", "researcher"]):
                category_data["level"] = "expert"
            elif any(word in response.lower() for word in ["general", "public", "layperson", "beginner"]):
                category_data["level"] = "general"
            elif any(word in response.lower() for word in ["student", "undergraduate", "graduate"]):
                category_data["level"] = "student"
        
        return category_data
    
    def _parse_contextual_response(self, response: str, context: str) -> Dict[str, Any]:
        """Parse response based on the question context"""
        context_lower = context.lower()
        response_lower = response.lower()
        
        # Generic mapping based on question patterns
        if "audience" in context_lower or "stakeholder" in context_lower or "who" in context_lower:
            return {"audience": response.strip()}
        
        elif "domain" in context_lower or "context" in context_lower or "area" in context_lower:
            return {"scope": {"domain": response.strip()}}
        
        elif "outcome" in context_lower or "decision" in context_lower or "goal" in context_lower:
            return {"scope": {"outcomes": response.strip()}}
        
        elif "format" in context_lower or "level of detail" in context_lower:
            return {"output_preferences": {"format": response.strip()}}
        
        elif "geographic" in context_lower or "location" in context_lower or "region" in context_lower:
            # Check if it's asking about both geographic AND industry
            if "industry" in context_lower or "sector" in context_lower:
                return {"scope": {"industry": response.strip()}}
            else:
                return {"scope": {"geographic": response.strip()}}
        
        elif "industry" in context_lower or "sector" in context_lower or "market" in context_lower:
            return {"scope": {"industry": response.strip()}}
            
        elif "type of" in context_lower and "insight" in context_lower:
            return {"scope": {"insight_types": response.strip()}}
        
        elif "timeline" in context_lower or "deadline" in context_lower or "when" in context_lower:
            return {"constraints": {"timeline": response.strip()}}
        
        elif "budget" in context_lower or "cost" in context_lower or "price" in context_lower:
            # Try to extract numeric value
            budget_match = re.search(r'\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', response)
            if budget_match:
                return {"budget_limit": float(budget_match.group(1).replace(',', ''))}
            else:
                return {"constraints": {"budget": response.strip()}}
        
        # For strategic analysis mode - check for strategic categories
        if any(prefix in context_lower for prefix in ["[context]", "[challenge]", "[scope]", "[baseline]", "[market]", "[metrics]", "[impact]"]):
            # Extract category from question
            category_match = re.search(r'\[(\w+)\]', context)
            if category_match:
                category = category_match.group(1).lower()
                
                # Map to strategic analysis fields
                if category == "context":
                    if "organization" in context_lower:
                        return {"strategic_analysis": {"organization_type": response.strip()}}
                    elif "industry" in context_lower:
                        return {"strategic_analysis": {"industry_sector": response.strip()}}
                
                elif category == "challenge":
                    return {"strategic_analysis": {"strategic_challenge": response.strip()}}
                
                elif category == "scope":
                    if "timeframe" in context_lower or "horizon" in context_lower:
                        return {"strategic_analysis": {"time_horizon": response.strip()}}
                    elif "constraint" in context_lower or "resource" in context_lower:
                        return {"strategic_analysis": {"resource_constraints": response.strip()}}
                
                elif category == "baseline":
                    return {"strategic_analysis": {"current_performance": response.strip()}}
                
                elif category == "market":
                    return {"strategic_analysis": {"market_evolution": response.strip()}}
                
                elif category == "metrics":
                    return {"strategic_analysis": {"success_metrics": response.strip()}}
                
                elif category == "impact":
                    return {"strategic_analysis": {"decision_context": response.strip()}}
        
        # If no specific pattern matched but response is substantive, store it generically
        if len(response.strip()) > 3 and response.strip().lower() not in ["yes", "no", "none", "n/a"]:
            # Store as general requirement info
            return {"scope": {"additional_info": response.strip()}}
        
        return {}
    
    def _is_affirmative(self, response: str) -> bool:
        """Check if response is affirmative"""
        affirmative_words = ["yes", "yeah", "yep", "sure", "okay", "ok", "correct", 
                           "right", "absolutely", "definitely", "certainly", "indeed"]
        return any(word in response.split() for word in affirmative_words)
    
    def _is_negative(self, response: str) -> bool:
        """Check if response is negative"""
        negative_words = ["no", "nope", "not", "negative", "incorrect", "wrong", 
                         "disagree", "false", "never"]
        return any(word in response.split() for word in negative_words)
    
    def extract_topic(self, response: str) -> Optional[str]:
        """Extract research topic from response"""
        # Remove common prefixes
        prefixes = ["i want to research", "i'd like to research", "research on", 
                   "let's research", "please research", "my topic is", "the topic is"]
        
        clean_response = response.lower()
        for prefix in prefixes:
            if clean_response.startswith(prefix):
                topic = response[len(prefix):].strip()
                return topic.strip('".?!')
        
        # If no prefix found, clean up the response
        # Remove question marks and quotes
        topic = response.strip('".?!')
        
        # If it's a short response, likely the topic itself
        if len(response.split()) <= 10:
            return topic
        
        return None