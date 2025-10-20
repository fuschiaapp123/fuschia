  How Graphiti-Based Knowledge Graph Memory Works in 
  Fuschia

  Overview

  Fuschia implements temporal knowledge graph memory using
  the https://github.com/getzep/graphiti library, which
  provides episodic memory, semantic entity extraction, and
   relationship mapping for AI agents. This enhances
  workflow execution with long-term memory capabilities.

  Architecture Components

  1. GraphitiEnhancedMemoryService 
  (graphiti_enhanced_memory_service.py)

  This is the core service that interfaces with Graphiti
  and Neo4j.

  Key Features:
  - Episodic Memory: Records workflow events as temporal
  episodes
  - Semantic Graph: Automatically extracts entities and
  relationships
  - Community Detection: Groups strongly connected entities
  - Temporal Search: Time-aware memory retrieval

  Episode Types Recorded:
  - workflow_start: Workflow initiation
  - task_execution: Each task execution with results
  - agent_thought: Agent reasoning steps
  - user_interaction: User inputs and responses
  - workflow_end: Workflow completion

  2. Memory Recording Flow

  When a workflow executes with memory enhancement:

  1. Workflow Start
     └─> Record workflow_start episode
         └─> Graphiti extracts entities (user, workflow 
  name, context)

  2. Task Execution
     ├─> Record agent_thought (task planning)
     ├─> Search memory for relevant knowledge
     ├─> Execute task with memory-enhanced context
     └─> Record task_execution episode
         └─> Graphiti extracts entities (task name, agent, 
  results)

  3. Workflow Completion
     └─> Record workflow_end episode
         └─> Graphiti creates semantic relationships

  3. Graphiti's Automatic Processing

  For each episode, Graphiti automatically:

  # From add_episode() call:
  episode_result = await graphiti_client.add_episode(
      name=f"task_execution_{uuid}",
      episode_body=content_with_metadata,
      reference_time=timestamp,
      source=EpisodeType.message,
      group_id=workflow_id  # Partition by workflow
  )

  # Graphiti automatically:
  # 1. Extracts entities (people, products, concepts)
  # 2. Identifies relationships between entities
  # 3. Creates semantic edges in the knowledge graph
  # 4. Assigns entities to communities
  # 5. Enables temporal search

  Example Entity Extraction:
  Episode: "Task 'Send Offer Letter' completed. Agent:
  HR_Agent. 
           Sent offer to John Doe for Software Engineer 
  position at $120k."

  Graphiti Extracts:
  ├─ Entities:
  │  ├─ Person: John Doe
  │  ├─ Role: Software Engineer
  │  ├─ Agent: HR_Agent
  │  └─ Amount: $120k
  └─ Relationships:
     ├─ HR_Agent → executed → Send Offer Letter
     ├─ Send Offer Letter → targets → John Doe
     └─ John Doe → offered → Software Engineer

  4. Memory Search During Execution

  When agents execute tasks:

  # Step 1: Search memory
  memory_result = await graphiti_client.search(
      query="previous offer letters sent",
      num_results=10,
      start_time=datetime.now() - timedelta(days=30),
      end_time=datetime.now()
  )

  # Returns:
  # - semantic_edges: Relationships found
  # - entity_nodes: Related entities
  # - community_nodes: Related knowledge clusters

  # Step 2: Enhance context
  enhanced_context = {
      **original_context,
      "memory_context": {
          "related_tasks": [...],
          "previous_decisions": [...],
          "known_entities": [...]
      }
  }

  # Step 3: Agent uses enhanced context
  result = await agent.execute_task(task, enhanced_context)

  5. Integration with Workflow Orchestrator

  The workflow orchestrator can enable memory enhancement:

  # In workflow_orchestrator.py:
  if execution.use_memory_enhancement:
      # Use Graphiti-enhanced execution
      await
  self._execute_workflow_with_graphiti_memory(execution)
  else:
      # Standard execution without memory
      await self._execute_workflow(execution)

  Data Storage in Neo4j

  Graphiti stores data in Neo4j with this structure:

  // Nodes
  (:Episode {uuid, name, content, timestamp, group_id})
  (:Entity {uuid, name, type, summary})
  (:Community {uuid, name, members[]})

  // Relationships
  (:Episode)-[:HAS_ENTITY]->(:Entity)
  (:Entity)-[:RELATES_TO {fact}]->(:Entity)
  (:Entity)-[:MEMBER_OF]->(:Community)

  Benefits for Fuschia

  1. Learning from Past Executions
    - Agents remember how similar tasks were handled
    - Avoid repeating mistakes
    - Reuse successful patterns
  2. Cross-Workflow Knowledge
    - Knowledge from one workflow can inform another
    - Example: Employee onboarding learns from previous
  hires
  3. Temporal Awareness
    - "What happened last week?"
    - "How did we handle this 3 months ago?"
  4. Entity Recognition
    - Remember customers, employees, products
    - Track relationships over time
  5. Community-Based Insights
    - Discover related knowledge clusters
    - "HR tasks" community, "Finance tasks" community

  Configuration

  To enable memory enhancement:

  # When creating workflow execution
  execution = workflow_execution_service.create_execution(
      workflow_template_id=template_id,
      initiated_by=user_id,
      execution_context={
          "use_memory_enhancement": True  # Enable Graphiti
      }
  )

  Requirements

  - Neo4j 5.23+ with APOC plugin
  - Vector similarity functions enabled
  - Graphiti library installed (graphiti-core)

  Example Use Case

  Scenario: Employee Onboarding Workflow

  1st Execution (New Hire: Alice):
     └─> Graphiti learns: IT setup took 2 days, manager is
  Bob

  2nd Execution (New Hire: Charlie):
     ├─> Search: "IT setup for new employees"
     ├─> Find: Previous Alice onboarding (2 days)
     ├─> Agent: "Plan 2 days for IT setup based on history"
     └─> Use: Bob as reference for manager assignment
  pattern

  Summary

  Fuschia's Graphiti integration provides temporal 
  knowledge graph memory that:
  - Records every workflow event as episodes
  - Extracts entities and relationships automatically
  - Searches memory to enhance agent decision-making
  - Learns from past executions
  - Scales with Neo4j's graph database

  This creates a continuously learning system where
  workflows become more intelligent over time!
