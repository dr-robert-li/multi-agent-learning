# HierarchicalResearchAI Examples

This document provides comprehensive examples of how to use HierarchicalResearchAI with your own documents and data sources.

## Table of Contents

1. [CLI Examples](#cli-examples)
2. [Python API Examples](#python-api-examples)
3. [Supported File Formats](#supported-file-formats)
4. [Integration with Research Workflow](#integration-with-research-workflow)

## CLI Examples

### Basic Source Management

```bash
# Add a PDF document
research-ai add-source --source "./research/paper.pdf" --description "Key research paper on AI ethics"

# Add a CSV dataset
research-ai add-source --source "./data/survey_results.csv" --type data --description "User survey data"

# Add a document from URL
research-ai add-source --source "https://example.com/report.pdf" --tags "report,analysis"

# List all sources
research-ai list-sources

# List only documents
research-ai list-sources --type document

# Search sources
research-ai search-sources "artificial intelligence"

# Show sources summary
research-ai sources-summary

# Remove a source
research-ai remove-source src_20240101_abc123
```

### Interactive Research with Sources

```bash
# Start interactive research (will prompt for sources)
research-ai research --topic "AI in Healthcare"

# Start research in batch mode
research-ai research --topic "Machine Learning Ethics" --interactive=false
```

## Python API Examples

### Basic Source Management

```python
import asyncio
from hierarchical_research_ai.tools import ResearchToolkit

async def main():
    # Initialize the toolkit
    toolkit = ResearchToolkit()
    
    # Add a document
    doc_id = await toolkit.add_source(
        source="./research/paper.pdf",
        source_type="document",
        metadata={
            "description": "Seminal paper on transformer architecture",
            "tags": ["machine-learning", "nlp", "transformers"],
            "author": "Vaswani et al.",
            "year": 2017
        }
    )
    print(f"Added document: {doc_id}")
    
    # Add a dataset
    data_id = await toolkit.add_source(
        source="./data/experiments.csv",
        source_type="data",
        metadata={
            "description": "Experimental results from ML model training",
            "tags": ["experiments", "results", "performance"]
        },
        options={
            "sep": ",",  # CSV separator
            "header": 0  # Header row
        }
    )
    print(f"Added dataset: {data_id}")
    
    # Get all user content
    content = toolkit.get_all_user_content()
    print(f"Documents: {len(content['documents'])}")
    print(f"Datasets: {len(content['datasets'])}")

asyncio.run(main())
```

### Multiple Sources at Once

```python
import asyncio
from hierarchical_research_ai.tools import add_sources_from_list

async def add_research_library():
    sources = [
        {
            "source": "./papers/attention_is_all_you_need.pdf",
            "source_type": "document",
            "metadata": {
                "description": "Original transformer paper",
                "tags": ["nlp", "attention", "transformers"]
            }
        },
        {
            "source": "./papers/bert_paper.pdf", 
            "source_type": "document",
            "metadata": {
                "description": "BERT: Pre-training of Deep Bidirectional Transformers",
                "tags": ["nlp", "bert", "pretraining"]
            }
        },
        {
            "source": "./data/model_benchmarks.json",
            "source_type": "data",
            "metadata": {
                "description": "Benchmark results for various models",
                "tags": ["benchmarks", "evaluation"]
            }
        },
        {
            "source": "https://api.github.com/repos/huggingface/transformers/issues",
            "source_type": "data",
            "metadata": {
                "description": "GitHub issues from transformers library",
                "tags": ["issues", "community"]
            },
            "options": {
                "method": "GET",
                "headers": {"Accept": "application/json"}
            }
        }
    ]
    
    source_ids = await add_sources_from_list(sources)
    print(f"Added {len(source_ids)} sources: {source_ids}")

asyncio.run(add_research_library())
```

### Full Research Workflow with Sources

```python
import asyncio
from hierarchical_research_ai import HierarchicalResearchSystem
from hierarchical_research_ai.tools import add_document, add_dataset

async def research_with_sources():
    # Add your sources first
    doc_id = await add_document(
        source="./research/my_analysis.pdf",
        description="My preliminary analysis of the topic",
        tags=["preliminary", "analysis"]
    )
    
    data_id = await add_dataset(
        source="./data/survey_data.csv",
        description="Survey responses from 1000 participants",
        tags=["survey", "primary-data"]
    )
    
    # Initialize research system
    research_system = HierarchicalResearchSystem(
        cli_mode=False,  # Programmatic mode
        privacy_mode=False
    )
    
    # Start research project
    project = research_system.start_project(
        topic="Impact of Social Media on Mental Health",
        target_length=25000,
        citation_style="APA",
        quality_level="academic_thesis",
        # Sources will be automatically detected and included
    )
    
    # Generate report
    report = await research_system.generate_report(project.id)
    
    print(f"Research completed: {report['output_path']}")
    print(f"Used {report['source_count']} sources including your documents")

asyncio.run(research_with_sources())
```

## Supported File Formats

### Documents

| Format | Extension | Description | Requirements |
|--------|-----------|-------------|--------------|
| PDF | `.pdf` | Portable Document Format | `pypdf` |
| Word | `.docx`, `.doc` | Microsoft Word documents | `python-docx` |
| Text | `.txt` | Plain text files | Built-in |
| Markdown | `.md` | Markdown formatted text | Built-in |
| HTML | `.html`, `.htm` | Web pages | `beautifulsoup4` |
| XML | `.xml` | XML documents | `beautifulsoup4` |

### Data Sources

| Format | Extension | Description | Requirements |
|--------|-----------|-------------|--------------|
| CSV | `.csv` | Comma-separated values | `pandas` |
| Excel | `.xlsx`, `.xls` | Microsoft Excel spreadsheets | `pandas` + `openpyxl` |
| JSON | `.json` | JavaScript Object Notation | Built-in |
| JSON Lines | `.jsonl` | Newline-delimited JSON | Built-in |
| SQLite | `.db`, `.sqlite` | SQLite database files | `sqlite3` + `pandas` |
| APIs | URLs | REST API endpoints | `aiohttp` |
| Web Scraping | URLs | Extract data from web pages | `beautifulsoup4` |

### URL Sources

```python
# Web-based documents
await add_document("https://arxiv.org/pdf/1706.03762.pdf")  # ArXiv paper
await add_document("https://example.com/research-report.pdf")

# Online datasets
await add_dataset("https://raw.githubusercontent.com/user/repo/data.csv")
await add_dataset("https://api.github.com/repos/user/repo/issues")

# Web scraping
await add_dataset(
    "https://en.wikipedia.org/wiki/Artificial_intelligence",
    options={
        "extract_tables": True,
        "selectors": {
            "headings": "h2, h3",
            "paragraphs": "p"
        }
    }
)
```

## Integration with Research Workflow

### Agent Context Integration

The research agents automatically receive context about your sources:

```python
# Example of how agents receive user content
from hierarchical_research_ai.tools import ResearchToolkit

toolkit = ResearchToolkit()

# Get context for literature review agent
context = toolkit.prepare_context_for_agent(
    agent_name="LiteratureSurveyAgent",
    source_types=["document"],  # Only documents
    keywords=["machine learning", "neural networks"]
)

# Context includes:
# - Filtered user documents
# - Content summaries
# - Agent-specific instructions
# - Integration guidelines
```

### Source Priority in Research

1. **User sources are prioritized** in all research phases
2. **Cross-referencing** between user content and external sources
3. **Proper attribution** in generated reports
4. **Data validation** using user datasets as primary evidence

### Example Research Output

When you provide sources, the research system:

```
Literature Review Section:
Based on your provided document "AI Ethics Framework (2023)", 
the current landscape shows... This aligns with recent findings 
from Smith et al. (2024) and contradicts earlier assumptions in...

Data Analysis Section:
Analysis of your survey data (n=1,000) reveals that 78% of 
respondents expressed concern about AI bias, which significantly 
exceeds the 45% reported in the broader literature...

Methodology Section:
Following the approach outlined in your preliminary analysis 
document, this research employs a mixed-methods design...
```

### Advanced Usage Examples

#### Custom Data Processing

```python
# Advanced CSV processing
data_id = await add_dataset(
    source="./complex_data.csv",
    options={
        "sep": ";",           # Semicolon separated
        "encoding": "utf-8",  # Specific encoding
        "skiprows": 2,        # Skip first 2 rows
        "usecols": [0, 2, 5], # Use only specific columns
        "parse_dates": ["date_column"]  # Parse dates
    }
)

# Database query
db_id = await add_dataset(
    source="./research.db",
    options={
        "query": "SELECT * FROM experiments WHERE accuracy > 0.9",
        "table_name": "experiments"  # Alternative: specify table
    }
)

# API with authentication
api_id = await add_dataset(
    source="https://api.example.com/data",
    options={
        "method": "GET",
        "headers": {
            "Authorization": "Bearer your-token",
            "Accept": "application/json"
        },
        "params": {
            "limit": 1000,
            "format": "json"
        }
    }
)
```

#### Batch Processing

```python
import os
import asyncio
from hierarchical_research_ai.tools import ResearchToolkit

async def process_research_folder():
    """Process an entire folder of research materials"""
    toolkit = ResearchToolkit()
    folder_path = "./research_materials/"
    
    sources_to_add = []
    
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        if filename.endswith(('.pdf', '.docx', '.txt')):
            sources_to_add.append({
                "source": file_path,
                "source_type": "document",
                "metadata": {
                    "description": f"Research material: {filename}",
                    "tags": ["research", "batch-upload"],
                    "filename": filename
                }
            })
        elif filename.endswith(('.csv', '.xlsx', '.json')):
            sources_to_add.append({
                "source": file_path,
                "source_type": "data",
                "metadata": {
                    "description": f"Dataset: {filename}",
                    "tags": ["data", "batch-upload"],
                    "filename": filename
                }
            })
    
    # Add all sources concurrently
    source_ids = await toolkit.add_multiple_sources(sources_to_add)
    print(f"Successfully processed {len(source_ids)} files")
    
    return source_ids

# Run batch processing
asyncio.run(process_research_folder())
```

## Session Management Examples

### CLI Session Management

```bash
# Start new research with session name
research-ai research --topic "AI Ethics" --session-name "Ethics Study 2024"

# Resume existing session
research-ai research --session-id abc123def456

# List all sessions
research-ai sessions

# List only active sessions
research-ai sessions --status active

# Search sessions
research-ai search-sessions "machine learning"

# Get session details
research-ai session-info abc123def456

# Export session for backup
research-ai export-session abc123def456 ./backup/session.json

# Import session
research-ai import-session ./backup/session.json

# Delete session
research-ai delete-session abc123def456

# Clean up old sessions
research-ai cleanup-sessions --max-age 30 --max-inactive 7

# Show session statistics
research-ai sessions-stats
```

### Interactive Session Selection

When you run `research-ai research`, you'll see:

```
Recent Sessions:
  1. Ethics Study 2024 - AI Ethics in Healthcare (2 days ago)
  2. Climate Research - Climate Change Adaptation (5 days ago)
  3. Market Analysis - AI Market Trends (1 week ago)
  n. Start new session

Choose session to resume or 'n' for new: 
```

### Python API Session Management

```python
import asyncio
from hierarchical_research_ai import HierarchicalResearchSystem
from hierarchical_research_ai.utils import SessionManager

async def session_example():
    session_manager = SessionManager()
    
    # Create new session
    session = session_manager.create_session(
        name="My Research Project",
        topic="Artificial Intelligence Ethics",
        requirements={
            "target_length": 25000,
            "citation_style": "APA",
            "privacy_mode": False
        },
        metadata={
            "project_code": "AIE-2024-001",
            "department": "Computer Science"
        }
    )
    
    print(f"Created session: {session.session_id}")
    
    # Resume research with session
    research_system = HierarchicalResearchSystem(session=session)
    result = await research_system.interactive_research()
    
    # List all sessions
    sessions = session_manager.list_sessions()
    for sess in sessions:
        print(f"{sess['name']}: {sess['topic']} ({sess['status']})")
    
    # Search sessions
    results = session_manager.search_sessions("AI")
    print(f"Found {len(results)} sessions matching 'AI'")

asyncio.run(session_example())
```

### Session State Management

```python
from hierarchical_research_ai.utils import SessionManager, MemoryManager

# Advanced session management
session_manager = SessionManager()
session = session_manager.load_session("session_id_here")

if session:
    # Access conversation history
    print(f"Conversation turns: {len(session.conversation_history)}")
    
    # Check progress
    progress = session.progress
    print(f"Phase: {progress['current_phase']}")
    print(f"Completion: {progress['completion_percentage']}%")
    
    # View agent outputs
    for agent_name, outputs in session.agent_outputs.items():
        print(f"{agent_name}: {len(outputs)} outputs")
    
    # Export session data
    exported = session_manager.export_session(session.session_id, "backup.json")
```

### Memory Management

```python
from hierarchical_research_ai.utils import MemoryManager

memory = MemoryManager()

# Add conversation turns
memory.add_conversation_turn("user", "What is machine learning?")
memory.add_conversation_turn("assistant", "Machine learning is...")

# Add agent outputs
memory.add_agent_output("LiteratureSurveyAgent", {
    "key_findings": ["Finding 1", "Finding 2"],
    "analysis": "Detailed analysis..."
})

# Get relevant context
context = memory.get_relevant_context("neural networks")

# Summarize session
summary = memory.summarize_session()
print(f"Key findings: {len(summary['key_findings'])}")

# Export memory for persistence
memory_data = memory.export_memory()

# Import memory state
memory.import_memory(memory_data)

# Compress memory to save space
memory.compress_memory(compression_ratio=0.5)
```

## Tips and Best Practices

### Source Management
1. **Organize with metadata**: Use descriptive tags and descriptions
2. **Check formats**: Ensure files are in supported formats
3. **Large files**: For very large datasets, consider sampling or chunking
4. **URLs**: Verify URLs are accessible and stable
5. **Privacy**: Use privacy mode for sensitive data

### Session Management
1. **Use descriptive names**: Name sessions clearly for easy identification
2. **Regular saves**: Session state is automatically saved during conversations
3. **Resume efficiently**: Take advantage of session resumption for long research
4. **Clean up**: Regularly clean up old or unused sessions
5. **Backup important sessions**: Export valuable sessions for backup

### Memory Management
1. **Monitor memory usage**: Check memory stats to avoid performance issues
2. **Compress when needed**: Use memory compression for long sessions
3. **Leverage context**: Use relevant context retrieval for better responses

```python
# Export your sources configuration
toolkit = ResearchToolkit()
manifest = toolkit.export_sources_manifest()

# Save for backup
import json
with open("sources_backup.json", "w") as f:
    json.dump(manifest, f, indent=2)

# Session backup
session_manager = SessionManager()
session_manager.export_session("session_id", "session_backup.json")
```

## Complete Workflow Example

```python
import asyncio
from hierarchical_research_ai import HierarchicalResearchSystem
from hierarchical_research_ai.tools import add_document
from hierarchical_research_ai.utils import SessionManager

async def complete_workflow():
    """Example of complete research workflow with session management"""
    
    # 1. Add your documents
    doc_id = await add_document(
        "./research/background.pdf",
        "Background research on the topic"
    )
    
    # 2. Check for existing sessions
    session_manager = SessionManager()
    recent_sessions = session_manager.list_sessions()[:3]
    
    if recent_sessions:
        print("Recent sessions:")
        for i, sess in enumerate(recent_sessions, 1):
            print(f"  {i}. {sess['name']} - {sess['topic']}")
        
        choice = input("Resume session (enter number) or start new (n): ")
        
        if choice.isdigit():
            session_id = recent_sessions[int(choice) - 1]['session_id']
            session = session_manager.load_session(session_id)
        else:
            session = None
    else:
        session = None
    
    # 3. Initialize research system
    research_system = HierarchicalResearchSystem(
        cli_mode=False,
        session=session
    )
    
    # 4. Start or resume research
    if session:
        print(f"Resuming: {session.name}")
        result = await research_system.resume_research(session.session_id)
    else:
        project = research_system.start_project(
            topic="AI Impact on Education",
            session_name="Education AI Study",
            target_length=30000
        )
        result = await research_system.generate_report(project.id)
    
    print(f"Research completed: {result['output_path']}")
    print(f"Session: {result['session_id']}")

# Run the workflow
asyncio.run(complete_workflow())
```