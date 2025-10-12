"""
Migration script to fix workflow_executions.organization_id to reference agent_organizations
instead of agent_templates.

This script:
1. Finds all workflow_executions with organization_id pointing to agent_templates
2. Creates agent_organizations from those templates if they don't exist
3. Updates workflow_executions to reference the correct agent_organizations
"""

import asyncio
import sqlite3
import uuid
from datetime import datetime

async def fix_organization_ids():
    """Fix organization_id references in workflow_executions table"""

    # Connect to database
    db_path = "./fuschia_users.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("🔍 Checking workflow_executions for incorrect organization_id references...")

        # Find all workflow executions with organization_id that exists in agent_templates
        cursor.execute("""
            SELECT we.id, we.workflow_template_id, we.organization_id
            FROM workflow_executions we
            WHERE we.organization_id IN (SELECT id FROM agent_templates)
        """)

        executions_to_fix = cursor.fetchall()

        if not executions_to_fix:
            print("✅ No workflow_executions need fixing. All organization_ids are correct.")
            return

        print(f"📋 Found {len(executions_to_fix)} workflow_executions with incorrect organization_id")

        # Mapping of template_id -> organization_id
        template_to_org_map = {}

        for execution_id, workflow_template_id, template_id in executions_to_fix:
            # Check if we already created an organization for this template
            if template_id in template_to_org_map:
                organization_id = template_to_org_map[template_id]
                print(f"   Using existing organization {organization_id[:8]}... for template {template_id[:8]}...")
            else:
                # Check if an organization already exists for this template
                cursor.execute("""
                    SELECT id FROM agent_organizations
                    WHERE agent_template_id = ?
                    LIMIT 1
                """, (template_id,))

                existing_org = cursor.fetchone()

                if existing_org:
                    organization_id = existing_org[0]
                    print(f"   Found existing organization {organization_id[:8]}... for template {template_id[:8]}...")
                else:
                    # Create a new agent_organization from the template
                    organization_id = str(uuid.uuid4())

                    # Get template details
                    cursor.execute("""
                        SELECT name, description, agents_data, connections_data,
                               entry_points, max_execution_time_minutes,
                               require_human_supervision, allow_parallel_execution
                        FROM agent_templates
                        WHERE id = ?
                    """, (template_id,))

                    template_data = cursor.fetchone()

                    if not template_data:
                        print(f"   ⚠️  Template {template_id[:8]}... not found, skipping...")
                        continue

                    (name, description, agents_data, connections_data,
                     entry_points, max_execution_time, require_supervision,
                     allow_parallel) = template_data

                    # Insert new agent_organization
                    cursor.execute("""
                        INSERT INTO agent_organizations (
                            id, name, description, agent_template_id,
                            entry_points, max_execution_time_minutes,
                            require_human_supervision, allow_parallel_execution,
                            agents_data, connections_data,
                            usage_count, status, organization_metadata,
                            created_by, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        organization_id,
                        f"{name} (Instance)",
                        description or f"Organization created from template {name}",
                        template_id,
                        entry_points or '[]',
                        max_execution_time or 120,
                        require_supervision if require_supervision is not None else True,
                        allow_parallel if allow_parallel is not None else True,
                        agents_data or '[]',
                        connections_data or '[]',
                        0,  # usage_count
                        'active',
                        '{}',  # organization_metadata
                        'system',  # created_by
                        datetime.utcnow().isoformat(),
                        datetime.utcnow().isoformat()
                    ))

                    print(f"   ✨ Created new organization {organization_id[:8]}... from template {template_id[:8]}...")

                template_to_org_map[template_id] = organization_id

            # Update workflow_execution to reference the correct organization
            cursor.execute("""
                UPDATE workflow_executions
                SET organization_id = ?
                WHERE id = ?
            """, (organization_id, execution_id))

            print(f"   ✅ Updated execution {execution_id[:8]}... to use organization {organization_id[:8]}...")

        # Commit all changes
        conn.commit()
        print(f"\n✅ Successfully fixed {len(executions_to_fix)} workflow_executions")
        print(f"✅ Created/reused {len(template_to_org_map)} agent_organizations")

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Workflow Execution Organization ID Migration")
    print("=" * 60)
    asyncio.run(fix_organization_ids())
    print("=" * 60)
    print("Migration completed!")
    print("=" * 60)
