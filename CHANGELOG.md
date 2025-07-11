# Changelog

All notable changes to HierarchicalResearchAI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.1] - 2025-07-03

### Fixed
- 💰 **Cost Tracking System**: Comprehensive fix for cost tracking showing $0.00 despite API usage
  - Updated pricing to accurate 2025 rates for all Perplexity and Anthropic models
  - Integrated cost tracking directly into ChatPerplexity and ChatAnthropic model classes
  - Added tiktoken library for accurate token counting across all model invocations
  - Fixed cost accumulation and tracking throughout entire research workflow
  - Enhanced cost reporting with detailed model-specific breakdowns
- 🧹 **Report Generation Quality**: Major improvements to final report cleaning and polish
  - Implemented comprehensive content cleaning system removing all agent artifacts, thinking tags, and test sections
  - Added structured agent logging to /logs/agent_outputs/ separate from final reports
  - Enhanced report quality with polished abstract generation from synthesis outputs
  - Fixed content extraction to use cleaned, professional-grade text throughout all sections
- 🔄 **Editorial Workflow Correction**: Fixed EditorAgent implementation based on user feedback
  - EditorAgent now generates improvement guidelines rather than performing post-processing rewrites
  - SectionWritingAgent applies improvement guidelines during content generation for better integration
  - Improved quality assurance feedback loop with guidelines passed to content generators during assembly
  - Enhanced workflow to ensure editorial improvements are applied during report creation, not after

### Improved
- 🎯 **Model Integration**: Enhanced model wrapper classes with comprehensive cost tracking
  - ChatPerplexity class with built-in usage tracking and token counting
  - ChatAnthropicWithCosts wrapper for seamless cost integration
  - Accurate per-request cost calculation with detailed logging
- 📊 **Report Assembly**: Enhanced final report generation with content quality improvements
  - Better content cleaning with regex patterns for removing unwanted artifacts
  - Improved section assembly with guidelines-driven content enhancement
  - Enhanced metadata generation and structured logging separation

## [0.4.0] - 2025-07-03

### Added
- 🎨 **EditorAgent**: Automated content improvement system based on quality assurance feedback
  - Gathers comprehensive feedback from all QA agents (peer review, citations, compliance)
  - Creates targeted editing prompts with specific improvement recommendations
  - Parses and applies content improvements to analysis outputs with structured formatting
  - Tracks which sections were improved and provides editing summaries
  - Integrates seamlessly into workflow between QA and analysis phases

### Fixed  
- 🔄 **Report Generation**: Critical fixes for agent output collection in workflow execution
  - Fixed state accumulation during workflow execution to properly collect agent outputs across all phases
  - Added safe handling for agent output merging to prevent key errors during state updates
  - Resolved issue where reports contained only placeholder text instead of actual research content
  - Fixed workflow execution to pass complete agent outputs to report generator
- 📊 **Quality Assurance Loop**: Enhanced QA retry mechanism with automated content editing
  - Routes to editing phase when QA score is below threshold (6.0) instead of direct retry
  - Returns to analysis phase after editing for re-evaluation with improved content
  - Maintains retry limits to prevent infinite loops while enabling iterative improvement

### Improved
- 🔧 **Workflow Orchestration**: Enhanced supervisor workflow with editing phase integration
  - Added editing phase node and intelligent routing logic in workflow supervisor
  - Improved progress tracking and error handling during content editing operations
  - Enhanced logging for editing phase progress and improvements applied
  - Better state management for iterative improvement cycles with retry count tracking

## [0.3.1] - 2025-07-02

### Added
- 📁 **Enhanced Source Integration**: Comprehensive multi-source data ingestion system
  - Support for folders containing documents or data files with automatic content analysis
  - Individual file support for PDFs, Word docs, CSVs, Excel, JSON, and more
  - Website URL integration for web content retrieval and processing
  - API endpoint support for real-time data access and ingestion
  - MCP (Model Context Protocol) server address support for connected data sources
  - Intelligent source type detection and automatic document vs. data classification
- 🔍 **Advanced Source Management**: Robust source processing and organization
  - Multi-format input parsing (comma-separated, newline-separated, quoted paths)
  - Comprehensive source validation with detailed error handling
  - Metadata collection for descriptions, tags, and source organization
  - Content search functionality with relevance scoring across sources
  - Source summary generation with word counts, row counts, and format analysis

### Fixed
- 🔄 **Workflow Stability**: Resolved critical infinite loop issues in quality assurance
  - Added retry limits (max 3 attempts) to prevent infinite analysis/QA cycles
  - Fixed quality score access logic to handle both dict and list agent output formats
  - Enhanced error handling for quality score evaluation with proper fallbacks
  - Added detailed logging for quality score evaluation and retry attempts
- 📊 **Progress Tracking**: Improved workflow progress visibility and accuracy
  - Fixed "completed_agents=0 phase=unknown" logging issues with conditional progress updates
  - Implemented phase-specific agent completion tracking with proper cleanup during retries
  - Added phase completion logging with per-phase and total agent counts
  - Enhanced final workflow completion summary with comprehensive status reporting

### Improved
- 🎯 **Strategic Analysis Framework**: Enhanced business analysis capabilities
  - Improved business topic detection with expanded keyword matching
  - Enhanced strategic question generation with contextual categorization
  - Refined response parsing for strategic analysis contexts
  - Better integration of strategic analysis template framework
- 🛠️ **Error Handling**: Comprehensive validation and graceful failure recovery
  - Enhanced source validation with detailed feedback for invalid inputs
  - Improved error messages and logging throughout the system
  - Better handling of network failures and API timeouts
  - Graceful degradation when sources cannot be processed

## [0.3.0] - 2025-07-02

### Added
- 🎯 **Strategic Analysis Template Integration**: Comprehensive business analysis framework for executive-level research
  - Automatic detection of business/strategic topics using intelligent keyword matching
  - Executive-focused question categories: [CONTEXT], [CHALLENGE], [SCOPE], [BASELINE], [MARKET], [METRICS], [IMPACT]
  - Weighted completeness scoring for strategic vs standard research projects
  - Strategic requirements tracking with 19 specialized business analysis fields
- 📊 **Configurable Question Depth Control**: Four questioning depth levels
  - MINIMAL: Essential strategic context only (1-2 questions)
  - STANDARD: Focused strategic areas (2-3 questions)
  - COMPREHENSIVE: Thorough strategic analysis (3-4 questions)
  - EXECUTIVE: High-level business impact focus (2-3 questions)
- 🏢 **Executive-Ready Features**: Board-room quality deliverables
  - Strategic welcome message highlighting business analysis capabilities
  - Professional consulting-grade analytical standards
  - ROI-focused recommendations with implementation roadmaps
  - Competitive positioning and market analysis framework
- 🔧 **Enhanced Environment Configuration**: New strategic analysis settings
  - `STRATEGIC_ANALYSIS_MODE`: Enable/disable strategic analysis framework
  - `CLARIFICATION_DEPTH`: Control question detail level
  - `MAX_QUESTIONS_PER_ROUND`: Limit questions per clarification round
  - `CLI_AUTO_CHOICE`: Auto-select options for testing automation

### Improved
- ✅ **State Management**: Enhanced with strategic analysis requirements tracking
- ✅ **Question Generation**: Dual-mode system for strategic vs standard research
- ✅ **Completeness Calculation**: Weighted scoring for essential vs optional categories
- ✅ **CLI Interface**: Strategic mode detection with specialized welcome messages
- ✅ **Documentation**: Comprehensive strategic analysis template documentation

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