"""
Document Ingestion System

Handles ingestion of various document types from local files and URLs.
"""

import os
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from urllib.parse import urlparse
import mimetypes
import tempfile
import structlog

# Document processing imports
try:
    import pypdf
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    PYTHON_DOCX_AVAILABLE = True
except ImportError:
    PYTHON_DOCX_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

logger = structlog.get_logger()


class DocumentIngestor:
    """Handles ingestion of documents from various sources"""
    
    SUPPORTED_EXTENSIONS = {
        '.pdf': 'pdf',
        '.docx': 'docx',
        '.doc': 'doc',
        '.txt': 'text',
        '.md': 'markdown',
        '.csv': 'csv',
        '.xlsx': 'excel',
        '.json': 'json',
        '.html': 'html',
        '.htm': 'html',
        '.xml': 'xml'
    }
    
    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = temp_dir or tempfile.mkdtemp()
        os.makedirs(self.temp_dir, exist_ok=True)
        
    async def ingest_document(self, source: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Ingest a document from local file or URL
        
        Args:
            source: Local file path or URL
            metadata: Additional metadata to associate with the document
            
        Returns:
            Dictionary containing extracted content and metadata
        """
        logger.info("Starting document ingestion", source=source)
        
        try:
            # Determine if source is URL or local file
            if self._is_url(source):
                document_data = await self._ingest_from_url(source)
            else:
                document_data = await self._ingest_from_file(source)
            
            # Add user-provided metadata
            if metadata:
                document_data['metadata'].update(metadata)
            
            logger.info("Document ingestion completed", 
                       source=source, 
                       word_count=len(document_data['content'].split()))
            
            return document_data
            
        except Exception as e:
            logger.error("Document ingestion failed", source=source, error=str(e))
            raise
    
    async def ingest_multiple_documents(self, sources: List[Union[str, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Ingest multiple documents concurrently
        
        Args:
            sources: List of sources (strings or dicts with 'source' and 'metadata' keys)
            
        Returns:
            List of ingested document data
        """
        tasks = []
        for source_info in sources:
            if isinstance(source_info, str):
                source = source_info
                metadata = None
            else:
                source = source_info.get('source')
                metadata = source_info.get('metadata')
            
            task = self.ingest_document(source, metadata)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log them
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("Failed to ingest document", 
                           source=sources[i], 
                           error=str(result))
            else:
                successful_results.append(result)
        
        return successful_results
    
    def _is_url(self, source: str) -> bool:
        """Check if source is a URL"""
        try:
            result = urlparse(source)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    async def _ingest_from_url(self, url: str) -> Dict[str, Any]:
        """Ingest document from URL"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                
                # Get content type
                content_type = response.headers.get('content-type', '').lower()
                
                # Save to temporary file
                content = await response.read()
                temp_file = os.path.join(self.temp_dir, f"temp_{hash(url)}")
                
                # Determine extension from content type or URL
                extension = self._get_extension_from_content_type(content_type)
                if not extension:
                    extension = Path(urlparse(url).path).suffix
                
                temp_file += extension
                
                with open(temp_file, 'wb') as f:
                    f.write(content)
                
                # Process the temporary file
                document_data = await self._process_file(temp_file, url)
                
                # Clean up
                try:
                    os.unlink(temp_file)
                except:
                    pass
                
                return document_data
    
    async def _ingest_from_file(self, file_path: str) -> Dict[str, Any]:
        """Ingest document from local file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        return await self._process_file(file_path, file_path)
    
    async def _process_file(self, file_path: str, original_source: str) -> Dict[str, Any]:
        """Process a file and extract content"""
        file_extension = Path(file_path).suffix.lower()
        file_type = self.SUPPORTED_EXTENSIONS.get(file_extension, 'unknown')
        
        # Basic metadata
        file_stat = os.stat(file_path)
        metadata = {
            'source': original_source,
            'file_type': file_type,
            'file_extension': file_extension,
            'file_size': file_stat.st_size,
            'modified_time': file_stat.st_mtime,
            'ingestion_timestamp': asyncio.get_event_loop().time()
        }
        
        # Extract content based on file type
        if file_type == 'pdf':
            content = await self._extract_pdf_content(file_path)
        elif file_type == 'docx':
            content = await self._extract_docx_content(file_path)
        elif file_type in ['text', 'markdown']:
            content = await self._extract_text_content(file_path)
        elif file_type == 'csv':
            content = await self._extract_csv_content(file_path)
        elif file_type == 'excel':
            content = await self._extract_excel_content(file_path)
        elif file_type == 'json':
            content = await self._extract_json_content(file_path)
        elif file_type == 'html':
            content = await self._extract_html_content(file_path)
        elif file_type == 'xml':
            content = await self._extract_xml_content(file_path)
        else:
            # Fallback to text extraction
            content = await self._extract_text_content(file_path)
        
        return {
            'content': content,
            'metadata': metadata,
            'word_count': len(content.split()),
            'char_count': len(content)
        }
    
    def _get_extension_from_content_type(self, content_type: str) -> str:
        """Get file extension from content type"""
        content_type_map = {
            'application/pdf': '.pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/msword': '.doc',
            'text/plain': '.txt',
            'text/markdown': '.md',
            'text/csv': '.csv',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'application/json': '.json',
            'text/html': '.html',
            'application/xml': '.xml',
            'text/xml': '.xml'
        }
        
        for ct, ext in content_type_map.items():
            if ct in content_type:
                return ext
        
        return ''
    
    async def _extract_pdf_content(self, file_path: str) -> str:
        """Extract text content from PDF"""
        if not PYPDF_AVAILABLE:
            raise ImportError("pypdf is required for PDF processing. Install with: pip install pypdf")
        
        try:
            reader = PdfReader(file_path)
            text_content = []
            
            for page in reader.pages:
                text_content.append(page.extract_text())
            
            return '\n\n'.join(text_content)
        except Exception as e:
            logger.warning("PDF extraction failed, trying alternative method", error=str(e))
            # Fallback to reading as text (might not work well)
            return await self._extract_text_content(file_path)
    
    async def _extract_docx_content(self, file_path: str) -> str:
        """Extract text content from DOCX"""
        if not PYTHON_DOCX_AVAILABLE:
            raise ImportError("python-docx is required for DOCX processing. Install with: pip install python-docx")
        
        try:
            doc = DocxDocument(file_path)
            paragraphs = [paragraph.text for paragraph in doc.paragraphs]
            return '\n\n'.join(paragraphs)
        except Exception as e:
            logger.warning("DOCX extraction failed", error=str(e))
            return await self._extract_text_content(file_path)
    
    async def _extract_text_content(self, file_path: str) -> str:
        """Extract content from plain text files"""
        encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        
        # If all encodings fail, read as binary and decode with errors='ignore'
        with open(file_path, 'rb') as f:
            return f.read().decode('utf-8', errors='ignore')
    
    async def _extract_csv_content(self, file_path: str) -> str:
        """Extract content from CSV files"""
        if not PANDAS_AVAILABLE:
            # Fallback to basic CSV reading
            return await self._extract_text_content(file_path)
        
        try:
            df = pd.read_csv(file_path)
            
            # Create a summary of the CSV
            summary = [
                f"CSV Data Summary:",
                f"Rows: {len(df)}",
                f"Columns: {len(df.columns)}",
                f"Column names: {', '.join(df.columns.tolist())}",
                "",
                "Sample data:",
                df.head(10).to_string(),
                "",
                "Data types:",
                df.dtypes.to_string()
            ]
            
            return '\n'.join(summary)
        except Exception as e:
            logger.warning("CSV processing failed", error=str(e))
            return await self._extract_text_content(file_path)
    
    async def _extract_excel_content(self, file_path: str) -> str:
        """Extract content from Excel files"""
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required for Excel processing. Install with: pip install pandas openpyxl")
        
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(file_path)
            content_parts = []
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                sheet_summary = [
                    f"Sheet: {sheet_name}",
                    f"Rows: {len(df)}",
                    f"Columns: {len(df.columns)}",
                    f"Column names: {', '.join(df.columns.tolist())}",
                    "",
                    "Sample data:",
                    df.head(5).to_string(),
                    ""
                ]
                
                content_parts.append('\n'.join(sheet_summary))
            
            return '\n\n'.join(content_parts)
        except Exception as e:
            logger.warning("Excel processing failed", error=str(e))
            return await self._extract_text_content(file_path)
    
    async def _extract_json_content(self, file_path: str) -> str:
        """Extract content from JSON files"""
        import json
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Create a readable summary of JSON structure
            def summarize_json(obj, level=0, max_level=3):
                indent = "  " * level
                if level > max_level:
                    return f"{indent}... (truncated)"
                
                if isinstance(obj, dict):
                    if not obj:
                        return f"{indent}{{}}"
                    
                    lines = [f"{indent}{{"]
                    for key, value in list(obj.items())[:10]:  # Limit keys
                        value_summary = summarize_json(value, level + 1, max_level)
                        lines.append(f"{indent}  {key}: {value_summary.strip()}")
                    
                    if len(obj) > 10:
                        lines.append(f"{indent}  ... ({len(obj) - 10} more keys)")
                    
                    lines.append(f"{indent}}}")
                    return '\n'.join(lines)
                
                elif isinstance(obj, list):
                    if not obj:
                        return f"{indent}[]"
                    
                    lines = [f"{indent}["]
                    for i, item in enumerate(obj[:5]):  # Limit items
                        item_summary = summarize_json(item, level + 1, max_level)
                        lines.append(f"{indent}  {item_summary.strip()}")
                    
                    if len(obj) > 5:
                        lines.append(f"{indent}  ... ({len(obj) - 5} more items)")
                    
                    lines.append(f"{indent}]")
                    return '\n'.join(lines)
                
                else:
                    return f"{indent}{repr(obj)}"
            
            summary = summarize_json(data)
            return f"JSON Structure:\n{summary}"
            
        except Exception as e:
            logger.warning("JSON processing failed", error=str(e))
            return await self._extract_text_content(file_path)
    
    async def _extract_html_content(self, file_path: str) -> str:
        """Extract text content from HTML files"""
        if not BS4_AVAILABLE:
            # Fallback to raw HTML
            return await self._extract_text_content(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            logger.warning("HTML processing failed", error=str(e))
            return await self._extract_text_content(file_path)
    
    async def _extract_xml_content(self, file_path: str) -> str:
        """Extract content from XML files"""
        if not BS4_AVAILABLE:
            return await self._extract_text_content(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            soup = BeautifulSoup(xml_content, 'xml')
            
            # Get text content
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            text = '\n'.join(line for line in lines if line)
            
            return text
            
        except Exception as e:
            logger.warning("XML processing failed", error=str(e))
            return await self._extract_text_content(file_path)
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """Get list of supported file formats"""
        format_categories = {
            'documents': ['.pdf', '.docx', '.doc', '.txt', '.md', '.html', '.htm', '.xml'],
            'data': ['.csv', '.xlsx', '.json'],
            'web': ['.html', '.htm', '.xml']
        }
        
        availability = {
            'documents': {
                'pdf': PYPDF_AVAILABLE,
                'docx': PYTHON_DOCX_AVAILABLE,
                'html': BS4_AVAILABLE,
                'basic_text': True
            },
            'data': {
                'csv': PANDAS_AVAILABLE,
                'excel': PANDAS_AVAILABLE,
                'json': True
            }
        }
        
        return {
            'supported_extensions': self.SUPPORTED_EXTENSIONS,
            'format_categories': format_categories,
            'library_availability': availability
        }