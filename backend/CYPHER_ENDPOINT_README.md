# Cypher Query Endpoint

## Overview

The Cypher query endpoint allows authenticated users to execute raw Cypher queries against the Neo4j database. This endpoint is designed to support the Neo4j Browser functionality in the frontend.

## Endpoint Details

- **URL**: `/api/v1/knowledge/cypher`
- **Method**: `POST`
- **Authentication**: Required (JWT token)
- **Content-Type**: `application/json`

## Request Format

```json
{
  "query": "MATCH (n) RETURN n LIMIT 10"
}
```

## Response Format

```json
{
  "nodes": [
    {
      "id": "123",
      "element_id": "4:abc123:0",
      "labels": ["KnowledgeNode"],
      "properties": {
        "name": "Example Node",
        "type": "entity",
        "description": "An example node"
      }
    }
  ],
  "relationships": [
    {
      "id": "456",
      "element_id": "5:def456:0",
      "type": "RELATED",
      "start_node": "123",
      "end_node": "789",
      "properties": {
        "weight": 1.0
      }
    }
  ],
  "summary": {
    "total_records": 1,
    "nodes_count": 1,
    "relationships_count": 1,
    "query": "MATCH (n) RETURN n LIMIT 10"
  },
  "raw_results": [
    {
      "n": {
        "id": 123,
        "labels": ["KnowledgeNode"],
        "properties": {...}
      }
    }
  ]
}
```

## Error Handling

The endpoint handles errors gracefully:

- **400 Bad Request**: Invalid Cypher query syntax
- **401 Unauthorized**: Missing or invalid authentication
- **500 Internal Server Error**: Database connection issues or unexpected errors

## Example Usage

### Using curl:

```bash
curl -X POST "http://localhost:8000/api/v1/knowledge/cypher" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "MATCH (n:KnowledgeNode) RETURN n LIMIT 5"
  }'
```

### Using Python requests:

```python
import requests

url = "http://localhost:8000/api/v1/knowledge/cypher"
headers = {
    "Authorization": "Bearer YOUR_JWT_TOKEN",
    "Content-Type": "application/json"
}
data = {
    "query": "MATCH (n:KnowledgeNode) RETURN n LIMIT 5"
}

response = requests.post(url, headers=headers, json=data)
result = response.json()
```

## Security Considerations

1. **Authentication Required**: All requests must include a valid JWT token
2. **Read-Only Recommended**: For security, consider limiting to read-only queries in production
3. **Query Validation**: The endpoint validates query syntax before execution
4. **Rate Limiting**: Consider implementing rate limiting for production use

## Frontend Integration

This endpoint is specifically designed to work with the Neo4j Browser component in the frontend. The response format matches the expected structure for graph visualization:

- `nodes`: Array of node objects with id, labels, and properties
- `relationships`: Array of relationship objects with type, start/end nodes, and properties
- `summary`: Metadata about the query execution
- `raw_results`: Raw Neo4j query results for debugging

## Common Queries

### Get all nodes:
```cypher
MATCH (n) RETURN n LIMIT 100
```

### Get all relationships:
```cypher
MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 100
```

### Get nodes and their relationships:
```cypher
MATCH (n:KnowledgeNode)-[r:RELATED]->(m:KnowledgeNode) 
RETURN n, r, m
```

### Search nodes by name:
```cypher
MATCH (n:KnowledgeNode) 
WHERE n.name CONTAINS 'search_term' 
RETURN n
```