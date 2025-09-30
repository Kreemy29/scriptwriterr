# AI Script Studio - Testing Documentation

## Overview

This document describes the comprehensive testing system created for the AI Script Studio project. The testing suite validates all functionalities, system prompts, and components to ensure everything works correctly.

## Test Scripts

### 1. `comprehensive_test_suite.py` - Full Test Suite

The main testing script that validates:

- **Database Operations**: CRUD operations, models, ratings system
- **AI Generation**: All system prompts and generation modes (RAG, Fast, Template)
- **RAG System**: Retrieval-augmented generation, embeddings, copy detection
- **Compliance System**: Content safety checking and scoring
- **Auto-Scoring**: LLM-based script quality assessment
- **Policy Learning**: Bandit learning system for optimization
- **Data Hierarchy**: Model-specific vs general content management
- **Import/Export**: Data management functionality
- **Health Checks**: Deployment readiness validation
- **Persona/Content Combinations**: All creator and content type combinations

**Usage:**
```bash
python comprehensive_test_suite.py
python comprehensive_test_suite.py --debug  # Show full error traces
```

### 2. `quick_test.py` - Fast Validation

A simplified test for quick validation of core functionality:

- Environment setup (API key)
- Database connectivity
- Core module imports
- Basic script generation
- Compliance system

**Usage:**
```bash
python quick_test.py
```

## System Prompts Tested

The test suite validates all system prompts used in the application:

### 1. RAG System Prompts (`src/rag_integration.py`)
- **Enhanced System Prompt**: For SOLO content creators with body-focused content
- **Content Style Guidelines**: NO corny pickup lines, sophisticated humor
- **Language Rules**: Solo-focused language (I, me, my vs we, us, our)
- **Visual Beat Requirements**: Unique, varied visual moments

### 2. Fast Generation Prompts (`src/rag_integration.py`)
- **Fast Mode Prompt**: Streamlined version for speed
- **Diversity Requirements**: Completely different scripts with varied approaches
- **Hook Strategies**: POV scenarios, reverse bait, questions, challenges

### 3. Template Generation Prompts (`src/deepseek_client.py`)
- **Video Planning Template**: Structured JSON output for video production
- **Script Guidance Rules**: Conditional script content based on video type
- **Hook Distinction**: Text overlay vs actual visual/audio hooks
- **Action Scene Requirements**: Detailed, specific scene descriptions

### 4. Auto-Scoring Prompts (`src/auto_scorer.py`)
- **LLM Judge System**: 6-dimension scoring (overall, hook, originality, style_fit, safety, authenticity)
- **Consistency Requirements**: Objective scoring with confidence levels

## Test Configuration

The test suite uses the following configuration:

```python
TEST_CONFIG = {
    "test_creators": ["Emily Kent", "Marcie", "Mia", "General Content"],
    "test_content_types": ["thirst-trap", "skit", "reaction-prank", "talking-style", "lifestyle", "fake-podcast"],
    "test_personas": ["girl-next-door; playful; witty", "bratty; teasing; demanding", "confident; in control"],
    "test_boundaries": ["No explicit words; suggestive only", "Spicy mode allowed", "Brand-safe content"],
    "min_scripts_per_test": 2,
    "timeout_seconds": 30
}
```

## Components Tested

### Database Layer (`src/db.py`, `src/models.py`)
- ✅ Script model with all fields (legacy + template format)
- ✅ Rating and revision tracking
- ✅ Model profiles and content templates
- ✅ Embedding storage for RAG
- ✅ Policy weights for learning system

### AI Generation Systems
- ✅ **RAG Integration** (`src/rag_integration.py`): Enhanced script generation with retrieval
- ✅ **Fast Generation** (`src/rag_integration.py`): Speed-optimized generation
- ✅ **Template Generation** (`src/deepseek_client.py`): Structured video planning templates
- ✅ **DeepSeek Client** (`src/deepseek_client.py`): API integration and prompt management

