# Changelog

All notable changes to HierarchicalResearchAI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.3] - 2025-07-02

### Fixed
- 🔧 **Critical Asyncio Fix**: Resolved "asyncio.run() cannot be called from a running event loop" error
  - Implemented `run_async_safe()` function with proper thread isolation for nested event loops
  - Added async-safe input handling in PromptConsole to prevent event loop conflicts
  - CLI now works reliably in all execution environments (sync, async, nested loops)
- 🔧 **Rich Library Replacement**: Completely replaced Rich with prompt_toolkit for reliable terminal input
  - Migrated from Rich Console to PromptConsole for consistent input handling
  - Removed all Rich markup patterns (`[red]`, `style='error'`, etc.) causing display issues
  - Updated table rendering system to use prompt_toolkit components
  - Fixed input visibility issues across different terminal environments
- 🔧 **Console Import Errors**: Fixed "name 'Console' is not defined" errors in CLI interface
  - Updated all CLI modules to use PromptConsole consistently
  - Removed problematic Rich dependencies causing import conflicts
- 🔧 **Terminal Input Handling**: Enhanced terminal input system with better fallbacks
  - Added sync input fallback for async contexts to prevent prompt_toolkit conflicts
  - Improved error handling for terminal input across SSH, tmux, and local environments

### Added
- ✨ **CLI Testing Support**: Added `CLI_AUTO_CHOICE` environment variable for automated testing
- ✨ **Async Safety**: Comprehensive async execution handling for CLI commands
- ✨ **Better Error Recovery**: Improved graceful handling of input and event loop errors

### Improved
- ✅ **CLI Reliability**: CLI interface now starts successfully without asyncio errors
- ✅ **Input Visibility**: Terminal input is now visible and reliable across all environments
- ✅ **Error Messages**: Cleaner error display without Rich markup conflicts

## [0.2.2] - 2025-07-02

### Fixed
- 🔧 **Perplexity API Integration**: Updated model names to use correct Perplexity models
  - Changed `deep_research_model` from `llama-3.1-sonar-large-128k-online` to `sonar-deep-research`
  - Changed `fast_search_model` from `llama-3.1-sonar-small-128k-online` to `sonar-pro`
- 🔧 **Message Formatting**: Fixed ChatPerplexity class message role formatting
  - Changed from using 'system' role to 'user' role for all messages
  - Resolved "Last message must have role `user` or `tool`" API errors
- 🔧 **Token Limits**: Updated max_tokens to 8000 for both Perplexity models per documentation
- 🔧 **CLI Input Visibility**: Added multiple input methods to handle terminal echo issues
  - Added force_echo, builtin, readline, raw, and echo input methods
  - Implemented DEBUG_INPUT and INPUT_METHOD environment variables for troubleshooting
- 🔧 **Error Logging**: Enhanced error reporting and diagnostics for API troubleshooting

### Improved
- ✅ **Research System**: Full research workflow now functional and generating reports
- ✅ **API Testing**: Added comprehensive API testing utilities for validation
- ✅ **Model Configuration**: Improved model initialization and error handling
- ✅ **Documentation**: Updated README with troubleshooting section for CLI input issues

### Verified
- ✅ Perplexity sonar-pro model working correctly with 200 OK responses
- ✅ Research system generating reports (149+ words in test execution)
- ✅ CLI interface functional with multiple input method workarounds
- ✅ Cost tracking and session management operational
- ✅ Async research workflow execution working end-to-end

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