# Fuschia Intelligent Automation Platform - Build Commands

## Step 1: Project Foundation and Dependencies Setup

```xml
<prompt>
<role>Advanced Python and JavaScript full-stack engineer specializing in enterprise automation platforms</role>
<content>Set up the foundational project structure for Fuschia, an intelligent automation platform. Initialize both backend (Python/FastAPI) and frontend (React/TypeScript) applications with proper project structure, package management, and essential dependencies.</content>
<instructions>
1. Create a monorepo structure with separate backend and frontend directories
2. Initialize Python backend with FastAPI, Neo4j driver, and authentication libraries
3. Initialize React frontend with TypeScript, Tailwind CSS, ReactFlow, and state management
4. Set up environment configuration files for development and production
5. Create basic project configuration files (package.json, requirements.txt, etc.)
6. Ensure all dependencies align with enterprise-grade security and performance requirements
7. Set up basic Docker configuration for containerization
</instructions>
</prompt>
```

## Step 2: Backend API Foundation and Neo4j Integration

```xml
<prompt>
<role>Senior backend engineer with expertise in FastAPI, Neo4j graph databases, and enterprise API design</role>
<content>Build the core backend API structure with Neo4j graph database integration for the Fuschia automation platform. Implement authentication, data models, and basic CRUD operations for knowledge graph management.</content>
<instructions>
1. Create FastAPI application structure with proper routing and middleware
2. Implement Neo4j database connection and configuration management
3. Set up authentication system with JWT tokens and user management
4. Create data models for knowledge graphs, workflows, and agents using Pydantic
5. Implement basic CRUD operations for knowledge graph nodes and relationships
6. Add API endpoints for user registration, login, and profile management
7. Create database initialization scripts and migration system
8. Implement proper error handling and logging throughout the API
9. Ensure all API responses follow consistent JSON structure with <200ms response times
</instructions>
</prompt>
```

## Step 3: Frontend Core UI and Navigation Framework

```xml
<prompt>
<role>Senior React/TypeScript frontend engineer with expertise in enterprise UI design and data visualization</role>
<content>Build the core frontend application structure with navigation, layout components, and UI framework matching fuschia.io design. Implement the collapsible sidebar navigation and tabbed workspace interface as specified in the PRD.</content>
<instructions>
1. Create React application structure with TypeScript and proper component organization
2. Implement the collapsible left sidebar with four main sections: Knowledge, Workflow, Agents, Settings
3. Build the tabbed workspace interface with chat and dynamic main panel
4. Style components to match fuschia.io website colors and design language
5. Create reusable UI components following enterprise design patterns
6. Implement responsive design for desktop application usage
7. Set up state management for user sessions, navigation state, and application data
8. Create basic routing system for different application sections
9. Implement loading states and error boundaries for robust user experience
</instructions>
</prompt>
```

## Step 4: Knowledge and Workflow Management Modules

```xml
<prompt>
<role>Full-stack engineer specializing in data visualization, workflow design, and graph-based systems</role>
<content>Implement the Knowledge Management and Workflow Management modules for Fuschia. Build interactive graph visualization, workflow canvas with ReactFlow, and data import/export capabilities.</content>
<instructions>
1. Create Knowledge Management module with chat-driven data exploration interface
2. Implement interactive Neo4j graph visualization using D3.js or similar library
3. Build data import functionality for external systems (ServiceNow, Salesforce, SAP, Workday)
4. Create Workflow Management module with ReactFlow-based visual process designer
5. Implement workflow template library with common business process templates
6. Add workflow version control and import/export capabilities
7. Build data validation and quality assessment tools for knowledge graphs
8. Create process storage system with proper metadata management
9. Implement real-time collaboration features for multi-user workflow editing
10. Ensure graph visualization can handle 1M+ nodes as specified in requirements
</instructions>
</prompt>
```

## Step 5: Agent Management and Runtime Execution System

```xml
<prompt>
<role>AI/ML engineer with expertise in multi-agent systems, LangGraph, and process orchestration</role>
<content>Build the Agent Management module and Runtime Execution Environment for Fuschia. Implement multi-agent system design, LangGraph integration, and real-time process orchestration with monitoring capabilities.</content>
<instructions>
1. Create Agent Management module with ReactFlow-based organization chart for agent design
2. Implement agent configuration system with capabilities, specializations, and performance settings
3. Integrate LangGraph for executable multi-agent workflows
4. Build Runtime Execution Environment with real-time process orchestration
5. Create conversational interface for user requests and agent interactions
6. Implement agent assignment and escalation management system
7. Build process monitoring dashboard with live status updates and performance metrics
8. Add agent learning and optimization configuration features
9. Create webhook system for external system integrations
10. Implement WebSocket connections for real-time updates and collaboration
11. Ensure system can handle 1,000+ concurrent users as specified
</instructions>
</prompt>
```

## Step 6: Sample Data Creation and Development Setup

```xml
<prompt>
<role>DevOps engineer and data architect with expertise in test data generation and development environments</role>
<content>Create comprehensive sample data, development environment setup, and testing infrastructure for the Fuschia automation platform. Generate realistic test data for knowledge graphs, workflows, and agent configurations.</content>
<instructions>
1. Create sample knowledge graph data with realistic business entities, relationships, and metadata
2. Generate sample workflow templates covering common business processes (approvals, escalations, data processing)
3. Create sample agent configurations with different specializations and capabilities
4. Build sample user accounts with different roles and permissions for testing
5. Generate sample integration data for ServiceNow, Salesforce, and other enterprise systems
6. Create development environment setup scripts for easy local development
7. Implement data seeding scripts for consistent development and demo environments
8. Create sample API request/response examples for all major endpoints
9. Generate realistic performance test data for load testing with 1M+ graph nodes
10. Document all sample data structures and usage scenarios
</instructions>
</prompt>
```

## Step 7: Comprehensive Documentation and User Guide

```xml
<prompt>
<role>Technical documentation specialist and developer advocate with expertise in enterprise software onboarding</role>
<content>Create comprehensive README documentation and user guides for the Fuschia automation platform. Provide complete instructions for setup, development, deployment, and usage from zero to production-ready state.</content>
<instructions>
1. Create detailed README.md with project overview, architecture, and quick start guide
2. Document complete installation and setup process for all dependencies (Neo4j, Python, Node.js)
3. Provide step-by-step development environment setup instructions
4. Create API documentation with endpoint descriptions, request/response examples, and authentication
5. Document all configuration options and environment variables
6. Create user guides for each module: Knowledge, Workflow, Agents, and Settings
7. Provide troubleshooting guide for common issues and solutions
8. Document deployment procedures for development, staging, and production environments
9. Create developer onboarding guide with code structure, conventions, and contribution guidelines
10. Include security best practices and compliance information
11. Document performance benchmarks and scalability considerations
12. Create sample usage scenarios and workflow examples for end users
</instructions>
</prompt>
```