# PagBank V2 Multi-Agent System - Central Specifications

**Epic ID**: pagbank-v2-production  
**Environment Stages**: dev → homolog → prod  
**Last Updated**: 2025-01-14  
**Version**: 2.0.0  

## Overview

Complete specifications for PagBank V2 transformation from POC to production-ready "agent factory" platform using Agno framework patterns, generic agent architectures, and proven infrastructure.

## Core Architecture Requirements

### 1. Ana Router Specification
- **Implementation**: Agno Team with `mode="route"` pattern
- **Members**: Dynamic loading via `[get_agent(name) for name in agent_names]`
- **Routing Logic**: Business unit identification and Portuguese responses
- **Integration**: Replace existing monolithic orchestrator completely

### 2. Generic Agent Factory Specification
- **Pattern**: Universal `get_agent(name: str) -> Agent` factory
- **Flexibility**: Branch-agnostic design (not PagBank-specific)
- **Caching**: Agent instance caching for performance
- **Configuration**: Database-driven with file fallback

### 3. Database Architecture Specification
- **Primary**: PostgreSQL with PgVector extension
- **Fallback**: SQLite for development environments
- **Connection**: Pool size 20, max overflow 30, recycle 3600s
- **Migration**: Alembic with environment-specific contexts

## Feature Specifications

### T-004: 5-Level Typification System

#### Business Logic Requirements
- **Hierarchy**: Business Unit → Product → Motive → Submotive → Conclusion
- **Validation**: Only valid business logic combinations allowed
- **Language**: Portuguese categories from knowledge base CSV
- **Integration**: Routes to correct specialist agents

#### Technical Requirements
- **Framework**: Agno workflow implementation
- **Validation**: Pydantic models with strict hierarchy validation
- **Performance**: < 30 seconds for complete workflow
- **Error Handling**: Graceful degradation with helpful suggestions

#### Acceptance Criteria
- [ ] 56 valid typification paths extracted from CSV
- [ ] Pydantic validation prevents invalid combinations
- [ ] Portuguese category names implemented exactly
- [ ] Routes to correct agents based on business unit
- [ ] Comprehensive test suite with 90%+ coverage

### T-005: Agent Versioning System

#### Business Logic Requirements
- **Versions**: Support v25, v26, v27 and future versions
- **Variants**: 2+ simultaneous versions for A/B testing
- **Prompts**: Different prompts per version
- **Management**: Hot deployment without system restart

#### Technical Requirements
- **Storage**: Database-driven configuration
- **API**: RESTful endpoints for version management
- **Performance**: Version switching < 100ms
- **Audit**: Complete version history and metrics

#### Acceptance Criteria
- [ ] Version creation, activation, deprecation working
- [ ] A/B testing with traffic distribution
- [ ] Different prompts supported per version
- [ ] Database-driven configuration loading
- [ ] CLI and API management interfaces

### T-006: Production Monitoring System

#### Business Logic Requirements
- **Real-time**: Live monitoring dashboard
- **Analytics**: Agent performance and system health
- **Alerts**: Intelligent alerting with multiple channels
- **Integration**: Typification and versioning analytics

#### Technical Requirements
- **Dashboard**: Interactive HTML with 30-second updates
- **Metrics**: Response time, success rate, error tracking
- **Alerts**: Email, webhook, WhatsApp delivery
- **Performance**: < 200ms dashboard response time

#### Acceptance Criteria
- [ ] Monitoring system live and functional
- [ ] Alerts configured and working
- [ ] Performance analytics operational
- [ ] Real-time metrics for agent performance
- [ ] Analytics for typification/versioning effectiveness

## Infrastructure Specifications

### Environment Configuration

#### Development (dev)
- **Database**: SQLite fallback for offline development
- **Secrets**: Local .env file with development keys
- **Logging**: Debug level with rich console output
- **Resources**: Local development resources only

#### Homolog (homolog)
- **Database**: PostgreSQL with development schema
- **Secrets**: Environment variables with test keys
- **Logging**: Info level with structured output
- **Resources**: Staging AWS resources

