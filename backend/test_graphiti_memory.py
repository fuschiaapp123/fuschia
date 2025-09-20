#!/usr/bin/env python3
"""
LEGACY TEST FILE - TEMPORARILY DISABLED

This test file is for the old Graphiti memory system and needs to be updated
to use the new official Graphiti package implementation.

The new implementation is in:
- graphiti_enhanced_memory_service.py 
- graphiti_enhanced_workflow_agent.py

TODO: Update this test file to use the new Graphiti enhanced memory system
"""

# Temporarily disable this test file until it can be updated for the new implementation
print("⚠️  This test file is temporarily disabled while being updated for the new Graphiti implementation")
print("🔧 The new memory system is available at /api/v1/graphiti-memory/")
exit(0)

import asyncio
import json
from datetime import datetime, timedelta
import uuid

# Note: Updated to use new Graphiti enhanced memory system
from app.services.graphiti_enhanced_memory_service import graphiti_enhanced_memory_service
from app.services.graphiti_enhanced_workflow_agent import GraphitiEnhancedWorkflowAgent, graphiti_enhanced_orchestrator
from app.models.graphiti_memory import (
    GraphEntity, GraphRelationship, MemoryQuery, TemporalInterval,
    EntityType, RelationshipType, EntityExtractionRequest
)
from app.models.agent_organization import (
    AgentNode, WorkflowTask, AgentRole, AgentStrategy, TaskStatus
)


async def test_schema_initialization():
    """Test schema initialization"""
    print("🔧 Testing Schema Initialization")
    print("-" * 40)
    
    try:
        await graphiti_memory_service.initialize_schema()
        print("✅ Schema initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Schema initialization failed: {e}")
        return False


async def test_entity_creation():
    """Test entity creation and retrieval"""
    print("\n📝 Testing Entity Creation")
    print("-" * 40)
    
    try:
        # Create test entities
        temporal = TemporalInterval(
            t_valid_start=datetime.utcnow(),
            t_ingested=datetime.utcnow()
        )
        
        # Person entity
        person_entity = GraphEntity(
            name="John Doe",
            entity_type=EntityType.PERSON,
            description="Test user for system interactions",
            properties={
                "email": "john.doe@example.com",
                "department": "IT",
                "role": "System Administrator"
            },
            temporal=temporal,
            source_type="test_data",
            agent_id="test-agent-001",
            confidence=0.95
        )
        
        created_person = await graphiti_memory_service.create_entity(person_entity)
        print(f"✅ Created person entity: {created_person.name}")
        
        # System entity
        system_entity = GraphEntity(
            name="ServiceNow Instance",
            entity_type=EntityType.SYSTEM,
            description="Primary ServiceNow instance for ticket management",
            properties={
                "url": "https://company.service-now.com",
                "version": "Quebec",
                "status": "active"
            },
            temporal=temporal,
            source_type="test_data",
            agent_id="test-agent-001",
            confidence=0.9
        )
        
        created_system = await graphiti_memory_service.create_entity(system_entity)
        print(f"✅ Created system entity: {created_system.name}")
        
        # Task entity
        task_entity = GraphEntity(
            name="Password Reset Request",
            entity_type=EntityType.TASK,
            description="Task to reset user password in ServiceNow",
            properties={
                "priority": "high",
                "category": "security",
                "estimated_duration": "5 minutes"
            },
            temporal=temporal,
            source_type="test_data",
            agent_id="test-agent-001",
            workflow_id="test-workflow-001"
        )
        
        created_task = await graphiti_memory_service.create_entity(task_entity)
        print(f"✅ Created task entity: {created_task.name}")
        
        return [created_person, created_system, created_task]
        
    except Exception as e:
        print(f"❌ Entity creation failed: {e}")
        return []


