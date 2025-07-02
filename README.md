# HierarchicalResearchAI

**Version 0.4.1**  
**Author: Dr. Robert Li**

A sophisticated multi-agent research system that leverages LangGraph supervisors to orchestrate hierarchical research workflows, integrating multiple LLMs and user-provided documents/data for comprehensive academic research and report generation.

## 🎯 Overview

HierarchicalResearchAI automates the entire research process from question formulation to final report generation. It uses a hierarchical multi-agent architecture where specialized agents handle different aspects of research under the coordination of LangGraph supervisors.

### Key Features

- **🤖 Multi-Agent Architecture**: Specialized agents for domain analysis, literature review, quantitative/qualitative analysis, quality assurance, and report generation
- **📊 Multi-LLM Integration**: Supports Perplexity (sonar-deep-research, sonar-pro), Claude (Sonnet 4, 3.5 Haiku), and Gemma 3n models
- **📚 Enhanced Source Integration**: Import folders, individual files, URLs, API endpoints, and MCP servers with intelligent type detection
- **🔄 Session Management**: Persistent sessions with resume/create/delete functionality
- **🛡️ Privacy Mode**: Local model fallback for sensitive research
- **💰 Accurate Cost Tracking**: Real-time API cost monitoring with 2025 pricing and detailed breakdowns across multiple LLM providers
- **📝 Academic Standards**: APA/MLA citation styles, academic formatting, quality assurance
- **✨ Enhanced Report Quality**: Professional content cleaning, structured agent logging, and editorial workflow improvements
- **🌐 Multi-Source Data Ingestion**: Comprehensive support for documents, data files, web APIs, and connected services
- **💼 Strategic Analysis Framework**: Executive-focused business analysis with intelligent topic detection and configurable depth
- **🔧 Robust Workflow Management**: Fixed infinite loops, enhanced progress tracking, and improved error handling

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/dr-robert-li/multi-agent-learning.git
cd multi-agent-learning
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
# Show available commands
research-ai --help

# Start interactive research
research-ai research --topic "AI in Healthcare"

# Check system status
research-ai status

# Show version
research-ai version

# Add your documents
research-ai add-source --source "./my-paper.pdf" --description "My preliminary research"

# List sessions
research-ai sessions

# Resume a session
research-ai research --session-id abc123

# Enable privacy mode
research-ai research --privacy-mode --topic "Sensitive Research"
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
- **SectionWritingAgent**: Writes individual report sections with QA improvement guidelines
- **CoherenceIntegrationAgent**: Ensures report coherence and flow
- **FinalAssemblyAgent**: Assembles final formatted report
- **EditorAgent**: Generates improvement guidelines based on quality assurance feedback

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

**Note**: The `output/` directory is automatically created when research is conducted and is excluded from version control.

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
research-ai version                      # Show version information
research-ai sessions-stats               # Show session statistics
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
- prompt_toolkit (for CLI)
- tiktoken (for cost tracking)

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

**Perplexity API Issues**
```bash
# Test Perplexity models specifically
python -c "from src.hierarchical_research_ai.config.models import ModelConfig; import asyncio; asyncio.run(ModelConfig().fast_search_model.ainvoke('test'))"

# Check model names in logs
LOG_LEVEL=DEBUG research-ai research --topic "test"
```

**CLI Input Visibility Issues**
```bash
# Test which input method works best for your terminal
research-ai test-input

# Try different input methods if typing is not visible
INPUT_METHOD=native research-ai research
INPUT_METHOD=readline research-ai research
INPUT_METHOD=force_echo research-ai research

# Enable input debugging
DEBUG_INPUT=true research-ai research

# The system auto-detects the best method, but you can override:
# - native: Direct terminal control (good for most terminals)
# - readline: Uses Python readline (good for TMUX/SSH)
# - prompt_toolkit: Prompt toolkit input (good for modern terminals)
# - force_echo: Aggressive echo forcing (good for problematic terminals)
# - simple: Basic fallback (works everywhere but may be invisible)
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

**Cost Tracking Issues**
```bash
# Check cost tracking status
research-ai status

