#!/usr/bin/env python3
"""
Debug script to check workflow templates in the database and identify why templates 
are returning empty nodes/edges arrays.
"""

import asyncio
import sqlite3
import json
from pathlib import Path

async def check_workflow_templates():
    """Check the workflow templates in the database"""
    print("=== Debugging Workflow Templates ===\n")
    
    # Check if SQLite database exists
    db_path = Path("fuschia_users.db")
    if not db_path.exists():
        print(f"❌ Database file {db_path} does not exist!")
        return
    
    # Connect to SQLite database
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()
        
        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Available tables: {tables}\n")
        
        # Check workflow_templates table
        if 'workflow_templates' in tables:
            print("✅ workflow_templates table found")
            cursor.execute("SELECT COUNT(*) FROM workflow_templates")
            count = cursor.fetchone()[0]
            print(f"📊 Total workflow templates: {count}")
            
            if count > 0:
                # Get all workflow templates
                cursor.execute("""
                    SELECT id, name, description, category, template_data, template_metadata 
                    FROM workflow_templates 
                    LIMIT 5
                """)
                templates = cursor.fetchall()
                
                for i, template in enumerate(templates, 1):
                    print(f"\n--- Template {i}: {template['name']} ---")
                    print(f"ID: {template['id']}")
                    print(f"Category: {template['category']}")
                    print(f"Description: {template['description']}")
                    
                    # Parse template_data JSON
                    template_data = template['template_data']
                    if template_data:
                        if isinstance(template_data, str):
                            try:
                                data = json.loads(template_data)
                                print(f"Template Data Type: {type(data)}")
                                print(f"Template Data Keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
                                
                                # Check for nodes and edges
                                if isinstance(data, dict):
                                    nodes = data.get('nodes', [])
                                    edges = data.get('edges', [])
                                    print(f"Nodes count: {len(nodes)}")
                                    print(f"Edges count: {len(edges)}")
                                    
                                    if len(nodes) == 0:
                                        print("⚠️  WARNING: No nodes found in template_data!")
                                    if len(edges) == 0:
                                        print("⚠️  WARNING: No edges found in template_data!")
                                        
                                    # Show first node if exists
                                    if nodes:
                                        print(f"First node sample: {json.dumps(nodes[0], indent=2)}")
                                else:
                                    print(f"❌ template_data is not a dict: {data}")
                            except json.JSONDecodeError as e:
                                print(f"❌ Failed to parse template_data JSON: {e}")
                                print(f"Raw template_data: {template_data[:200]}...")
                        else:
                            print(f"Template Data (direct): {template_data}")
                    else:
                        print("❌ template_data is None or empty")
        else:
            print("❌ workflow_templates table not found")
            
        # Check legacy templates table
        if 'templates' in tables:
            print("\n✅ Legacy templates table found")
            cursor.execute("SELECT COUNT(*) FROM templates WHERE template_type = 'workflow'")
            count = cursor.fetchone()[0]
            print(f"📊 Total legacy workflow templates: {count}")
            
            if count > 0:
                cursor.execute("""
                    SELECT id, name, description, category, template_data, template_metadata 
                    FROM templates 
                    WHERE template_type = 'workflow'
                    LIMIT 5
                """)
                templates = cursor.fetchall()
                
                for i, template in enumerate(templates, 1):
                    print(f"\n--- Legacy Template {i}: {template['name']} ---")
                    print(f"ID: {template['id']}")
                    print(f"Category: {template['category']}")
                    
                    template_data = template['template_data']
                    if template_data:
                        if isinstance(template_data, str):
                            try:
                                data = json.loads(template_data)
                                nodes = data.get('nodes', [])
                                edges = data.get('edges', [])
                                print(f"Legacy nodes count: {len(nodes)}")
                                print(f"Legacy edges count: {len(edges)}")
                                
                                if len(nodes) == 0:
                                    print("⚠️  WARNING: No nodes in legacy template!")
                            except json.JSONDecodeError as e:
                                print(f"❌ Failed to parse legacy template_data: {e}")
                        else:
                            print(f"Legacy template_data: {template_data}")
        else:
            print("❌ Legacy templates table not found")
            
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    finally:
        if conn:
            conn.close()
    
    print("\n=== Debug Complete ===")

if __name__ == "__main__":
    asyncio.run(check_workflow_templates())