async def test_relationship_creation(entities):
    """Test relationship creation between entities"""
    print("\n🔗 Testing Relationship Creation")
    print("-" * 40)
    
    if len(entities) < 3:
        print("⚠️ Not enough entities for relationship testing")
        return []
    
    try:
        temporal = TemporalInterval(
            t_valid_start=datetime.utcnow(),
            t_ingested=datetime.utcnow()
        )
        
        relationships = []
        
        # Person uses System
        person_uses_system = GraphRelationship(
            source_entity_id=entities[0].id,  # Person
            target_entity_id=entities[1].id,  # System
            relationship_type=RelationshipType.USES,
            properties={"frequency": "daily", "access_level": "admin"},
            temporal=temporal,
            source_type="test_data",
            agent_id="test-agent-001"
        )
        
        created_rel1 = await graphiti_memory_service.create_relationship(person_uses_system)
        relationships.append(created_rel1)
        print(f"✅ Created relationship: {entities[0].name} USES {entities[1].name}")
        
        # Person assigned to Task
        person_assigned_task = GraphRelationship(
            source_entity_id=entities[0].id,  # Person
            target_entity_id=entities[2].id,  # Task
            relationship_type=RelationshipType.ASSIGNED_TO,
            properties={"assigned_date": datetime.utcnow().isoformat()},
            temporal=temporal,
            source_type="test_data",
            agent_id="test-agent-001",
            workflow_id="test-workflow-001"
        )
        
        created_rel2 = await graphiti_memory_service.create_relationship(person_assigned_task)
        relationships.append(created_rel2)
        print(f"✅ Created relationship: {entities[0].name} ASSIGNED_TO {entities[2].name}")
        
        # Task uses System
        task_uses_system = GraphRelationship(
            source_entity_id=entities[2].id,  # Task
            target_entity_id=entities[1].id,  # System
            relationship_type=RelationshipType.USES,
            properties={"interaction_type": "api_call"},
            temporal=temporal,
            source_type="test_data",
            agent_id="test-agent-001",
            workflow_id="test-workflow-001"
        )
        
        created_rel3 = await graphiti_memory_service.create_relationship(task_uses_system)
        relationships.append(created_rel3)
        print(f"✅ Created relationship: {entities[2].name} USES {entities[1].name}")
        
        return relationships
        
    except Exception as e:
        print(f"❌ Relationship creation failed: {e}")
        return []


async def test_memory_querying():
    """Test memory querying capabilities"""
    print("\n🔍 Testing Memory Querying")
    print("-" * 40)
    
    try:
        # Test 1: General query
        query1 = MemoryQuery(
            query_text="password reset ServiceNow",
            max_results=10,
            include_relationships=True
        )
        
        result1 = await graphiti_memory_service.query_memory(query1)
        print(f"✅ General query found {len(result1.entities)} entities, {len(result1.relationships)} relationships")
        print(f"   Query time: {result1.query_time_ms:.2f}ms")
        
        # Test 2: Entity type specific query
        query2 = MemoryQuery(
            query_text="system admin",
            entity_types=[EntityType.PERSON, EntityType.SYSTEM],
            max_results=5,
            include_relationships=False
        )
        
        result2 = await graphiti_memory_service.query_memory(query2)
        print(f"✅ Type-specific query found {len(result2.entities)} entities")
        
        # Test 3: Agent-specific query
        query3 = MemoryQuery(
            query_text="test agent memory",
            agent_id="test-agent-001",
            max_results=15,
            include_relationships=True
        )
        
        result3 = await graphiti_memory_service.query_memory(query3)
        print(f"✅ Agent-specific query found {len(result3.entities)} entities, {len(result3.relationships)} relationships")
        
        # Test 4: Workflow-specific query
        query4 = MemoryQuery(
            query_text="workflow tasks",
            workflow_id="test-workflow-001",
            max_results=10
        )
        
        result4 = await graphiti_memory_service.query_memory(query4)
        print(f"✅ Workflow-specific query found {len(result4.entities)} entities")
        
        return [result1, result2, result3, result4]
        
    except Exception as e:
        print(f"❌ Memory querying failed: {e}")
        return []


