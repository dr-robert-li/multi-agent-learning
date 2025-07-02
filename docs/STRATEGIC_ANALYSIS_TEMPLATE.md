# Strategic Analysis Template Integration

## Overview

HierarchicalResearchAI now integrates a **Strategic Analysis Template** to provide executive-level strategic business analysis capabilities. This feature automatically detects business/strategic topics and applies a structured framework designed for board-ready deliverables and strategic decision-making.

## Features

### Automatic Strategic Detection
The system automatically detects when a research topic is business/strategic in nature and switches to strategic analysis mode. Topics containing keywords like:
- `business`, `strategy`, `market`, `competitive`, `organization`
- `company`, `revenue`, `growth`, `transformation`, `innovation`
- `consulting`, `planning`, `executive`, `leadership`, `management`
- Combinations like `market analysis`, `business analysis`, `digital transformation`

### Executive-Focused Question Framework
When strategic mode is activated, the system uses specialized questioning that follows a Strategic Analysis Template:

#### Strategic Question Categories
1. **[CONTEXT]** - Organization & Industry Context
2. **[CHALLENGE]** - Strategic Challenge Definition  
3. **[SCOPE]** - Analysis Scope & Constraints
4. **[BASELINE]** - Current State Analysis
5. **[MARKET]** - Competitive Dynamics
6. **[METRICS]** - Success Criteria
7. **[IMPACT]** - Business Impact & ROI

### Configurable Question Depth
Control the level of questioning detail through environment variables:

- **MINIMAL** (1-2 questions): Essential strategic context only
- **STANDARD** (2-3 questions): Focused strategic areas  
- **COMPREHENSIVE** (3-4 questions): Thorough strategic analysis
- **EXECUTIVE** (2-3 questions): High-level business impact focus

## Configuration

### Environment Variables

```bash
# Enable strategic analysis mode
STRATEGIC_ANALYSIS_MODE=true

# Set questioning depth
CLARIFICATION_DEPTH=executive  # Options: minimal, standard, comprehensive, executive

# Control question volume
MAX_QUESTIONS_PER_ROUND=3

# Auto-selection for testing
CLI_AUTO_CHOICE=n  # Automatically start new session
```

### Example Configuration (.env)
```env
# Strategic Analysis Template Configuration
STRATEGIC_ANALYSIS_MODE=true
CLARIFICATION_DEPTH=executive
MAX_QUESTIONS_PER_ROUND=2
```

## Usage Examples

### Automatic Strategic Detection
```bash
# These topics automatically trigger strategic mode:
research-ai research --topic "digital transformation strategy for retail banking"
research-ai research --topic "competitive analysis of SaaS market"
research-ai research --topic "organizational restructuring plan"
research-ai research --topic "market entry strategy for fintech"

# These topics use standard research mode:
research-ai research --topic "quantum physics principles"
research-ai research --topic "climate change effects"
research-ai research --topic "machine learning algorithms"
```

### Manual Mode Control
```bash
# Force strategic mode with environment variable
STRATEGIC_ANALYSIS_MODE=true research-ai research --topic "any topic"

# Disable strategic mode
STRATEGIC_ANALYSIS_MODE=false research-ai research --topic "business strategy"

# Set executive-level questioning
CLARIFICATION_DEPTH=executive research-ai research --topic "digital transformation"

# Minimal questioning for quick analysis
CLARIFICATION_DEPTH=minimal research-ai research --topic "market analysis"
```

## Strategic Welcome Message

When strategic mode is active, users see:

```
┌─ Strategic Research Assistant ─┐
│ Welcome to HierarchicalResearchAI - Strategic Analysis Mode
│
│ I'll help you conduct executive-level strategic business analysis 
│ using a Strategic Analysis Template framework.
│
│ Strategic Features:
│ - Executive-focused business analysis framework
│ - Strategic challenge diagnosis and recommendation
│ - Competitive positioning and market analysis
│ - Implementation roadmaps with ROI projections
│ - Board-ready deliverables and executive summaries
│ - Industry best practices and proven frameworks
│
│ Question Depth: EXECUTIVE
│ - MINIMAL: Essential strategic context only (1-2 questions)
│ - STANDARD: Focused strategic areas (2-3 questions)  
│ - COMPREHENSIVE: Thorough strategic analysis (3-4 questions)
│ - EXECUTIVE: High-level business impact focus (2-3 questions)
└─────────────────────────────────┘
```

