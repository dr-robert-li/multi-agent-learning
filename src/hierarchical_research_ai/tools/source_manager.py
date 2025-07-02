"""
Source Manager

Manages user-provided documents and data sources, integrating them into the research workflow.
"""

import os
import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pathlib import Path
import structlog

from .document_ingestion import DocumentIngestor
from .data_ingestion import DataIngestor

logger = structlog.get_logger()


class SourceManager:
    """Manages all user-provided sources (documents and data)"""
    
    def __init__(self, workspace_dir: Optional[str] = None):
        self.workspace_dir = workspace_dir or "./workspace"
        self.sources_dir = os.path.join(self.workspace_dir, "sources")
        self.metadata_file = os.path.join(self.workspace_dir, "sources_metadata.json")
        
        # Create directories
        os.makedirs(self.sources_dir, exist_ok=True)
        os.makedirs(self.workspace_dir, exist_ok=True)
        
        # Initialize ingestors
        self.document_ingestor = DocumentIngestor(temp_dir=os.path.join(self.workspace_dir, "temp"))
        self.data_ingestor = DataIngestor(temp_dir=os.path.join(self.workspace_dir, "temp"))
        
        # Load existing metadata
        self.sources_metadata = self._load_metadata()
    
    async def add_source(self, 
                        source: str,
                        source_type: str = 'auto',
                        metadata: Optional[Dict[str, Any]] = None,
                        options: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a new source (document or data) to the research project
        
        Args:
            source: File path, URL, or data source identifier
            source_type: Type of source ('document', 'data', 'auto')
            metadata: User-provided metadata
            options: Ingestion options
            
        Returns:
            Source ID for referencing the source
        """
        logger.info("Adding new source", source=source, source_type=source_type)
        
        try:
            # Generate unique source ID
            source_id = self._generate_source_id(source)
            
            # Auto-detect source type if needed
            if source_type == 'auto':
                source_type = self._detect_source_type(source)
            
            # Ingest the source
            if source_type == 'document':
                ingested_data = await self.document_ingestor.ingest_document(source, metadata)
            elif source_type == 'data':
                ingested_data = await self.data_ingestor.ingest_data(source, options=options or {})
            else:
                raise ValueError(f"Unknown source type: {source_type}")
            
            # Add to metadata
            source_metadata = {
                'id': source_id,
                'original_source': source,
                'source_type': source_type,
                'added_timestamp': datetime.now().isoformat(),
                'user_metadata': metadata or {},
                'ingestion_options': options or {},
                'ingested_data': ingested_data
            }
            
            self.sources_metadata[source_id] = source_metadata
            self._save_metadata()
            
            logger.info("Source added successfully", source_id=source_id, source=source)
            return source_id
            
        except Exception as e:
            logger.error("Failed to add source", source=source, error=str(e))
            raise
    
    async def add_multiple_sources(self, 
                                  sources: List[Dict[str, Any]]) -> List[str]:
        """
        Add multiple sources concurrently
        
        Args:
            sources: List of source configurations
                Each should have: {'source': str, 'source_type': str, 'metadata': dict, 'options': dict}
                
        Returns:
            List of source IDs
        """
        tasks = []
        for source_config in sources:
            source = source_config.get('source')
            source_type = source_config.get('source_type', 'auto')
            metadata = source_config.get('metadata')
            options = source_config.get('options')
            
            task = self.add_source(source, source_type, metadata, options)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return successful source IDs
        source_ids = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("Failed to add source", 
                           source=sources[i], 
                           error=str(result))
            else:
                source_ids.append(result)
        
        return source_ids
    
    def get_source(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Get source metadata and data by ID"""
        return self.sources_metadata.get(source_id)
    
    def list_sources(self, source_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all sources or sources of a specific type
        
        Args:
            source_type: Filter by source type ('document', 'data', or None for all)
            
        Returns:
            List of source metadata
        """
        sources = list(self.sources_metadata.values())
        
        if source_type:
            sources = [s for s in sources if s.get('source_type') == source_type]
        
        return sources
    
    def remove_source(self, source_id: str) -> bool:
        """Remove a source from the project"""
        if source_id in self.sources_metadata:
            del self.sources_metadata[source_id]
            self._save_metadata()
            logger.info("Source removed", source_id=source_id)
            return True
        return False
    
    def get_sources_summary(self) -> Dict[str, Any]:
        """Get a summary of all sources"""
        documents = [s for s in self.sources_metadata.values() if s.get('source_type') == 'document']
        data_sources = [s for s in self.sources_metadata.values() if s.get('source_type') == 'data']
        
        summary = {
            'total_sources': len(self.sources_metadata),
            'documents': {
                'count': len(documents),
                'total_words': sum(s.get('ingested_data', {}).get('word_count', 0) for s in documents),
                'formats': list(set(s.get('ingested_data', {}).get('metadata', {}).get('file_type') for s in documents))
            },
            'data_sources': {
                'count': len(data_sources),
                'total_rows': sum(s.get('ingested_data', {}).get('metadata', {}).get('row_count', 0) for s in data_sources),
                'formats': list(set(s.get('ingested_data', {}).get('metadata', {}).get('data_type') for s in data_sources))
            },
            'recent_additions': sorted(
                [{'id': s['id'], 'source': s['original_source'], 'added': s['added_timestamp']} 
                 for s in self.sources_metadata.values()],
                key=lambda x: x['added'],
                reverse=True
            )[:5]
        }
        
        return summary
    
    def search_sources(self, query: str, source_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search sources by content or metadata
        
        Args:
            query: Search query
            source_type: Filter by source type
            
        Returns:
            List of matching sources with relevance scores
        """
        query_lower = query.lower()
        matching_sources = []
        
        for source_id, source_data in self.sources_metadata.items():
            if source_type and source_data.get('source_type') != source_type:
                continue
            
            relevance_score = 0
            
            # Search in original source path/URL
            if query_lower in source_data.get('original_source', '').lower():
                relevance_score += 10
            
            # Search in user metadata
            user_metadata = source_data.get('user_metadata', {})
            for key, value in user_metadata.items():
                if query_lower in str(value).lower():
                    relevance_score += 5
            
            # Search in content (for documents)
            ingested_data = source_data.get('ingested_data', {})
            content = ingested_data.get('content', '')
            if query_lower in content.lower():
                relevance_score += 3
            
            # Search in summary
            summary = ingested_data.get('summary', '')
            if query_lower in summary.lower():
                relevance_score += 2
            
            if relevance_score > 0:
                matching_sources.append({
                    'source_id': source_id,
                    'source_data': source_data,
                    'relevance_score': relevance_score
                })
        
        # Sort by relevance score
        matching_sources.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return matching_sources
    
    def get_content_for_research(self, source_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get formatted content from sources for research agents
        
        Args:
            source_ids: Specific source IDs to include (None for all)
            
        Returns:
            Formatted content for research use
        """
        if source_ids is None:
            sources_to_include = list(self.sources_metadata.values())
        else:
            sources_to_include = [self.sources_metadata[sid] for sid in source_ids if sid in self.sources_metadata]
        
        formatted_content = {
            'documents': [],
            'datasets': [],
            'summary': {
                'total_sources': len(sources_to_include),
                'total_words': 0,
                'total_data_rows': 0
            }
        }
        
        for source in sources_to_include:
            ingested_data = source.get('ingested_data', {})
            
            if source.get('source_type') == 'document':
                doc_content = {
                    'source_id': source['id'],
                    'original_source': source['original_source'],
                    'content': ingested_data.get('content', ''),
                    'word_count': ingested_data.get('word_count', 0),
                    'metadata': source.get('user_metadata', {}),
                    'file_type': ingested_data.get('metadata', {}).get('file_type'),
                    'summary': ingested_data.get('summary', '')
                }
                formatted_content['documents'].append(doc_content)
                formatted_content['summary']['total_words'] += doc_content['word_count']
            
            elif source.get('source_type') == 'data':
                data_content = {
                    'source_id': source['id'],
                    'original_source': source['original_source'],
                    'data': ingested_data.get('data', []),
                    'summary': ingested_data.get('summary', ''),
                    'metadata': {
                        **source.get('user_metadata', {}),
                        **ingested_data.get('metadata', {})
                    }
                }
                formatted_content['datasets'].append(data_content)
                
                row_count = ingested_data.get('metadata', {}).get('row_count', 0)
                formatted_content['summary']['total_data_rows'] += row_count
        
        return formatted_content
    
    def export_sources_manifest(self) -> Dict[str, Any]:
        """Export a manifest of all sources for backup/sharing"""
        return {
            'export_timestamp': datetime.now().isoformat(),
            'workspace_dir': self.workspace_dir,
            'sources_count': len(self.sources_metadata),
            'sources': {
                source_id: {
                    'original_source': data['original_source'],
                    'source_type': data['source_type'],
                    'added_timestamp': data['added_timestamp'],
                    'user_metadata': data['user_metadata'],
                    'content_summary': {
                        'word_count': data.get('ingested_data', {}).get('word_count'),
                        'row_count': data.get('ingested_data', {}).get('metadata', {}).get('row_count'),
                        'file_type': data.get('ingested_data', {}).get('metadata', {}).get('file_type'),
                        'data_type': data.get('ingested_data', {}).get('metadata', {}).get('data_type')
                    }
                }
                for source_id, data in self.sources_metadata.items()
            }
        }
    
    def _detect_source_type(self, source: str) -> str:
        """Auto-detect whether source is document or data"""
        # Check file extension
        if source.startswith(('http://', 'https://')):
            # URL - check for common patterns
            if any(ext in source.lower() for ext in ['.pdf', '.docx', '.doc', '.txt', '.md', '.html']):
                return 'document'
            elif any(ext in source.lower() for ext in ['.csv', '.json', '.xlsx', '.xls']):
                return 'data'
            else:
                # Default to data for APIs
                return 'data'
        else:
            # Local file - check extension
            path = Path(source)
            extension = path.suffix.lower()
            
            document_extensions = {'.pdf', '.docx', '.doc', '.txt', '.md', '.html', '.htm', '.xml'}
            data_extensions = {'.csv', '.json', '.jsonl', '.xlsx', '.xls', '.db', '.sqlite'}
            
            if extension in document_extensions:
                return 'document'
            elif extension in data_extensions:
                return 'data'
            else:
                # Default to document for unknown types
                return 'document'
    
    def _generate_source_id(self, source: str) -> str:
        """Generate a unique source ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        source_hash = str(abs(hash(source)))[:8]
        return f"src_{timestamp}_{source_hash}"
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load sources metadata from file"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("Failed to load metadata file", error=str(e))
        
        return {}
    
    def _save_metadata(self):
        """Save sources metadata to file"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.sources_metadata, f, indent=2, default=str)
        except Exception as e:
            logger.error("Failed to save metadata file", error=str(e))