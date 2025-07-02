# Changelog

All notable changes to HierarchicalResearchAI will be documented in this file.

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