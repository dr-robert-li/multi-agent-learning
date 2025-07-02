# Changelog

All notable changes to HierarchicalResearchAI will be documented in this file.

## [0.2.1] - 2025-07-02

### Fixed
- **Critical Fix**: Resolved package import errors that prevented CLI commands from working
- **Package Structure**: Restructured `/src/` directory to properly organize modules within `hierarchical_research_ai/` package
- **Module Imports**: Fixed relative import paths in `__init__.py` for correct module resolution
- **CLI Functionality**: Restored full CLI command functionality (`research-ai`, `hrai` commands now work correctly)

### Changed
- **Package Layout**: Moved all modules (`agents/`, `cli/`, `config/`, `tools/`, `utils/`, `workflows/`) into proper package structure
- **Import Paths**: Updated package imports to use correct relative paths (`.workflows.research_workflow`)
- **Entry Points**: Verified console script entry points work correctly after package restructuring

## [0.2.0] - 2025-07-02

### Added
- Complete testing infrastructure (108+ tests)
- CLI commands system with Rich terminal UI
- Enhanced configuration system (`AgentConfig`, `TeamConfig`)
- Comprehensive `CostTracker` with budget management
- Virtual environment setup and development tools
- MIT License (2025 copyright)

### Fixed
- Circular import issues between CLI and workflow modules
- Pydantic validation conflicts in ChatPerplexity
- Type annotations and async method signatures
- Interactive session parameter handling
- Structlog import linter warnings

### Changed
- **Author**: Updated to "Dr. Robert Li"
- **Repository**: Updated to `https://github.com/dr-robert-li/multi-agent-learning`
- **Dependencies**: Added semantic-scholar, pandoc, spacy, typing-extensions
- Enhanced error handling and code organization

## [0.1.0] - 2025-07-02

### Added
- Initial project structure and multi-agent architecture
- Core configuration systems (models, costs)
- Basic CLI interface and LangGraph integration
- Multi-LLM support (Perplexity, Anthropic, Ollama)
- Privacy mode framework and session management