#### Production (prod)
- **Database**: PostgreSQL with production schema
- **Secrets**: AWS Secrets Manager integration
- **Logging**: Warning level with CloudWatch integration
- **Resources**: Production AWS infrastructure

### Dependencies Specification

#### Core Production Dependencies
```toml
# Database & Migration
"alembic>=1.14.0"
"psycopg2-binary>=2.9.0"

# Cloud & Deployment  
"boto3>=1.37.0"
"docker>=7.1.0"

# Development Tools
"ruff>=0.9.0"

# AI/ML Production
"tiktoken>=0.8.0"
"nest-asyncio>=1.6.0"

# HTTP & Communication
"requests>=2.32.0"

# User Experience
"tqdm>=4.67.0"
```

#### Container Specification
- **Base**: python:3.12-slim
- **Security**: Non-root user execution
- **Environment**: Multi-stage builds for dev/homolog/prod
- **Health**: Container health checks every 30 seconds

### AWS Infrastructure Specification

#### ECS/Fargate Configuration
- **CPU**: 2048 (2 vCPU) for production
- **Memory**: 4096 MB for production
- **Instances**: Minimum 2 for high availability
- **Load Balancer**: ALB with HTTPS termination

#### Database Configuration
- **Engine**: PostgreSQL 15+
- **Class**: db.r6g.large for production
- **Multi-AZ**: Enabled for high availability
- **Backup**: Automated daily backups with 7-day retention

## Integration Requirements

### Context Injection
- **Task Tool**: Full codebase access with context injection
- **Zen Tools**: Limited context, require explicit information
- **Subagents**: Inherit main agent context automatically

### Model Selection Strategy
- **Gemini 2.5 Pro**: Deep thinking, architecture decisions, complex analysis
- **Grok 4**: Research, investigation, technical validation
- **O3**: Code generation, debugging, systematic analysis

### Framework Validation
- **Post-completion**: Automatic spec validation using appropriate models
- **Multi-model**: Different models for different validation aspects
- **Context-aware**: Full codebase access for thorough validation

## Compliance Requirements

### Code Quality
- **Type Checking**: mypy --strict compliance
- **Linting**: ruff check with zero errors
- **Formatting**: ruff format applied
- **Testing**: 90%+ coverage minimum

### Security
- **Secrets**: No hardcoded secrets in codebase
- **Dependencies**: Regular security scanning
- **API**: Rate limiting and input validation
- **Database**: Prepared statements and injection protection

### Performance
- **API Response**: < 200ms for standard endpoints
- **Database Queries**: < 100ms for common operations
- **Memory Usage**: < 512MB baseline
- **Startup Time**: < 30 seconds cold start

## Success Criteria

### Functional Requirements
- [ ] Ana router handles all requests using Agno Team pattern
- [ ] Generic agent factory works for any configuration
- [ ] 5-level typification validates hierarchy correctly
- [ ] Agent versioning supports simultaneous variants
- [ ] Monitoring provides real-time visibility

### Non-Functional Requirements
- [ ] System handles 100+ concurrent requests
- [ ] Zero-downtime deployments achieved
- [ ] 99.9% uptime SLA maintained
- [ ] All environments (dev/homolog/prod) operational
- [ ] Security compliance validated

### Business Requirements
- [ ] All PagBank business units supported
- [ ] Portuguese language interface
- [ ] Brazilian banking compliance
- [ ] Production-ready scalability
- [ ] Multi-branch capability enabled

## Validation Framework

### Automatic Spec Validation
1. **Post-Task Completion**: Trigger spec validation automatically
2. **Multi-Model Approach**: Use appropriate model for validation type
3. **Full Context**: Leverage complete codebase access for thorough review
4. **Documentation**: Update specs based on validation findings

### Validation Models
- **T-004 (Typification)**: Gemini 2.5 Pro for complex workflow validation
- **T-005 (Versioning)**: Grok 4 for technical system validation  
- **T-006 (Monitoring)**: O3 for systematic feature validation
- **Infrastructure**: Multi-model approach based on complexity

---

**Note**: This specification serves as the single source of truth for PagBank V2 development. All implementations must be validated against these requirements using the automatic validation framework.