# View detailed cost logs
cat logs/cost_tracking.json

# Verify API keys and models are configured correctly
echo $PERPLEXITY_API_KEY | head -c 10
echo $ANTHROPIC_API_KEY | head -c 10
```

**Report Quality Issues**
```bash
# Check agent logs for debugging
ls -la logs/agent_outputs/

# Verify content cleaning is working
grep -i "<think>" output/reports/*.md  # Should return no results
```

**Asyncio Event Loop Errors**
- **Problem**: `Error: asyncio.run() cannot be called from a running event loop`
- **Solution**: Fixed in v0.2.3. Update to latest version or use `CLI_AUTO_CHOICE=n` environment variable for automated testing.

**Terminal Input Not Visible**
- **Problem**: When typing, characters don't appear on screen
- **Solution**: Fixed in v0.2.3 with prompt_toolkit replacement. For older versions, try:
  ```bash
  INPUT_METHOD=force_echo research-ai research
  DEBUG_INPUT=true research-ai research  # For debugging
  ```

**API Connection Issues**
- **Problem**: 400 Bad Request errors from Perplexity
- **Solution**: Fixed in v0.2.2+. Check your API keys and model configurations.

### Debug Commands

**Test Terminal Input Methods**
```bash
research-ai test-input  # Test different input methods
```

**Check System Status**
```bash
research-ai status  # Verify model configurations and API access
```

**Environment Variables for Testing**
```bash
CLI_AUTO_CHOICE=n research-ai research  # Skip session selection
DEBUG_INPUT=true research-ai research   # Enable input debugging
INPUT_METHOD=simple research-ai research # Force simple input method
```

### Getting Help

If you encounter issues:
1. Check the [CHANGELOG.md](./CHANGELOG.md) for recent fixes
2. Run `research-ai status` to verify configuration
3. Use `research-ai test-input` to diagnose terminal issues
4. Check GitHub Issues for similar problems

## 📋 Version History

See [CHANGELOG.md](./CHANGELOG.md) for detailed version history and release notes.

**Current Version: 0.4.1**
- ✅ **Fixed Cost Tracking**: Comprehensive cost tracking system with accurate 2025 API pricing and real-time monitoring
- ✅ **Enhanced Report Quality**: Professional-grade report generation with content cleaning and structured logging
- ✅ **Corrected Editorial Workflow**: Improved quality assurance with guidelines applied during content generation
- ✅ **Enhanced Source Integration**: Support for folders, individual files, URLs, API endpoints, and MCP servers
- ✅ **Intelligent Type Detection**: Automatic classification of documents vs. data sources
- ✅ **Robust Workflow Management**: Fixed infinite loops with retry limits and enhanced progress tracking  
- ✅ **Strategic Analysis Framework**: Executive-focused business analysis with intelligent topic detection
- ✅ **Multi-Source Data Ingestion**: Comprehensive support for diverse data sources and formats

## 📄 License

This project is licensed under the MIT License - see the `LICENSE` file for details.

**Copyright (c) 2025 Dr. Robert Li**

## 🙏 Acknowledgments

- LangGraph for workflow orchestration
- LangChain for LLM integration
- Anthropic for Claude models
- Perplexity for research-optimized models
- prompt_toolkit for reliable terminal interfaces

## 📞 Support

- 🐛 Issues: [GitHub Issues](https://github.com/dr-robert-li/multi-agent-learning/issues)
- 📋 Changelog: [CHANGELOG.md](./CHANGELOG.md)

**Note**: This project is provided "as-is" without warranty or support. While no active support is provided, issues can be logged on the GitHub issues page for tracking purposes.

---

**Made with ❤️ for researchers, by researchers**