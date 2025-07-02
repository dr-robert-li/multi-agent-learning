"""
Research Tools Integration

Provides integrated tools for research agents to access user sources and external data.
"""

from typing import Dict, Any, List, Optional, Union
import asyncio
from .source_manager import SourceManager
from .document_ingestion import DocumentIngestor
from .data_ingestion import DataIngestor


class ResearchToolkit:
    """Integrated toolkit for research agents"""
    
    def __init__(self, workspace_dir: Optional[str] = None):
        self.source_manager = SourceManager(workspace_dir)
        self.document_ingestor = DocumentIngestor()
        self.data_ingestor = DataIngestor()
    
    # Source Management API
    async def add_source(self, 
                        source: str,
                        source_type: str = 'auto',
                        metadata: Optional[Dict[str, Any]] = None,
                        options: Optional[Dict[str, Any]] = None) -> str:
        """Add a source to the research project"""
        return await self.source_manager.add_source(source, source_type, metadata, options)
    
    async def add_multiple_sources(self, sources: List[Dict[str, Any]]) -> List[str]:
        """Add multiple sources concurrently"""
        return await self.source_manager.add_multiple_sources(sources)
    
    def get_source(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Get source by ID"""
        return self.source_manager.get_source(source_id)
    
    def list_sources(self, source_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all sources or filter by type"""
        return self.source_manager.list_sources(source_type)
    
    def search_sources(self, query: str, source_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search sources by content or metadata"""
        return self.source_manager.search_sources(query, source_type)
    
    def remove_source(self, source_id: str) -> bool:
        """Remove a source"""
        return self.source_manager.remove_source(source_id)
    
    # Content Access for Research
    def get_all_user_content(self) -> Dict[str, Any]:
        """Get all user-provided content formatted for research"""
        return self.source_manager.get_content_for_research()
    
    def get_user_content_by_ids(self, source_ids: List[str]) -> Dict[str, Any]:
        """Get specific user content by source IDs"""
        return self.source_manager.get_content_for_research(source_ids)
    
    def get_documents_content(self) -> List[Dict[str, Any]]:
        """Get all user documents content"""
        content = self.get_all_user_content()
        return content.get('documents', [])
    
    def get_datasets_content(self) -> List[Dict[str, Any]]:
        """Get all user datasets content"""
        content = self.get_all_user_content()
        return content.get('datasets', [])
    
    # Direct Ingestion API
    async def ingest_document_direct(self, source: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Directly ingest a document without storing in source manager"""
        return await self.document_ingestor.ingest_document(source, metadata)
    
    async def ingest_data_direct(self, source: str, data_type: str = 'auto', options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Directly ingest data without storing in source manager"""
        return await self.data_ingestor.ingest_data(source, data_type, options)
    
    # Utility Methods
    def get_sources_summary(self) -> Dict[str, Any]:
        """Get summary of all sources"""
        return self.source_manager.get_sources_summary()
    
    def export_sources_manifest(self) -> Dict[str, Any]:
        """Export manifest of all sources"""
        return self.source_manager.export_sources_manifest()
    
    def get_supported_formats(self) -> Dict[str, Any]:
        """Get information about supported formats"""
        return {
            'documents': self.document_ingestor.get_supported_formats(),
            'data': self.data_ingestor.get_supported_formats()
        }
    
    # Integration with Research Agents
    def prepare_context_for_agent(self, 
                                 agent_name: str, 
                                 source_types: Optional[List[str]] = None,
                                 keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Prepare user content context for a specific research agent
        
        Args:
            agent_name: Name of the agent requesting context
            source_types: Filter by source types ('document', 'data')
            keywords: Filter sources by keywords in metadata or content
            
        Returns:
            Formatted context for the agent
        """
        # Get all user content
        all_content = self.get_all_user_content()
        
        # Filter by source types
        if source_types:
            if 'document' not in source_types:
                all_content['documents'] = []
            if 'data' not in source_types:
                all_content['datasets'] = []
        
        # Filter by keywords
        if keywords:
            filtered_docs = []
            for doc in all_content['documents']:
                doc_text = f"{doc['content']} {doc.get('summary', '')} {str(doc.get('metadata', {}))}"
                if any(keyword.lower() in doc_text.lower() for keyword in keywords):
                    filtered_docs.append(doc)
            all_content['documents'] = filtered_docs
            
            filtered_data = []
            for dataset in all_content['datasets']:
                data_text = f"{dataset.get('summary', '')} {str(dataset.get('metadata', {}))}"
                if any(keyword.lower() in data_text.lower() for keyword in keywords):
                    filtered_data.append(dataset)
            all_content['datasets'] = filtered_data
        
        # Prepare agent-specific context
        context = {
            'agent_name': agent_name,
            'user_content': all_content,
            'content_summary': {
                'total_documents': len(all_content['documents']),
                'total_datasets': len(all_content['datasets']),
                'total_words': sum(doc['word_count'] for doc in all_content['documents']),
                'total_data_rows': sum(
                    dataset.get('metadata', {}).get('row_count', 0) 
                    for dataset in all_content['datasets']
                )
            },
            'instructions': self._get_agent_instructions(agent_name, all_content)
        }
        
        return context
    
    def _get_agent_instructions(self, agent_name: str, content: Dict[str, Any]) -> str:
        """Get agent-specific instructions for handling user content"""
        instructions = f"""
User Content Available for {agent_name}:

Documents: {len(content['documents'])} files
- Total content: {sum(doc['word_count'] for doc in content['documents']):,} words
- Types: {', '.join(set(doc.get('metadata', {}).get('file_type', 'unknown') for doc in content['documents']))}

Datasets: {len(content['datasets'])} sources
- Total rows: {sum(dataset.get('metadata', {}).get('row_count', 0) for dataset in content['datasets']):,}
- Types: {', '.join(set(dataset.get('metadata', {}).get('data_type', 'unknown') for dataset in content['datasets']))}

Instructions:
1. Prioritize user-provided content in your analysis
2. Cross-reference findings with user documents and data
3. Cite user sources appropriately in your output
4. Consider user data as primary evidence where applicable
5. Integrate user content with external research seamlessly
"""
        
        # Agent-specific instructions
        if 'literature' in agent_name.lower():
            instructions += "\n6. Treat user documents as key sources in your literature review"
            instructions += "\n7. Compare user documents with external literature"
        
        elif 'analysis' in agent_name.lower():
            instructions += "\n6. Use user datasets as primary data for analysis"
            instructions += "\n7. Validate findings against user-provided evidence"
        
        elif 'domain' in agent_name.lower():
            instructions += "\n6. Use user content to understand specific domain context"
            instructions += "\n7. Identify gaps between user knowledge and broader domain"
        
        return instructions


# Convenience functions for direct use
async def add_document(source: str, description: str = "", tags: List[str] = None) -> str:
    """Convenience function to add a document"""
    toolkit = ResearchToolkit()
    metadata = {}
    if description:
        metadata['description'] = description
    if tags:
        metadata['tags'] = tags
    
    return await toolkit.add_source(source, 'document', metadata)


async def add_dataset(source: str, description: str = "", tags: List[str] = None, options: Dict[str, Any] = None) -> str:
    """Convenience function to add a dataset"""
    toolkit = ResearchToolkit()
    metadata = {}
    if description:
        metadata['description'] = description
    if tags:
        metadata['tags'] = tags
    
    return await toolkit.add_source(source, 'data', metadata, options)


async def add_sources_from_list(sources: List[Union[str, Dict[str, Any]]]) -> List[str]:
    """Convenience function to add multiple sources from a list"""
    toolkit = ResearchToolkit()
    
    # Normalize sources to dict format
    normalized_sources = []
    for source in sources:
        if isinstance(source, str):
            normalized_sources.append({'source': source})
        else:
            normalized_sources.append(source)
    
    return await toolkit.add_multiple_sources(normalized_sources)


def get_all_user_sources() -> Dict[str, Any]:
    """Convenience function to get all user sources"""
    toolkit = ResearchToolkit()
    return toolkit.get_all_user_content()


def search_user_sources(query: str) -> List[Dict[str, Any]]:
    """Convenience function to search user sources"""
    toolkit = ResearchToolkit()
    return toolkit.search_sources(query)