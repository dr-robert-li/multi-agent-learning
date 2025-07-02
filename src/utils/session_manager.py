"""
Session Manager

Handles persistent session storage, resumption, and management for research projects.
"""

import os
import json
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
import structlog

logger = structlog.get_logger()


@dataclass
class ResearchSession:
    """Represents a research session with all its data"""
    session_id: str
    name: str
    topic: str
    created_at: str
    last_accessed: str
    status: str  # 'active', 'completed', 'paused', 'error'
    requirements: Dict[str, Any]
    conversation_history: List[Dict[str, Any]]
    agent_outputs: Dict[str, Any]
    source_ids: List[str]
    progress: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResearchSession':
        """Create from dictionary"""
        return cls(**data)
    
    def update_last_accessed(self):
        """Update the last accessed timestamp"""
        self.last_accessed = datetime.now().isoformat()
    
    def get_age_days(self) -> int:
        """Get session age in days"""
        created = datetime.fromisoformat(self.created_at)
        return (datetime.now() - created).days
    
    def get_last_accessed_days(self) -> int:
        """Get days since last access"""
        accessed = datetime.fromisoformat(self.last_accessed)
        return (datetime.now() - accessed).days


class SessionManager:
    """Manages research session persistence and lifecycle"""
    
    def __init__(self, sessions_dir: Optional[str] = None):
        self.sessions_dir = sessions_dir or os.path.join(os.getcwd(), ".hrai_sessions")
        self.sessions_index_file = os.path.join(self.sessions_dir, "sessions_index.json")
        
        # Create sessions directory
        os.makedirs(self.sessions_dir, exist_ok=True)
        
        # Load sessions index
        self.sessions_index = self._load_sessions_index()
    
    def create_session(self, 
                      name: str, 
                      topic: str, 
                      requirements: Dict[str, Any],
                      metadata: Optional[Dict[str, Any]] = None) -> ResearchSession:
        """
        Create a new research session
        
        Args:
            name: Human-readable session name
            topic: Research topic
            requirements: Research requirements and configuration
            metadata: Additional metadata
            
        Returns:
            Created ResearchSession object
        """
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        session = ResearchSession(
            session_id=session_id,
            name=name,
            topic=topic,
            created_at=now,
            last_accessed=now,
            status='active',
            requirements=requirements,
            conversation_history=[],
            agent_outputs={},
            source_ids=[],
            progress={
                'current_phase': 'initialization',
                'completion_percentage': 0,
                'phases_completed': [],
                'estimated_time_remaining': None
            },
            metadata=metadata or {}
        )
        
        # Save session
        self._save_session(session)
        
        # Update index
        self.sessions_index[session_id] = {
            'name': name,
            'topic': topic,
            'created_at': now,
            'last_accessed': now,
            'status': 'active'
        }
        self._save_sessions_index()
        
        logger.info("Created new session", session_id=session_id, name=name, topic=topic)
        return session
    
    def load_session(self, session_id: str) -> Optional[ResearchSession]:
        """
        Load a session by ID
        
        Args:
            session_id: Session identifier
            
        Returns:
            ResearchSession object or None if not found
        """
        if session_id not in self.sessions_index:
            return None
        
        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
        
        if not os.path.exists(session_file):
            logger.warning("Session file not found", session_id=session_id)
            # Clean up index
            del self.sessions_index[session_id]
            self._save_sessions_index()
            return None
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            session = ResearchSession.from_dict(session_data)
            session.update_last_accessed()
            
            # Update index
            self.sessions_index[session_id]['last_accessed'] = session.last_accessed
            self._save_sessions_index()
            
            logger.info("Loaded session", session_id=session_id)
            return session
            
        except Exception as e:
            logger.error("Failed to load session", session_id=session_id, error=str(e))
            return None
    
    def save_session(self, session: ResearchSession):
        """
        Save a session to persistent storage
        
        Args:
            session: ResearchSession to save
        """
        session.update_last_accessed()
        self._save_session(session)
        
        # Update index
        self.sessions_index[session.session_id] = {
            'name': session.name,
            'topic': session.topic,
            'created_at': session.created_at,
            'last_accessed': session.last_accessed,
            'status': session.status
        }
        self._save_sessions_index()
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session permanently
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if session_id not in self.sessions_index:
            return False
        
        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
        
        try:
            # Remove session file
            if os.path.exists(session_file):
                os.remove(session_file)
            
            # Remove from index
            del self.sessions_index[session_id]
            self._save_sessions_index()
            
            logger.info("Deleted session", session_id=session_id)
            return True
            
        except Exception as e:
            logger.error("Failed to delete session", session_id=session_id, error=str(e))
            return False
    
    def list_sessions(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all sessions with optional status filtering
        
        Args:
            status_filter: Filter by status ('active', 'completed', 'paused', 'error')
            
        Returns:
            List of session metadata
        """
        sessions = []
        
        for session_id, session_info in self.sessions_index.items():
            if status_filter and session_info.get('status') != status_filter:
                continue
            
            # Add computed fields
            session_data = session_info.copy()
            session_data['session_id'] = session_id
            
            # Calculate age
            if session_info.get('created_at'):
                created = datetime.fromisoformat(session_info['created_at'])
                session_data['age_days'] = (datetime.now() - created).days
            
            if session_info.get('last_accessed'):
                accessed = datetime.fromisoformat(session_info['last_accessed'])
                session_data['last_accessed_days'] = (datetime.now() - accessed).days
            
            sessions.append(session_data)
        
        # Sort by last accessed (most recent first)
        sessions.sort(key=lambda x: x.get('last_accessed', ''), reverse=True)
        
        return sessions
    
    def search_sessions(self, query: str) -> List[Dict[str, Any]]:
        """
        Search sessions by name, topic, or content
        
        Args:
            query: Search query
            
        Returns:
            List of matching sessions
        """
        query_lower = query.lower()
        matching_sessions = []
        
        for session_id, session_info in self.sessions_index.items():
            relevance_score = 0
            
            # Search in name
            if query_lower in session_info.get('name', '').lower():
                relevance_score += 10
            
            # Search in topic
            if query_lower in session_info.get('topic', '').lower():
                relevance_score += 8
            
            # Load full session for content search (expensive)
            if relevance_score == 0:
                session = self.load_session(session_id)
                if session:
                    # Search in conversation history
                    for message in session.conversation_history:
                        if query_lower in str(message.get('content', '')).lower():
                            relevance_score += 2
                            break
                    
                    # Search in requirements
                    if query_lower in str(session.requirements).lower():
                        relevance_score += 3
            
            if relevance_score > 0:
                session_data = session_info.copy()
                session_data['session_id'] = session_id
                session_data['relevance_score'] = relevance_score
                matching_sessions.append(session_data)
        
        # Sort by relevance
        matching_sessions.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return matching_sessions
    
    def cleanup_old_sessions(self, max_age_days: int = 30, max_inactive_days: int = 7) -> int:
        """
        Clean up old or inactive sessions
        
        Args:
            max_age_days: Maximum age in days before deletion
            max_inactive_days: Maximum days of inactivity before deletion
            
        Returns:
            Number of sessions deleted
        """
        deleted_count = 0
        sessions_to_delete = []
        
        for session_id, session_info in self.sessions_index.items():
            should_delete = False
            
            # Check age
            if session_info.get('created_at'):
                created = datetime.fromisoformat(session_info['created_at'])
                age_days = (datetime.now() - created).days
                if age_days > max_age_days:
                    should_delete = True
            
            # Check inactivity
            if session_info.get('last_accessed'):
                accessed = datetime.fromisoformat(session_info['last_accessed'])
                inactive_days = (datetime.now() - accessed).days
                if inactive_days > max_inactive_days:
                    should_delete = True
            
            if should_delete:
                sessions_to_delete.append(session_id)
        
        # Delete identified sessions
        for session_id in sessions_to_delete:
            if self.delete_session(session_id):
                deleted_count += 1
        
        if deleted_count > 0:
            logger.info("Cleaned up old sessions", count=deleted_count)
        
        return deleted_count
    
    def export_session(self, session_id: str, export_path: str) -> bool:
        """
        Export a session to a file
        
        Args:
            session_id: Session to export
            export_path: Path to save the export
            
        Returns:
            True if successful, False otherwise
        """
        session = self.load_session(session_id)
        if not session:
            return False
        
        try:
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'export_version': '1.0',
                'session': session.to_dict()
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info("Exported session", session_id=session_id, path=export_path)
            return True
            
        except Exception as e:
            logger.error("Failed to export session", session_id=session_id, error=str(e))
            return False
    
    def import_session(self, import_path: str) -> Optional[str]:
        """
        Import a session from a file
        
        Args:
            import_path: Path to the exported session file
            
        Returns:
            New session ID if successful, None otherwise
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            session_data = import_data['session']
            
            # Generate new session ID to avoid conflicts
            old_session_id = session_data['session_id']
            new_session_id = str(uuid.uuid4())
            session_data['session_id'] = new_session_id
            
            # Update timestamps
            now = datetime.now().isoformat()
            session_data['last_accessed'] = now
            session_data['metadata']['imported_at'] = now
            session_data['metadata']['original_session_id'] = old_session_id
            
            # Create session
            session = ResearchSession.from_dict(session_data)
            self._save_session(session)
            
            # Update index
            self.sessions_index[new_session_id] = {
                'name': session.name + ' (Imported)',
                'topic': session.topic,
                'created_at': session.created_at,
                'last_accessed': now,
                'status': session.status
            }
            self._save_sessions_index()
            
            logger.info("Imported session", new_session_id=new_session_id, original_id=old_session_id)
            return new_session_id
            
        except Exception as e:
            logger.error("Failed to import session", error=str(e))
            return None
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about all sessions"""
        sessions = self.list_sessions()
        
        if not sessions:
            return {
                'total_sessions': 0,
                'active_sessions': 0,
                'completed_sessions': 0,
                'average_age_days': 0,
                'oldest_session_days': 0,
                'most_recent_access_days': 0
            }
        
        stats = {
            'total_sessions': len(sessions),
            'active_sessions': len([s for s in sessions if s.get('status') == 'active']),
            'completed_sessions': len([s for s in sessions if s.get('status') == 'completed']),
            'paused_sessions': len([s for s in sessions if s.get('status') == 'paused']),
            'error_sessions': len([s for s in sessions if s.get('status') == 'error'])
        }
        
        ages = [s.get('age_days', 0) for s in sessions if s.get('age_days') is not None]
        if ages:
            stats['average_age_days'] = sum(ages) / len(ages)
            stats['oldest_session_days'] = max(ages)
        
        access_days = [s.get('last_accessed_days', 0) for s in sessions if s.get('last_accessed_days') is not None]
        if access_days:
            stats['most_recent_access_days'] = min(access_days)
        
        return stats
    
    def _save_session(self, session: ResearchSession):
        """Save session data to file"""
        session_file = os.path.join(self.sessions_dir, f"{session.session_id}.json")
        
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session.to_dict(), f, indent=2, default=str)
        except Exception as e:
            logger.error("Failed to save session file", session_id=session.session_id, error=str(e))
            raise
    
    def _load_sessions_index(self) -> Dict[str, Any]:
        """Load the sessions index file"""
        if os.path.exists(self.sessions_index_file):
            try:
                with open(self.sessions_index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("Failed to load sessions index", error=str(e))
        
        return {}
    
    def _save_sessions_index(self):
        """Save the sessions index file"""
        try:
            with open(self.sessions_index_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions_index, f, indent=2, default=str)
        except Exception as e:
            logger.error("Failed to save sessions index", error=str(e))