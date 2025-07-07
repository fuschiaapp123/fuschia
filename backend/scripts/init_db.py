#!/usr/bin/env python3
"""
Database initialization script for Fuschia
Creates sample data for development and testing
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.neo4j import neo4j_driver
from app.services.user_service import UserService
from app.services.knowledge_service import KnowledgeService
from app.models.user import UserCreate, UserRole
from app.models.knowledge import KnowledgeNodeCreate, KnowledgeRelationshipCreate, NodeType, RelationshipType


async def create_sample_users():
    """Create sample users for testing"""
    user_service = UserService()
    
    sample_users = [
        {
            "email": "admin@fuschia.io",
            "full_name": "System Administrator",
            "password": "admin123",
            "role": UserRole.ADMIN
        },
        {
            "email": "manager@fuschia.io",
            "full_name": "Process Manager",
            "password": "manager123",
            "role": UserRole.MANAGER
        },
        {
            "email": "analyst@fuschia.io",
            "full_name": "Business Analyst",
            "password": "analyst123",
            "role": UserRole.ANALYST
        },
        {
            "email": "user@fuschia.io",
            "full_name": "End User",
            "password": "user123",
            "role": UserRole.USER
        }
    ]
    
    created_users = []
    for user_data in sample_users:
        try:
            user = await user_service.create_user(UserCreate(**user_data))
            created_users.append(user)
            print(f"Created user: {user.email}")
        except Exception as e:
            print(f"Error creating user {user_data['email']}: {e}")
    
    return created_users


async def create_sample_knowledge_graph():
    """Create sample knowledge graph data"""
    knowledge_service = KnowledgeService()
    admin_user_id = "admin-user-id"  # This would be the actual admin user ID
    
    # Sample departments
    departments = [
        {"name": "Human Resources", "description": "Manages employee lifecycle and policies"},
        {"name": "IT Operations", "description": "Manages technology infrastructure and support"},
        {"name": "Finance", "description": "Handles financial planning and accounting"},
        {"name": "Sales", "description": "Manages customer acquisition and revenue"},
        {"name": "Customer Support", "description": "Provides customer service and technical support"}
    ]
    
    # Sample systems
    systems = [
        {"name": "ServiceNow", "description": "IT Service Management platform"},
        {"name": "Salesforce", "description": "Customer Relationship Management system"},
        {"name": "SAP", "description": "Enterprise Resource Planning system"},
        {"name": "Workday", "description": "Human Capital Management system"},
        {"name": "Slack", "description": "Communication and collaboration platform"}
    ]
    
    # Sample processes
    processes = [
        {"name": "Employee Onboarding", "description": "Process for new hire integration"},
        {"name": "Incident Management", "description": "IT incident resolution workflow"},
        {"name": "Invoice Processing", "description": "Accounts payable automation"},
        {"name": "Lead Qualification", "description": "Sales lead evaluation process"},
        {"name": "Customer Escalation", "description": "Support ticket escalation workflow"}
    ]
    
    created_nodes = []
    
    # Create department nodes
    for dept in departments:
        node = await knowledge_service.create_node(
            KnowledgeNodeCreate(
                name=dept["name"],
                type=NodeType.DEPARTMENT,
                description=dept["description"],
                properties={"category": "organizational"}
            ),
            admin_user_id
        )
        created_nodes.append(node)
        print(f"Created department node: {node.name}")
    
    # Create system nodes
    for system in systems:
        node = await knowledge_service.create_node(
            KnowledgeNodeCreate(
                name=system["name"],
                type=NodeType.SYSTEM,
                description=system["description"],
                properties={"category": "technology", "status": "active"}
            ),
            admin_user_id
        )
        created_nodes.append(node)
        print(f"Created system node: {node.name}")
    
    # Create process nodes
    for process in processes:
        node = await knowledge_service.create_node(
            KnowledgeNodeCreate(
                name=process["name"],
                type=NodeType.PROCESS,
                description=process["description"],
                properties={"category": "business_process", "automation_level": "manual"}
            ),
            admin_user_id
        )
        created_nodes.append(node)
        print(f"Created process node: {node.name}")
    
    # Create sample relationships
    relationships = [
        # HR manages Employee Onboarding
        (0, 5, RelationshipType.MANAGES),
        # IT Operations manages Incident Management
        (1, 6, RelationshipType.MANAGES),
        # ServiceNow supports Incident Management
        (5, 6, RelationshipType.REQUIRES),
        # Salesforce supports Lead Qualification
        (6, 8, RelationshipType.REQUIRES),
        # Finance manages Invoice Processing
        (2, 7, RelationshipType.MANAGES),
    ]
    
    for from_idx, to_idx, rel_type in relationships:
        if from_idx < len(created_nodes) and to_idx < len(created_nodes):
            try:
                rel = await knowledge_service.create_relationship(
                    KnowledgeRelationshipCreate(
                        from_node_id=created_nodes[from_idx].id,
                        to_node_id=created_nodes[to_idx].id,
                        type=rel_type,
                        properties={"created_by_script": True}
                    ),
                    admin_user_id
                )
                print(f"Created relationship: {created_nodes[from_idx].name} -> {created_nodes[to_idx].name}")
            except Exception as e:
                print(f"Error creating relationship: {e}")
    
    return created_nodes


async def clear_database():
    """Clear all data from the database"""
    print("Clearing database...")
    
    queries = [
        "MATCH (n) DETACH DELETE n",  # Delete all nodes and relationships
        "DROP CONSTRAINT IF EXISTS user_email_unique",
        "DROP CONSTRAINT IF EXISTS knowledge_node_id_unique"
    ]
    
    for query in queries:
        try:
            await neo4j_driver.execute_write(query)
        except Exception as e:
            print(f"Note: {e}")
    
    print("Database cleared")


async def create_constraints():
    """Create database constraints"""
    print("Creating database constraints...")
    
    constraints = [
        "CREATE CONSTRAINT user_email_unique IF NOT EXISTS FOR (u:User) REQUIRE u.email IS UNIQUE",
        "CREATE CONSTRAINT knowledge_node_id_unique IF NOT EXISTS FOR (n:KnowledgeNode) REQUIRE n.id IS UNIQUE"
    ]
    
    for constraint in constraints:
        try:
            await neo4j_driver.execute_write(constraint)
            print(f"Created constraint: {constraint.split()[-1]}")
        except Exception as e:
            print(f"Note: {e}")


async def main():
    """Main initialization function"""
    print("Starting Fuschia database initialization...")
    
    try:
        # Connect to database
        await neo4j_driver.connect()
        print("Connected to Neo4j database")
        
        # Clear existing data (optional, comment out for production)
        await clear_database()
        
        # Create constraints
        await create_constraints()
        
        # Create sample data
        print("\nCreating sample users...")
        users = await create_sample_users()
        
        print(f"\nCreating sample knowledge graph...")
        nodes = await create_sample_knowledge_graph()
        
        print(f"\n✅ Database initialization completed successfully!")
        print(f"Created {len(users)} users and {len(nodes)} knowledge nodes")
        
        print("\nSample user credentials:")
        print("Admin: admin@fuschia.io / admin123")
        print("Manager: manager@fuschia.io / manager123")
        print("Analyst: analyst@fuschia.io / analyst123")
        print("User: user@fuschia.io / user123")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise
    
    finally:
        await neo4j_driver.close()
        print("Database connection closed")


if __name__ == "__main__":
    asyncio.run(main())