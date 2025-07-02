# HierarchicalResearchAI

A sophisticated multi-agent research system that leverages LangGraph supervisors to orchestrate hierarchical research workflows, integrating multiple LLMs and user-provided documents/data for comprehensive academic research and report generation.

## 🎯 Overview

HierarchicalResearchAI automates the entire research process from question formulation to final report generation. It uses a hierarchical multi-agent architecture where specialized agents handle different aspects of research under the coordination of LangGraph supervisors.

### Key Features

- **🤖 Multi-Agent Architecture**: Specialized agents for domain analysis, literature review, quantitative/qualitative analysis, quality assurance, and report generation
- **📊 Multi-LLM Integration**: Supports Perplexity (sonar-deep-research, sonar-pro), Claude (Sonnet 4, 3.5 Haiku), and Gemma 3n models
- **📚 Document Integration**: Import your own PDFs, Word docs, CSVs, Excel files, JSON data, and more
- **🔄 Session Management**: Persistent sessions with resume/create/delete functionality
- **🛡️ Privacy Mode**: Local model fallback for sensitive research
- **💰 Cost Tracking**: Monitor API usage across multiple LLM providers
- **📝 Academic Standards**: APA/MLA citation styles, academic formatting, quality assurance
- **🌐 Web Integration**: Ingest data from URLs, APIs, and web scraping

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/your-username/hierarchical-research-ai.git
cd hierarchical-research-ai
pip install -e .
```

### Environment Setup

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required API keys in `.env`:
```env
PERPLEXITY_API_KEY=your_perplexity_key
ANTHROPIC_API_KEY=your_anthropic_key
PRIVACY_MODE=false
```

### Basic Usage

#### Command Line Interface

```bash
# Start interactive research
research-ai research --topic "AI in Healthcare"

# Add your documents
research-ai add-source --source "./my-paper.pdf" --description "My preliminary research"

# List sessions
research-ai sessions

# Resume a session
research-ai research --session-id abc123
```

#### Python API

```python
import asyncio
from hierarchical_research_ai import HierarchicalResearchSystem

async def main():
    # Initialize system
    research_system = HierarchicalResearchSystem(cli_mode=False)
    
    # Start research project
    project = research_system.start_project(
        topic="Machine Learning Ethics",
        target_length=25000,
        citation_style="APA"
    )
    
    # Generate comprehensive report
    result = await research_system.generate_report(project.id)
    print(f"Report saved to: {result['output_path']}")

asyncio.run(main())
```

## 📖 Architecture

### Multi-Agent Hierarchy

#### Research Team
- **DomainAnalysisAgent**: Analyzes research domain and scope
- **LiteratureSurveyAgent**: Conducts comprehensive literature reviews
- **ResearchQuestionFormulationAgent**: Formulates precise research questions

#### Analysis Team
- **QuantitativeAnalysisAgent**: Handles statistical and numerical analysis
- **QualitativeAnalysisAgent**: Performs thematic and interpretive analysis
- **SynthesisAgent**: Integrates findings from multiple sources

#### Quality Assurance Team
- **PeerReviewAgent**: Evaluates research quality and rigor
- **CitationVerificationAgent**: Ensures proper academic citations
- **AcademicStandardsComplianceAgent**: Validates academic formatting

#### Generation Team
- **SectionWritingAgent**: Writes individual report sections
- **CoherenceIntegrationAgent**: Ensures report coherence and flow
- **FinalAssemblyAgent**: Assembles final formatted report

### LangGraph Supervision

The system uses LangGraph to orchestrate agent workflows through hierarchical supervisors:

1. **Research Planning Phase**: Domain analysis → Literature survey → Question formulation
2. **Data Collection Phase**: User source integration → External data gathering
3. **Analysis Phase**: Quantitative analysis → Qualitative analysis → Synthesis
4. **Quality Assurance Phase**: Peer review → Citation verification → Compliance check
5. **Report Generation Phase**: Section writing → Coherence integration → Final assembly

## 🔧 Advanced Features

### Document and Data Integration

Add your own research materials:

```python
from hierarchical_research_ai.tools import ResearchToolkit

toolkit = ResearchToolkit()

# Add documents
doc_id = await toolkit.add_source(
    source="./research/paper.pdf",
    source_type="document",
    metadata={
        "description": "Key research paper",
        "tags": ["primary-source", "peer-reviewed"]
    }
)

# Add datasets
data_id = await toolkit.add_source(
    source="./data/survey.csv",
    source_type="data",
    metadata={"description": "Survey results"}
)
```

Supported formats:
- **Documents**: PDF, Word (.docx), TXT, Markdown, HTML, XML
- **Data**: CSV, Excel, JSON, SQLite, APIs, Web scraping

### Session Management

```python
from hierarchical_research_ai.utils import SessionManager