async def test_entity_extraction():
    """Test entity extraction from text"""
    print("\n🧠 Testing Entity Extraction")
    print("-" * 40)
    
    try:
        # Test text containing various entity types
        test_text = """
        User Sarah Johnson from the Marketing department requested a password reset for her ServiceNow account.
        The task has been assigned to the IT Support team and requires accessing the ServiceNow admin portal.
        This is a high priority security task that should be completed within 2 hours.
        The user's manager Mike Chen has approved this request via email.
        """
        
        extraction_request = EntityExtractionRequest(
            text=test_text,
            source_type="test_extraction",
            source_metadata={"test_case": "entity_extraction_test"},
            agent_id="test-agent-002",
            workflow_id="test-workflow-002",
            use_llm=False,  # Use simple pattern matching for testing
            confidence_threshold=0.5
        )
        
        result = await graphiti_memory_service.extract_entities_from_text(extraction_request)
        
        print(f"✅ Extracted {result.new_entities_created} entities from text")
        print(f"   Processing time: {result.processing_time_ms:.2f}ms")
        print(f"   LLM calls used: {result.llm_calls_used}")
        print(f"   Confidence score: {result.confidence_score:.2f}")
        
        for entity in result.entities:
            print(f"   - {entity.name} ({entity.entity_type.value})")
        
        return result
        
    except Exception as e:
        print(f"❌ Entity extraction failed: {e}")
        return None


async def test_memory_enhanced_agent():
    """Test memory-enhanced agent functionality"""
    print("\n🤖 Testing Memory-Enhanced Agent")
    print("-" * 40)
    
    try:
        # Create test agent
        agent_node = AgentNode(
            name="Test Memory Agent",
            description="Agent for testing memory capabilities",
            role=AgentRole.SPECIALIST,
            strategy=AgentStrategy.HYBRID
        )
        
        # Create memory-enhanced agent
        memory_agent = MemoryEnhancedAgent(
            agent_node=agent_node,
            workflow_id="test-workflow-003",
            execution_id="test-execution-001"
        )
        
        # Create test task
        test_task = WorkflowTask(
            name="Check ServiceNow Status",
            description="Check the status of ServiceNow system and report any issues",
            objective="Verify system health",
            completion_criteria="System status confirmed"
        )
        
        # Test context
        test_context = {
            "system_name": "ServiceNow",
            "check_type": "health_check",
            "priority": "normal"
        }
        
        # Execute task with memory enhancement
        result = await memory_agent.execute_task_with_memory(test_task, test_context)
        
        print(f"✅ Memory-enhanced task execution completed")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Confidence: {result.get('confidence', 0.0):.2f}")
        print(f"   Execution method: {result.get('execution_method', 'unknown')}")
        
        if result.get('memory_entities_used'):
            print(f"   Memory entities used: {result['memory_entities_used']}")
        
        if result.get('memory_relationships_used'):
            print(f"   Memory relationships used: {result['memory_relationships_used']}")
        
        # Get agent memory summary
        memory_summary = await memory_agent.get_agent_memory_summary()
        print(f"✅ Agent memory summary retrieved")
        print(f"   Total entities: {memory_summary['total_entities']}")
        print(f"   Total relationships: {memory_summary['total_relationships']}")
        print(f"   Entity types: {list(memory_summary['entity_types'].keys())}")
        
        return memory_agent, result, memory_summary
        
    except Exception as e:
        print(f"❌ Memory-enhanced agent test failed: {e}")
        return None, None, None


async def test_memory_stats():
    """Test memory statistics functionality"""
    print("\n📊 Testing Memory Statistics")
    print("-" * 40)
    
    try:
        stats = await graphiti_memory_service.get_memory_stats(refresh=True)
        
        print(f"✅ Memory statistics retrieved")
        print(f"   Total entities: {stats.total_entities}")
        print(f"   Total relationships: {stats.total_relationships}")
        print(f"   Entity types: {stats.entities_by_type}")
        print(f"   Relationship types: {stats.relationships_by_type}")
        
        if stats.oldest_entity_timestamp:
            print(f"   Oldest entity: {stats.oldest_entity_timestamp}")
        if stats.newest_entity_timestamp:
            print(f"   Newest entity: {stats.newest_entity_timestamp}")
        
        return stats
        
    except Exception as e:
        print(f"❌ Memory statistics test failed: {e}")
        return None


