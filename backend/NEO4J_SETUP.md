# Neo4j Setup for Graphiti Memory Enhancement

## Requirements

The Graphiti temporal knowledge graph memory system requires:
- **Neo4j 5.23.0+** with vector similarity functions
- **APOC plugin** for advanced graph operations
- **Proper authentication** configured

## Quick Setup with Docker

### Option 1: Basic Neo4j with APOC (Recommended for Development)

```bash
docker run \
  --name fuschia-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_PLUGINS='["apoc"]' \
  -e NEO4J_apoc_export_file_enabled=true \
  -e NEO4J_apoc_import_file_enabled=true \
  -e NEO4J_apoc_import_file_use__neo4j__config=true \
  -v fuschia-neo4j-data:/data \
  neo4j:5.23
```

### Option 2: Neo4j with Vector Extensions (For Production)

```bash
docker run \
  --name fuschia-neo4j-vector \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -e NEO4J_PLUGINS='["apoc", "graph-data-science"]' \
  -e NEO4J_apoc_export_file_enabled=true \
  -e NEO4J_apoc_import_file_enabled=true \
  -e NEO4J_dbms_security_procedures_unrestricted=apoc.*,gds.* \
  -v fuschia-neo4j-data:/data \
  neo4j:5.23-enterprise
```

## Configuration

Update your `.env` file or environment variables:

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j  
NEO4J_PASSWORD=password
```

## Verification

1. **Web Interface**: Visit http://localhost:7474
2. **Login**: Use `neo4j` / `password`
3. **Test Vector Functions**:
   ```cypher
   RETURN vector.similarity.cosine([1, 2, 3], [4, 5, 6]) AS similarity
   ```

## Troubleshooting

### Error: "Unknown function 'vector.similarity.cosine'"

**Solution**: Ensure you're using Neo4j 5.23+ with proper plugins:
```bash
# Check Neo4j version
docker exec fuschia-neo4j neo4j version

# Check installed plugins
docker exec fuschia-neo4j ls /var/lib/neo4j/plugins/
```

### Error: "ServiceUnavailable"

**Solution**: Neo4j is not running
```bash
# Check if container is running
docker ps | grep neo4j

# Start the container
docker start fuschia-neo4j
```

### Error: "AuthError"

**Solution**: Check credentials in your configuration
```bash
# Update environment variables
export NEO4J_USERNAME=neo4j
export NEO4J_PASSWORD=password
```

## Memory Enhancement Features

With proper Neo4j setup, the Fuschia platform provides:

- ✅ **Episodic Memory**: Records all workflow conversations and agent interactions
- ✅ **Entity Extraction**: Automatically identifies and links entities from episodes  
- ✅ **Semantic Relationships**: Builds knowledge graphs of entity relationships
- ✅ **Community Detection**: Groups strongly connected entities for better insights
- ✅ **Temporal Search**: Query memory with time-based constraints
- ✅ **3-Tuple Results**: Returns (semantic_edges, entity_nodes, community_nodes)

## Graceful Degradation

If Neo4j is not available, the Fuschia platform will:
- ✅ Continue to operate normally
- ⚠️ Log warnings about disabled memory features
- ⚠️ Skip episode recording (no errors thrown)
- ⚠️ Return empty results for memory searches

This ensures development can continue even without proper Neo4j setup.