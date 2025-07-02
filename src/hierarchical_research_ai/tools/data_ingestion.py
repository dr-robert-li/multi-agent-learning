"""
Data Ingestion System

Handles ingestion of structured and unstructured data from various sources.
"""

import os
import asyncio
import aiohttp
import json
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import tempfile
import structlog

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import sqlite3
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False

logger = structlog.get_logger()


class DataIngestor:
    """Handles ingestion of structured and unstructured data"""
    
    SUPPORTED_DATA_FORMATS = {
        'csv': 'Comma-separated values',
        'excel': 'Excel spreadsheets (.xlsx, .xls)',
        'json': 'JSON data files',
        'jsonl': 'JSON Lines format',
        'parquet': 'Apache Parquet files',
        'sqlite': 'SQLite database files',
        'api': 'REST API endpoints',
        'web_scraping': 'Web page data extraction'
    }
    
    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = temp_dir or tempfile.mkdtemp()
        os.makedirs(self.temp_dir, exist_ok=True)
    
    async def ingest_data(self, 
                         source: str, 
                         data_type: str = 'auto',
                         options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Ingest data from various sources
        
        Args:
            source: Data source (file path, URL, database connection string)
            data_type: Type of data ('csv', 'excel', 'json', 'api', etc.)
            options: Additional options for data ingestion
            
        Returns:
            Dictionary containing processed data and metadata
        """
        logger.info("Starting data ingestion", source=source, data_type=data_type)
        
        options = options or {}
        
        try:
            # Auto-detect data type if needed
            if data_type == 'auto':
                data_type = self._detect_data_type(source)
            
            # Ingest based on data type
            if data_type == 'csv':
                data = await self._ingest_csv(source, options)
            elif data_type == 'excel':
                data = await self._ingest_excel(source, options)
            elif data_type == 'json':
                data = await self._ingest_json(source, options)
            elif data_type == 'jsonl':
                data = await self._ingest_jsonl(source, options)
            elif data_type == 'sqlite':
                data = await self._ingest_sqlite(source, options)
            elif data_type == 'api':
                data = await self._ingest_api(source, options)
            elif data_type == 'web_scraping':
                data = await self._ingest_web_scraping(source, options)
            else:
                raise ValueError(f"Unsupported data type: {data_type}")
            
            logger.info("Data ingestion completed", 
                       source=source, 
                       rows=data.get('row_count', 0))
            
            return data
            
        except Exception as e:
            logger.error("Data ingestion failed", source=source, error=str(e))
            raise
    
    async def ingest_multiple_datasets(self, 
                                     datasets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ingest multiple datasets concurrently
        
        Args:
            datasets: List of dataset configurations
                Each should have: {'source': str, 'data_type': str, 'options': dict}
                
        Returns:
            List of ingested datasets
        """
        tasks = []
        for dataset_config in datasets:
            source = dataset_config.get('source')
            data_type = dataset_config.get('data_type', 'auto')
            options = dataset_config.get('options', {})
            
            task = self.ingest_data(source, data_type, options)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log them
        successful_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("Failed to ingest dataset", 
                           dataset=datasets[i], 
                           error=str(result))
            else:
                successful_results.append(result)
        
        return successful_results
    
    def _detect_data_type(self, source: str) -> str:
        """Auto-detect data type from source"""
        if source.startswith(('http://', 'https://')):
            if any(ext in source.lower() for ext in ['.csv', '.json', '.xlsx']):
                # URL with file extension
                if '.csv' in source.lower():
                    return 'csv'
                elif '.json' in source.lower():
                    return 'json'
                elif '.xlsx' in source.lower() or '.xls' in source.lower():
                    return 'excel'
            else:
                # Assume API endpoint
                return 'api'
        else:
            # Local file
            path = Path(source)
            extension = path.suffix.lower()
            
            if extension == '.csv':
                return 'csv'
            elif extension in ['.xlsx', '.xls']:
                return 'excel'
            elif extension == '.json':
                return 'json'
            elif extension == '.jsonl':
                return 'jsonl'
            elif extension == '.db' or extension == '.sqlite':
                return 'sqlite'
            else:
                return 'csv'  # Default fallback
    
    async def _ingest_csv(self, source: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest CSV data"""
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required for CSV processing. Install with: pip install pandas")
        
        try:
            # Handle URL vs local file
            if source.startswith(('http://', 'https://')):
                df = pd.read_csv(source, **options)
            else:
                df = pd.read_csv(source, **options)
            
            # Generate data summary
            summary = self._generate_dataframe_summary(df, source)
            
            return {
                'data': df.to_dict('records'),
                'metadata': {
                    'source': source,
                    'data_type': 'csv',
                    'row_count': len(df),
                    'column_count': len(df.columns),
                    'columns': df.columns.tolist(),
                    'dtypes': df.dtypes.to_dict(),
                    'memory_usage': df.memory_usage(deep=True).sum(),
                    'ingestion_timestamp': asyncio.get_event_loop().time()
                },
                'summary': summary,
                'dataframe': df  # Keep original for further processing
            }
            
        except Exception as e:
            logger.error("CSV ingestion failed", source=source, error=str(e))
            raise
    
    async def _ingest_excel(self, source: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest Excel data"""
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required for Excel processing. Install with: pip install pandas openpyxl")
        
        try:
            # Read all sheets or specific sheet
            sheet_name = options.get('sheet_name', None)
            
            if sheet_name:
                df = pd.read_excel(source, sheet_name=sheet_name, **{k: v for k, v in options.items() if k != 'sheet_name'})
                sheets_data = {sheet_name: df}
            else:
                sheets_data = pd.read_excel(source, sheet_name=None, **options)
            
            # Combine all sheets or use single sheet
            if len(sheets_data) == 1:
                df = list(sheets_data.values())[0]
                sheet_info = f"Sheet: {list(sheets_data.keys())[0]}"
            else:
                # Combine all sheets
                df = pd.concat(sheets_data.values(), ignore_index=True)
                sheet_info = f"Combined {len(sheets_data)} sheets: {', '.join(sheets_data.keys())}"
            
            summary = self._generate_dataframe_summary(df, source)
            summary = f"{sheet_info}\n\n{summary}"
            
            return {
                'data': df.to_dict('records'),
                'metadata': {
                    'source': source,
                    'data_type': 'excel',
                    'row_count': len(df),
                    'column_count': len(df.columns),
                    'columns': df.columns.tolist(),
                    'sheets': list(sheets_data.keys()),
                    'dtypes': df.dtypes.to_dict(),
                    'ingestion_timestamp': asyncio.get_event_loop().time()
                },
                'summary': summary,
                'dataframe': df,
                'sheets_data': sheets_data
            }
            
        except Exception as e:
            logger.error("Excel ingestion failed", source=source, error=str(e))
            raise
    
    async def _ingest_json(self, source: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest JSON data"""
        try:
            # Handle URL vs local file
            if source.startswith(('http://', 'https://')):
                async with aiohttp.ClientSession() as session:
                    async with session.get(source) as response:
                        response.raise_for_status()
                        data = await response.json()
            else:
                with open(source, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            # Try to convert to DataFrame if possible
            df = None
            if isinstance(data, list) and data and isinstance(data[0], dict):
                try:
                    if PANDAS_AVAILABLE:
                        df = pd.DataFrame(data)
                except:
                    pass
            
            # Generate summary
            summary = self._generate_json_summary(data, source)
            if df is not None:
                summary += "\n\nDataFrame Summary:\n" + self._generate_dataframe_summary(df, source)
            
            metadata = {
                'source': source,
                'data_type': 'json',
                'ingestion_timestamp': asyncio.get_event_loop().time()
            }
            
            if df is not None:
                metadata.update({
                    'row_count': len(df),
                    'column_count': len(df.columns),
                    'columns': df.columns.tolist(),
                    'dtypes': df.dtypes.to_dict()
                })
            
            result = {
                'data': data,
                'metadata': metadata,
                'summary': summary
            }
            
            if df is not None:
                result['dataframe'] = df
            
            return result
            
        except Exception as e:
            logger.error("JSON ingestion failed", source=source, error=str(e))
            raise
    
    async def _ingest_jsonl(self, source: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest JSON Lines data"""
        try:
            data = []
            
            if source.startswith(('http://', 'https://')):
                async with aiohttp.ClientSession() as session:
                    async with session.get(source) as response:
                        response.raise_for_status()
                        text = await response.text()
                        lines = text.strip().split('\n')
            else:
                with open(source, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            
            for line in lines:
                if line.strip():
                    data.append(json.loads(line))
            
            # Convert to DataFrame if possible
            df = None
            if data and isinstance(data[0], dict):
                try:
                    if PANDAS_AVAILABLE:
                        df = pd.DataFrame(data)
                except:
                    pass
            
            summary = f"JSON Lines data with {len(data)} records"
            if df is not None:
                summary += "\n\nDataFrame Summary:\n" + self._generate_dataframe_summary(df, source)
            
            metadata = {
                'source': source,
                'data_type': 'jsonl',
                'record_count': len(data),
                'ingestion_timestamp': asyncio.get_event_loop().time()
            }
            
            if df is not None:
                metadata.update({
                    'row_count': len(df),
                    'column_count': len(df.columns),
                    'columns': df.columns.tolist(),
                    'dtypes': df.dtypes.to_dict()
                })
            
            result = {
                'data': data,
                'metadata': metadata,
                'summary': summary
            }
            
            if df is not None:
                result['dataframe'] = df
            
            return result
            
        except Exception as e:
            logger.error("JSON Lines ingestion failed", source=source, error=str(e))
            raise
    
    async def _ingest_sqlite(self, source: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest SQLite database data"""
        if not SQLITE_AVAILABLE:
            raise ImportError("sqlite3 is required for SQLite processing")
        
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required for SQLite processing. Install with: pip install pandas")
        
        try:
            conn = sqlite3.connect(source)
            
            # Get table names
            tables_query = "SELECT name FROM sqlite_master WHERE type='table';"
            tables = pd.read_sql_query(tables_query, conn)['name'].tolist()
            
            # Read specified table or all tables
            table_name = options.get('table_name')
            query = options.get('query')
            
            if query:
                df = pd.read_sql_query(query, conn)
                data_source = f"Custom query: {query[:100]}..."
            elif table_name:
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                data_source = f"Table: {table_name}"
            else:
                # Read first table or combine all
                if tables:
                    df = pd.read_sql_query(f"SELECT * FROM {tables[0]}", conn)
                    data_source = f"Table: {tables[0]} (first table)"
                else:
                    raise ValueError("No tables found in database")
            
            conn.close()
            
            summary = f"SQLite Database: {source}\n"
            summary += f"Available tables: {', '.join(tables)}\n"
            summary += f"Data source: {data_source}\n\n"
            summary += self._generate_dataframe_summary(df, source)
            
            return {
                'data': df.to_dict('records'),
                'metadata': {
                    'source': source,
                    'data_type': 'sqlite',
                    'tables': tables,
                    'data_source': data_source,
                    'row_count': len(df),
                    'column_count': len(df.columns),
                    'columns': df.columns.tolist(),
                    'dtypes': df.dtypes.to_dict(),
                    'ingestion_timestamp': asyncio.get_event_loop().time()
                },
                'summary': summary,
                'dataframe': df
            }
            
        except Exception as e:
            logger.error("SQLite ingestion failed", source=source, error=str(e))
            raise
    
    async def _ingest_api(self, source: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest data from API endpoint"""
        try:
            headers = options.get('headers', {})
            params = options.get('params', {})
            method = options.get('method', 'GET').upper()
            auth = options.get('auth')
            
            async with aiohttp.ClientSession() as session:
                if method == 'GET':
                    async with session.get(source, headers=headers, params=params, auth=auth) as response:
                        response.raise_for_status()
                        
                        content_type = response.headers.get('content-type', '').lower()
                        if 'json' in content_type:
                            data = await response.json()
                        else:
                            text = await response.text()
                            try:
                                data = json.loads(text)
                            except:
                                data = {'raw_text': text}
                
                elif method == 'POST':
                    post_data = options.get('data', {})
                    async with session.post(source, headers=headers, json=post_data, auth=auth) as response:
                        response.raise_for_status()
                        data = await response.json()
                
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Try to convert to DataFrame if possible
            df = None
            if isinstance(data, list) and data and isinstance(data[0], dict):
                try:
                    if PANDAS_AVAILABLE:
                        df = pd.DataFrame(data)
                except:
                    pass
            elif isinstance(data, dict):
                # Look for common API response patterns
                for key in ['data', 'results', 'items', 'records']:
                    if key in data and isinstance(data[key], list):
                        try:
                            if PANDAS_AVAILABLE:
                                df = pd.DataFrame(data[key])
                            break
                        except:
                            pass
            
            summary = f"API Response from: {source}\n"
            summary += f"Response type: {type(data).__name__}\n"
            
            if df is not None:
                summary += "\nDataFrame Summary:\n" + self._generate_dataframe_summary(df, source)
            else:
                summary += f"Data structure: {self._describe_data_structure(data)}"
            
            metadata = {
                'source': source,
                'data_type': 'api',
                'method': method,
                'ingestion_timestamp': asyncio.get_event_loop().time()
            }
            
            if df is not None:
                metadata.update({
                    'row_count': len(df),
                    'column_count': len(df.columns),
                    'columns': df.columns.tolist(),
                    'dtypes': df.dtypes.to_dict()
                })
            
            result = {
                'data': data,
                'metadata': metadata,
                'summary': summary
            }
            
            if df is not None:
                result['dataframe'] = df
            
            return result
            
        except Exception as e:
            logger.error("API ingestion failed", source=source, error=str(e))
            raise
    
    async def _ingest_web_scraping(self, source: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest data through web scraping"""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("beautifulsoup4 is required for web scraping. Install with: pip install beautifulsoup4")
        
        try:
            headers = options.get('headers', {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            async with aiohttp.ClientSession() as session:
                async with session.get(source, headers=headers) as response:
                    response.raise_for_status()
                    html = await response.text()
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract data based on options
            selectors = options.get('selectors', {})
            extract_tables = options.get('extract_tables', True)
            extract_text = options.get('extract_text', True)
            
            extracted_data = {}
            
            # Extract custom selectors
            for name, selector in selectors.items():
                elements = soup.select(selector)
                extracted_data[name] = [elem.get_text(strip=True) for elem in elements]
            
            # Extract tables
            if extract_tables and PANDAS_AVAILABLE:
                try:
                    tables = pd.read_html(html)
                    if tables:
                        extracted_data['tables'] = [table.to_dict('records') for table in tables]
                except:
                    pass
            
            # Extract general text
            if extract_text:
                # Remove scripts and styles
                for script in soup(["script", "style"]):
                    script.decompose()
                
                text = soup.get_text()
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                clean_text = '\n'.join(chunk for chunk in chunks if chunk)
                extracted_data['text_content'] = clean_text
            
            summary = f"Web scraping from: {source}\n"
            summary += f"Data extracted: {list(extracted_data.keys())}\n"
            
            if 'tables' in extracted_data:
                summary += f"Tables found: {len(extracted_data['tables'])}\n"
            
            return {
                'data': extracted_data,
                'metadata': {
                    'source': source,
                    'data_type': 'web_scraping',
                    'extracted_elements': list(extracted_data.keys()),
                    'ingestion_timestamp': asyncio.get_event_loop().time()
                },
                'summary': summary
            }
            
        except Exception as e:
            logger.error("Web scraping failed", source=source, error=str(e))
            raise
    
    def _generate_dataframe_summary(self, df, source: str) -> str:
        """Generate a summary of a pandas DataFrame"""
        if not PANDAS_AVAILABLE:
            return "DataFrame summary not available (pandas not installed)"
        
        summary_parts = [
            f"Data Summary for: {source}",
            f"Shape: {df.shape[0]} rows × {df.shape[1]} columns",
            "",
            "Column Information:",
        ]
        
        for col in df.columns:
            dtype = df[col].dtype
            null_count = df[col].isnull().sum()
            null_pct = (null_count / len(df)) * 100
            
            if pd.api.types.is_numeric_dtype(df[col]):
                stats = f"mean: {df[col].mean():.2f}, std: {df[col].std():.2f}"
            else:
                unique_count = df[col].nunique()
                stats = f"unique values: {unique_count}"
            
            summary_parts.append(f"  {col} ({dtype}): {null_count} nulls ({null_pct:.1f}%), {stats}")
        
        # Sample data
        summary_parts.extend([
            "",
            "Sample Data (first 5 rows):",
            df.head().to_string()
        ])
        
        return "\n".join(summary_parts)
    
    def _generate_json_summary(self, data: Any, source: str) -> str:
        """Generate a summary of JSON data"""
        summary_parts = [f"JSON Data Summary for: {source}"]
        
        if isinstance(data, dict):
            summary_parts.extend([
                f"Type: Dictionary with {len(data)} keys",
                f"Keys: {', '.join(list(data.keys())[:10])}{'...' if len(data) > 10 else ''}"
            ])
        elif isinstance(data, list):
            summary_parts.extend([
                f"Type: List with {len(data)} items",
                f"First item type: {type(data[0]).__name__ if data else 'N/A'}"
            ])
        else:
            summary_parts.append(f"Type: {type(data).__name__}")
        
        return "\n".join(summary_parts)
    
    def _describe_data_structure(self, data: Any, max_depth: int = 3, current_depth: int = 0) -> str:
        """Describe the structure of data"""
        if current_depth >= max_depth:
            return f"{type(data).__name__} (truncated)"
        
        if isinstance(data, dict):
            if not data:
                return "empty dict"
            key_types = {}
            for key, value in list(data.items())[:5]:
                value_desc = self._describe_data_structure(value, max_depth, current_depth + 1)
                key_types[key] = value_desc
            
            desc = "dict: {" + ", ".join([f"{k}: {v}" for k, v in key_types.items()])
            if len(data) > 5:
                desc += f", ... ({len(data) - 5} more)"
            desc += "}"
            return desc
        
        elif isinstance(data, list):
            if not data:
                return "empty list"
            
            item_desc = self._describe_data_structure(data[0], max_depth, current_depth + 1)
            return f"list[{len(data)}]: {item_desc}"
        
        else:
            return type(data).__name__
    
    def get_supported_formats(self) -> Dict[str, Any]:
        """Get information about supported data formats"""
        return {
            'formats': self.SUPPORTED_DATA_FORMATS,
            'requirements': {
                'csv': 'pandas',
                'excel': 'pandas + openpyxl',
                'json': 'built-in',
                'jsonl': 'built-in',
                'sqlite': 'sqlite3 + pandas',
                'api': 'aiohttp',
                'web_scraping': 'beautifulsoup4 + aiohttp'
            },
            'availability': {
                'pandas': PANDAS_AVAILABLE,
                'numpy': NUMPY_AVAILABLE,
                'sqlite3': SQLITE_AVAILABLE
            }
        }