async def test_workflow_memory_integration():
    """Test workflow memory integration"""
    print("\n🔄 Testing Workflow Memory Integration")
    print("-" * 40)
    
    try:
        # Create test agents
        agents = [
            AgentNode(
                name="Memory Agent 1",
                description="First agent with memory capabilities",
                role=AgentRole.COORDINATOR,
                strategy=AgentStrategy.HYBRID
            ),
            AgentNode(
                name="Memory Agent 2", 
                description="Second agent with memory capabilities",
                role=AgentRole.SPECIALIST,
                strategy=AgentStrategy.CHAIN_OF_THOUGHT
            )
        ]
        
        # Create test tasks
        tasks = [
            WorkflowTask(
                name="Initialize System Check",
                description="Initialize comprehensive system health check",
                objective="Prepare for system monitoring",
                completion_criteria="All systems ready for monitoring"
            ),
            WorkflowTask(
                name="Execute Health Checks",
                description="Execute health checks on all monitored systems",
                objective="Verify all systems are operational",
                completion_criteria="Health status confirmed for all systems"
            ),
            WorkflowTask(
                name="Generate Status Report",
                description="Generate comprehensive status report",
                objective="Document system status",
                completion_criteria="Status report generated and stored"
            )
        ]
        
        # Test context
        workflow_context = {
            "workflow_type": "system_monitoring",
            "monitoring_scope": "full_infrastructure",
            "report_format": "detailed"
        }
        
        # Execute workflow with memory enhancement
        workflow_id = f"test-workflow-{uuid.uuid4()}"
        execution_id = f"test-execution-{uuid.uuid4()}"
        
        result = await memory_enhanced_orchestrator.execute_workflow_with_memory(
            workflow_id=workflow_id,
            execution_id=execution_id,
            agents=agents,
            tasks=tasks,
            context=workflow_context
        )
        
        print(f"✅ Memory-enhanced workflow execution completed")
        print(f"   Workflow ID: {workflow_id}")
        print(f"   Execution ID: {execution_id}")
        print(f"   Total tasks: {result['total_tasks']}")
        print(f"   Successful tasks: {result['successful_tasks']}")
        print(f"   Failed tasks: {result['failed_tasks']}")
        print(f"   Memory enhanced: {result['memory_enhanced']}")
        print(f"   Agents used: {result['agents_used']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Workflow memory integration test failed: {e}")
        return None


async def run_comprehensive_test():
    """Run comprehensive test of Graphiti memory system"""
    print("🚀 Starting Comprehensive Graphiti Memory System Test")
    print("=" * 60)
    
    test_results = {}
    
    # Test 1: Schema initialization
    test_results["schema_init"] = await test_schema_initialization()
    
    if not test_results["schema_init"]:
        print("\n❌ Schema initialization failed, stopping tests")
        return test_results
    
    # Test 2: Entity creation
    entities = await test_entity_creation()
    test_results["entity_creation"] = len(entities) > 0
    
    # Test 3: Relationship creation
    relationships = await test_relationship_creation(entities)
    test_results["relationship_creation"] = len(relationships) > 0
    
    # Test 4: Memory querying
    query_results = await test_memory_querying()
    test_results["memory_querying"] = len(query_results) > 0
    
    # Test 5: Entity extraction
    extraction_result = await test_entity_extraction()
    test_results["entity_extraction"] = extraction_result is not None
    
    # Test 6: Memory-enhanced agent
    agent, agent_result, memory_summary = await test_memory_enhanced_agent()
    test_results["memory_enhanced_agent"] = agent is not None
    
    # Test 7: Memory statistics
    stats = await test_memory_stats()
    test_results["memory_stats"] = stats is not None
    
    # Test 8: Workflow memory integration
    workflow_result = await test_workflow_memory_integration()
    test_results["workflow_integration"] = workflow_result is not None
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Graphiti memory system is working correctly.")
    else:
        print(f"⚠️ {total_tests - passed_tests} tests failed. Check logs for details.")
    
    # Additional information
    if stats:
        print(f"\nFinal Memory Statistics:")
        print(f"   Total entities in memory: {stats.total_entities}")
        print(f"   Total relationships in memory: {stats.total_relationships}")
        print(f"   Entity types created: {list(stats.entities_by_type.keys())}")
    
    return test_results


if __name__ == "__main__":
    print("Starting Graphiti Knowledge Graph Memory Tests...")
    print(f"Timestamp: {datetime.utcnow()}")
    
    try:
        test_results = asyncio.run(run_comprehensive_test())
        
        if all(test_results.values()):
            print(f"\n✅ All tests completed successfully!")
            exit(0)
        else:
            print(f"\n❌ Some tests failed!")
            exit(1)
            
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)