## Strategic Question Examples

### Executive Depth
- `[IMPACT] What strategic decision needs to be made and what's the expected ROI?`
- `[COMPETITIVE] What competitive advantage or market position are you seeking?`
- `[CONSTRAINTS] What are the key resource constraints and success metrics?`

### Standard Depth
- `[CONTEXT] What organization type and industry sector require strategic analysis?`
- `[CHALLENGE] What specific strategic question or decision needs to be addressed?`
- `[SCOPE] What are the key constraints, timeframe, and success criteria?`

### Comprehensive Depth
- `[CONTEXT] What organization and industry sector are we analyzing?`
- `[CHALLENGE] What specific strategic challenge or opportunity requires analysis?`
- `[BASELINE] What is the current market position and performance baseline?`
- `[MARKET] What competitive or market changes are driving the strategic need?`

## State Management

### Strategic Requirements Tracking
The system tracks additional strategic analysis fields:

```python
"strategic_analysis": {
    "organization_name": "",
    "organization_type": "",
    "industry_sector": "",
    "organization_size": "",
    "business_model": "",
    "strategic_challenge": "",
    "time_horizon": "",
    "urgency_level": "",
    "decision_context": "",
    "current_performance": "",
    "known_challenges": "",
    "stakeholder_context": "",
    "technology_relevance": "",
    "market_evolution": "",
    "transformation_scope": "",
    "resource_constraints": "",
    "risk_tolerance": "",
    "success_metrics": "",
    "implementation_capacity": ""
}
```

### Completeness Scoring
Strategic projects use weighted completeness scoring:
- **Essential categories** (higher weight): topic, strategic_challenge, organization_type
- **Optional categories** (lower weight): organization_name, industry_sector, decision_context

## Integration with Strategic Analysis Framework

This integration implements a comprehensive Strategic Analysis Template framework:

### Initial Clarification Requirements
1. **Organization and Industry Context**
2. **Strategic Challenge Definition**
3. **Current State Analysis Requirements**
4. **Future State and Technology Context**
5. **Analysis Scope and Constraints**
6. **Reference Materials and Source Documents**

### Strategic Framework Application
- **Executive-focused analytical depth** with business impact translation
- **Rigorous fact-checking** with evidence-based insights
- **Clear, action-oriented writing** prioritizing strategic recommendations
- **Board-ready recommendations** with ROI projections and implementation roadmaps

### Quality Standards
- **Executive readability** using pyramid principle structure
- **Strategic clarity** with direct, business-focused language
- **Professional integrity** with consulting-grade analytical standards
- **Competitive positioning** with sharp market position definition

## Testing Strategic Mode

Test the strategic analysis integration:

```bash
# Test strategic detection
python -c "
from src.hierarchical_research_ai.cli.question_generator import QuestionGenerator
from src.hierarchical_research_ai.config.models import ModelConfig
gen = QuestionGenerator(ModelConfig())
print('Strategic:', gen._is_business_strategic_topic('digital transformation'))
print('Standard:', gen._is_business_strategic_topic('quantum physics'))
"

# Test CLI with strategic mode
STRATEGIC_ANALYSIS_MODE=true CLARIFICATION_DEPTH=executive research-ai research --topic "business strategy"
```

## Benefits

### For Business Users
- **Executive-ready analysis** designed for C-suite consumption
- **Strategic framework application** using proven business methodologies
- **Board-ready deliverables** with implementation roadmaps
- **ROI-focused recommendations** with competitive positioning

### For Researchers
- **Structured questioning** following strategic analysis best practices
- **Context-aware completeness** tracking essential vs. optional information
- **Depth control** matching questioning intensity to analysis needs
- **Professional standards** ensuring consulting-grade output quality

### For Organizations
- **Decision support** with clear go/no-go criteria and investment priorities
- **Risk mitigation** with scenario planning and contingency strategies
- **Implementation guidance** with 90-day, 1-year, and 3-year milestones
- **Success tracking** with KPIs, targets, and monitoring mechanisms

## Conclusion

The Strategic Analysis Template integration transforms HierarchicalResearchAI into a comprehensive strategic business analysis platform capable of producing executive-level deliverables that meet board-room standards while maintaining the flexibility to handle standard research topics using traditional academic approaches.