### RAG System (`src/rag_retrieval.py`)
- ✅ Semantic embeddings with SentenceTransformers
- ✅ Hybrid retrieval (semantic + BM25 + quality + freshness)
- ✅ Copy detection and anti-plagiarism
- ✅ Dynamic few-shot pack building
- ✅ Policy-weighted retrieval

### Quality & Compliance
- ✅ **Compliance Checker** (`src/compliance.py`): Content safety validation
- ✅ **Auto Scorer** (`src/auto_scorer.py`): LLM-based quality assessment
- ✅ **Policy Learner** (`src/bandit_learner.py`): Multi-armed bandit optimization

### Data Management
- ✅ **Data Hierarchy** (`src/data_hierarchy.py`): Model-specific vs general content
- ✅ **Import/Export**: JSONL data management
- ✅ **Reference Retrieval**: Hybrid reference system

## Running Tests

### Prerequisites
1. Python 3.8+
2. All dependencies installed: `pip install -r requirements.txt`
3. DEEPSEEK_API_KEY environment variable set (for generation tests)
4. Database initialized

### Quick Start
```bash
# Quick validation
python quick_test.py

# Full test suite
python comprehensive_test_suite.py

# With debug output
python comprehensive_test_suite.py --debug
```

### Expected Output

The test suite generates:
- Real-time progress logs with timestamps
- Detailed test results for each component
- Performance metrics (execution time)
- Comprehensive test report saved to file
- Overall pass/fail status

### Test Report

Each test run generates a detailed report including:
- Summary statistics (pass/fail rates)
- Individual test results with details
- System information
- Test configuration
- Error details for failed tests

## Interpreting Results

### Success Indicators
- ✅ All tests pass
- Database operations work correctly
- AI generation produces valid scripts
- System prompts generate appropriate content
- Compliance system correctly classifies content
- RAG system retrieves relevant references

### Common Issues
- ❌ **API Key Missing**: Set DEEPSEEK_API_KEY environment variable
- ❌ **Database Errors**: Run `python -c "from src.db import init_db; init_db()"`
- ❌ **Import Errors**: Install missing dependencies
- ❌ **Generation Failures**: Check API key validity and rate limits

## Continuous Testing

For development and deployment:

1. **Pre-commit**: Run `python quick_test.py`
2. **Pre-deployment**: Run `python comprehensive_test_suite.py`
3. **CI/CD Integration**: Include both scripts in automated testing
4. **Health Monitoring**: Use built-in health checks for production monitoring

## System Prompt Validation

The test suite specifically validates that all system prompts:

1. **Generate Valid Output**: JSON format, required fields present
2. **Follow Content Guidelines**: Solo content, appropriate language
3. **Maintain Consistency**: Reproducible results with same inputs
4. **Handle Edge Cases**: Different personas, content types, boundaries
5. **Respect Compliance**: Generated content passes safety checks

## Performance Benchmarks

Expected performance (approximate):
- Quick Test: 5-15 seconds
- Full Test Suite: 2-5 minutes
- Individual Generation: 1-3 seconds per script
- RAG Retrieval: <1 second per query
- Database Operations: <100ms per operation

## Contributing

When adding new functionality:
1. Add corresponding tests to `comprehensive_test_suite.py`
2. Update test configuration if needed
3. Document new system prompts
4. Ensure all tests pass before submitting

## Troubleshooting

### Common Solutions
```bash
# Reset database
rm studio.db
python -c "from src.db import init_db; init_db()"

# Check dependencies
pip install -r requirements.txt

# Verify API key
echo $DEEPSEEK_API_KEY

# Run with debug output
python comprehensive_test_suite.py --debug
```

### Getting Help
1. Check test report for detailed error information
2. Run with `--debug` flag for full stack traces
3. Verify environment setup with `python quick_test.py`
4. Check logs in the generated test report file

