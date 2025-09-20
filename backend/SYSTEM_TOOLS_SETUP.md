# System Tools Setup Guide

This document explains how to set up and configure the System Tools for workflow agents, including RAG knowledge base access and MCP integration.

## Overview

The System Tools service provides three categories of tools to enhance workflow agent capabilities:

1. **RAG Knowledge Tools** - Access knowledge bases stored in AWS S3
2. **MCP Integration Tools** - Connect to Model Context Protocol services
3. **Context Enhancement Tools** - Provide additional context for tasks

## Prerequisites

### Required Python Packages

```bash
pip install boto3 langchain faiss-cpu openai httpx PyPDF2 python-docx
```

### Environment Variables

Create a `.env` file or set these environment variables:

```env
# AWS S3 Configuration for RAG Knowledge Base
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
KNOWLEDGE_S3_BUCKET=fuschia-knowledge-base
KNOWLEDGE_S3_PREFIX=documents/

# OpenAI for Embeddings (RAG)
OPENAI_API_KEY=your_openai_api_key

# MCP Service Endpoints (optional)
MCP_KNOWLEDGE_ENDPOINT=http://localhost:8001/mcp
MCP_TOOLS_ENDPOINT=http://localhost:8002/mcp
MCP_CONTEXT_ENDPOINT=http://localhost:8003/mcp
```

## Setting up RAG Knowledge Base

### 1. Create S3 Bucket

```bash
aws s3 mb s3://fuschia-knowledge-base
```

### 2. Upload Documents

Upload your PDF, DOCX, and TXT files to the S3 bucket:

```bash
aws s3 cp ./documents/ s3://fuschia-knowledge-base/documents/ --recursive
```

Supported file formats:
- PDF files (`.pdf`)
- Microsoft Word documents (`.docx`)
- Plain text files (`.txt`)

### 3. Directory Structure

```
s3://fuschia-knowledge-base/
└── documents/
    ├── policy-manual.pdf
    ├── procedures-guide.docx
    ├── troubleshooting.txt
    └── reference-materials/
        ├── api-documentation.pdf
        └── system-architecture.docx
```

## Available System Tools

### RAG Knowledge Search

**Tool Name:** `rag_knowledge_search`

**Description:** Search through knowledge base of documents stored in AWS S3 using RAG

**Parameters:**
- `query` (string): Search query to find relevant information
- `max_results` (int, optional): Maximum number of results to return (default: 5)

**Example Usage in Workflow:**
```
Agent can call: rag_knowledge_search("How to handle system errors")
```

### MCP Service Call

**Tool Name:** `mcp_service_call`

**Description:** Call external MCP services to enhance context and capabilities

**Parameters:**
- `service` (string): MCP service name ('knowledge', 'tools', 'context')
- `method` (string): Method to call on the MCP service
- `parameters` (dict, optional): Parameters to pass to the method

**Example Usage in Workflow:**
```
Agent can call: mcp_service_call("knowledge", "search", {"query": "user authentication"})
```

### Context Enhancement

**Tool Name:** `enhance_context`

**Description:** Enhance task context with additional relevant information

**Parameters:**
- `task_description` (string): Description of the task
- `current_context` (dict, optional): Current context information

**Example Usage in Workflow:**
```
Agent can call: enhance_context("Deploy application to production environment")
```

## Integration with Workflow Agents

The system tools are automatically available to all workflow execution agents. When a workflow runs, agents have access to:

1. **Workflow Tools** - Task-specific tools defined in the workflow
2. **Human-in-the-Loop Tools** - User interaction tools (questions, approvals, information requests)
3. **System Tools** - RAG knowledge, MCP integration, context enhancement
4. **Tools Registry** - Custom tools registered in the tools registry

## Example Workflow Scenario

```
User: "I need help troubleshooting a database connection issue"

Agent Flow:
1. Use enhance_context() to analyze the task complexity and requirements
2. Use rag_knowledge_search() to find relevant troubleshooting documentation
3. Use ask_user_question() to gather specific error details
4. Use appropriate workflow tools to implement the solution
5. Use complete_task() to mark the task as finished
```

## Monitoring and Logging

System tools provide comprehensive logging:

```python
# View system tools logs
tail -f logs/system_tools.log

# Check tool initialization status
curl http://localhost:8000/api/v1/system-tools/status

# View available tools
curl http://localhost:8000/api/v1/system-tools/list
```

## Troubleshooting

### RAG Knowledge Tool Issues

1. **"Knowledge base not available"**
   - Check AWS credentials and S3 bucket permissions
   - Verify OPENAI_API_KEY is set correctly
   - Ensure documents exist in the specified S3 bucket

2. **"No relevant information found"**
   - Try rephrasing the search query
   - Check that documents were processed correctly
   - Verify vector store was built successfully

### MCP Integration Issues

1. **"MCP service not available"**
   - Check MCP service endpoints are running
   - Verify network connectivity to MCP services
   - Review MCP service logs for errors

### Performance Optimization

1. **Vector Store Caching**
   - Vector stores are cached locally in `./knowledge_cache/`
   - Rebuild cache by deleting the directory and restarting

2. **Document Processing**
   - Large documents are chunked for better search performance
   - Adjust chunk size in `system_tools_service.py` if needed

## Advanced Configuration

### Custom System Tools

To add custom system tools:

```python
from app.services.system_tools_service import BaseSystemTool, SystemToolMetadata, SystemToolCategory

class CustomTool(BaseSystemTool):
    def __init__(self):
        super().__init__(SystemToolMetadata(
            name="custom_tool",
            category=SystemToolCategory.DATA_ACCESS,
            description="Custom tool description",
            version="1.0.0"
        ))
    
    async def initialize(self) -> bool:
        # Initialize your tool
        return True
    
    async def execute(self, *args, **kwargs) -> str:
        # Implement your tool logic
        return "Tool result"

# Register the tool
from app.services.system_tools_service import system_tools_service
await system_tools_service.register_tool(CustomTool())
```

### Tool Categories

Available categories:
- `RAG_KNOWLEDGE` - Knowledge base and document search
- `MCP_INTEGRATION` - Model Context Protocol services
- `CONTEXT_ENHANCEMENT` - Task context enhancement
- `DATA_ACCESS` - Data retrieval and manipulation
- `EXTERNAL_SERVICES` - External API and service integration