session_manager = SessionManager()

# Create session
session = session_manager.create_session(
    name="AI Ethics Study",
    topic="Ethics in Artificial Intelligence",
    requirements={"target_length": 30000}
)

# Resume later
session = session_manager.load_session(session_id)
```

### Privacy Mode

For sensitive research, enable privacy mode to use local models:

```python
research_system = HierarchicalResearchSystem(privacy_mode=True)
```

## 📊 Output Examples

### Research Report Structure

Generated reports include:
- **Executive Summary** with key findings
- **Literature Review** integrating your sources with external research
- **Methodology** section explaining the research approach
- **Results** with quantitative and qualitative findings
- **Discussion** synthesizing all findings
- **Conclusion** with future research directions
- **References** in academic format (APA/MLA)
- **Appendices** with metadata and agent contributions

### Sample Output Metrics

```
✅ Research Completed Successfully

📊 Report Statistics:
   • Word Count: 28,450 words
   • Sections: 8 major sections
   • Citations: 127 academic sources
   • User Sources: 5 documents + 2 datasets
   • Quality Score: 8.7/10

💰 Cost Summary:
   • Total API Cost: $12.34
   • Perplexity: $8.21
   • Anthropic: $4.13

📁 Output: ./output/reports/AI_Ethics_Study_20240101_143022.md
```

## 🛠️ CLI Commands

### Research Commands
```bash
research-ai research [OPTIONS]           # Start interactive research
research-ai research --topic "Topic"     # Start with specific topic
research-ai research --session-id ID     # Resume session
```

### Source Management
```bash
research-ai add-source --source PATH     # Add document/data source
research-ai list-sources                 # List all sources
research-ai search-sources "query"       # Search sources
research-ai remove-source ID             # Remove source
research-ai sources-summary              # Show sources summary
```

### Session Management
```bash
research-ai sessions                     # List all sessions
research-ai session-info ID              # Show session details
research-ai delete-session ID            # Delete session
research-ai export-session ID PATH       # Export session
research-ai import-session PATH          # Import session
research-ai cleanup-sessions             # Clean old sessions
```

### System Commands
```bash
research-ai status                       # Show system status
research-ai costs                        # Show cost summary
research-ai config                       # Show configuration
```

## 🔒 Security and Privacy

- **Privacy Mode**: Use local models for sensitive research
- **Data Isolation**: User documents processed separately
- **API Key Security**: Environment variable protection
- **Session Encryption**: Local session data protection
- **Audit Trail**: Complete research process logging

## 📚 Examples

See `EXAMPLES.md` for comprehensive usage examples including:
- Document and data integration workflows
- Session management patterns
- Advanced configuration options
- Batch processing examples
- Python API usage patterns

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/test_agents.py
pytest tests/test_tools.py
pytest tests/test_workflows.py

# Run with coverage
pytest --cov=src tests/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📋 Requirements

### Core Dependencies
- Python 3.9+
- LangGraph 0.1.0+
- LangChain 0.1.0+
- aiohttp
- structlog
- rich (for CLI)

### LLM Providers
- Anthropic API (Claude models)
- Perplexity API (research models)
- Optional: Local models for privacy mode

### Document Processing
- pypdf (PDF processing)
- python-docx (Word documents)
- pandas (data analysis)
- beautifulsoup4 (web scraping)

## 🐛 Troubleshooting

### Common Issues

**API Key Errors**
```bash
# Check your .env file
cat .env | grep API_KEY

# Verify API keys are valid
research-ai status
```

**Memory Issues with Large Documents**
```python
# Enable memory optimization
research_system = HierarchicalResearchSystem(
    workspace_dir="./large_workspace",
    memory_optimization=True
)
```

**Session Loading Errors**
```bash
# List available sessions
research-ai sessions

# Clean up corrupted sessions
research-ai cleanup-sessions --repair
```

## 📄 License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## 🙏 Acknowledgments

- LangGraph for workflow orchestration
- LangChain for LLM integration
- Anthropic for Claude models
- Perplexity for research-optimized models
- Rich for beautiful CLI interfaces

## 📞 Support

- 📧 Email: support@hierarchical-research-ai.com
- 💬 Discord: [Join our community](https://discord.gg/hierarchical-research-ai)
- 📖 Documentation: [Full docs](https://docs.hierarchical-research-ai.com)
- 🐛 Issues: [GitHub Issues](https://github.com/your-username/hierarchical-research-ai/issues)

---

**Made with ❤️ for researchers, by researchers**