# Codebase Knowledge CSV Schema Analysis

## Current State Analysis
- Business-unit focused structure (not suitable for development knowledge)
- Need generic, flexible schema for any codebase
- Must integrate with refactored Agno RowChunking system
- Developer-centric query patterns required

## Developer Query Patterns Analysis

### Common Developer Questions:
1. **"How do I..."** - Implementation guidance
2. **"Why does..."** - Architecture/design decisions
3. **"Where is..."** - Code location and navigation
4. **"What's the pattern for..."** - Best practices and conventions
5. **"How to debug..."** - Troubleshooting guidance
6. **"What dependencies..."** - Integration knowledge
7. **"How to test..."** - Testing approaches
8. **"How to deploy..."** - Operational knowledge

### Knowledge Categories:
- **Architecture**: System design, patterns, principles
- **Implementation**: Code examples, best practices
- **Configuration**: Setup, environment, deployment
- **Testing**: Test patterns, coverage, strategies
- **Debugging**: Common issues, troubleshooting
- **Integration**: APIs, dependencies, external systems
- **Performance**: Optimization, monitoring, scaling
- **Security**: Authentication, authorization, vulnerabilities

## RAG System Requirements
- Semantic search on question/content fields
- Metadata filtering on category/component/tags
- Context-aware chunking for long answers
- Cross-reference capabilities via file_references
- Difficulty-based progressive disclosure

## Schema Design Principles
1. **Query-Optimized**: Primary fields match developer search patterns
2. **Flexible Metadata**: Tags and categories allow multiple classification dimensions
3. **Context-Rich**: File references and code examples provide actionable context
4. **Scalable**: Works for small projects to enterprise codebases
5. **Maintainable**: Clear structure for easy updates and curation