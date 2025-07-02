"""
Privacy Manager

Handles privacy-sensitive operations and data protection.
"""

import os
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog

logger = structlog.get_logger()


class PrivacyManager:
    """Manages privacy settings and data protection"""
    
    def __init__(self):
        self.privacy_mode = os.getenv("PRIVACY_MODE", "false").lower() == "true"
        self.data_retention_days = int(os.getenv("DATA_RETENTION_DAYS", "30"))
        self.anonymize_data = os.getenv("ANONYMIZE_DATA", "false").lower() == "true"
    
    def is_privacy_mode_enabled(self) -> bool:
        """Check if privacy mode is enabled"""
        return self.privacy_mode
    
    def sanitize_data(self, data: Any) -> Any:
        """Sanitize sensitive data based on privacy settings"""
        if not self.privacy_mode:
            return data
        
        if isinstance(data, dict):
            return {key: self.sanitize_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_data(item) for item in data]
        elif isinstance(data, str):
            return self._sanitize_string(data)
        else:
            return data
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize sensitive information from text"""
        if not self.anonymize_data:
            return text
        
        # Simple sanitization patterns
        import re
        
        # Email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        
        # Phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        
        # Social security numbers
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
        
        # Credit card numbers
        text = re.sub(r'\b\d{4}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b', '[CREDIT_CARD]', text)
        
        return text
    
    def hash_sensitive_data(self, data: str) -> str:
        """Create a hash of sensitive data for identification without exposure"""
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def get_privacy_warning(self) -> str:
        """Get privacy mode warning message"""
        if not self.privacy_mode:
            return ""
        
        return """
⚠️  **Privacy Mode Active**

- All processing done locally when possible
- Sensitive data sanitized before external API calls
- Limited context window for local models
- Reduced reasoning capabilities
- No real-time web access for some operations

This mode protects sensitive data but may impact research quality.
        """
    
    def check_data_sensitivity(self, text: str) -> Dict[str, Any]:
        """Analyze text for potentially sensitive information"""
        import re
        
        sensitivity_indicators = {
            'emails': len(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)),
            'phone_numbers': len(re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text)),
            'ssn': len(re.findall(r'\b\d{3}-\d{2}-\d{4}\b', text)),
            'credit_cards': len(re.findall(r'\b\d{4}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b', text)),
            'personal_names': len(re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', text)),
            'addresses': len(re.findall(r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr)\b', text, re.IGNORECASE))
        }
        
        total_indicators = sum(sensitivity_indicators.values())
        
        return {
            'sensitivity_score': min(total_indicators / 10, 1.0),  # Normalized to 0-1
            'indicators': sensitivity_indicators,
            'is_sensitive': total_indicators > 0,
            'recommendation': 'Enable privacy mode' if total_indicators > 2 else 'Privacy mode optional'
        }
    
    def get_privacy_compliant_config(self) -> Dict[str, Any]:
        """Get configuration optimized for privacy"""
        return {
            'use_local_models': True,
            'minimize_data_sharing': True,
            'anonymize_outputs': True,
            'reduce_context_window': True,
            'disable_external_apis': True,
            'enable_data_encryption': True
        }