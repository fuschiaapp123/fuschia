# Fuschia Intelligent Automation Platform - Claude Build Context

## Project Overview
Fuschia is an enterprise intelligent automation platform that combines multi-agent AI workflows with graph-based knowledge management. It's designed as a unified, no-code SaaS platform for large and medium enterprises.

## Architecture
- **Backend**: Python FastAPI with Neo4j graph database
- **Frontend**: React TypeScript with Tailwind CSS and ReactFlow
- **Database**: Neo4j for knowledge graphs (1M+ nodes support)
- **Deployment**: Docker containerization, multi-tenant SaaS

## Key Technologies
- **Backend**: FastAPI, Neo4j Python driver, Pydantic, JWT authentication
- **Frontend**: React, TypeScript, ReactFlow, D3.js, Tailwind CSS
- **AI/ML**: LangGraph for multi-agent workflows
- **Integrations**: ServiceNow, Salesforce, SAP, Workday APIs

## Build Commands
Run lint and typecheck with:
- Backend: `ruff check` and `mypy .`
- Frontend: `npm run lint` and `npm run typecheck`

## Performance Requirements
- API responses < 200ms
- Support 1,000+ concurrent users
- Handle 1M+ graph nodes
- Real-time WebSocket updates

## Security Features
- AES-256 encryption
- Multi-factor authentication
- SOC 2 compliance requirements
- JWT token-based authentication

## Core Modules
1. **Knowledge Management**: Graph visualization, data import/export
2. **Workflow Management**: Visual process design with ReactFlow
3. **Agent Management**: Multi-agent system configuration
4. **Runtime Execution**: Real-time process orchestration

## Development Workflow
1. Follow the 7-step build commands in `claude-build-commands.md`
2. Each command corresponds to a major development phase
3. Maintain enterprise-grade code quality and security standards
4. Use sample data for testing and development

## Testing Strategy
- Use provided sample data for development testing
- Focus on performance benchmarks (response times, concurrent users)
- Validate graph database operations with large datasets
- Test real-time features with WebSocket connections