from fastapi import APIRouter, Depends
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth import get_current_user
from app.models.user import User
from app.db.postgres import get_db, WorkflowExecutionTable, WorkflowTemplateTable, UserTable, WorkflowTaskTable

router = APIRouter()

async def get_task_details_with_original_ids(task_ids: List[str], template_data: dict, execution_id: str, db: AsyncSession):
    """Convert task IDs to task objects with details from template

    Note: task_ids are UUIDs assigned at runtime, not the original node IDs.
    We need to fetch the tasks from DB to get the original_node_id from context.
    """
    if not task_ids or not template_data or 'nodes' not in template_data:
        return []

    # Fetch actual task objects from database to get original_node_id
    task_query = select(WorkflowTaskTable).where(
        WorkflowTaskTable.execution_id == execution_id,
        WorkflowTaskTable.id.in_(task_ids)
    )
    task_result = await db.execute(task_query)
    task_records = task_result.scalars().all()

    # Create a map of node IDs to node data
    node_map = {node['id']: node for node in template_data.get('nodes', [])}

    tasks = []
    for task_record in task_records:
        # Get original node ID from task context
        original_node_id = task_record.context.get('original_node_id') if task_record.context else None

        if original_node_id and original_node_id in node_map:
            node = node_map[original_node_id]
            tasks.append({
                'id': original_node_id,  # Use original node ID for frontend mapping
                'name': node.get('data', {}).get('label', 'Unnamed Task'),
                'type': node.get('data', {}).get('type', 'action'),
                'description': node.get('data', {}).get('description', ''),
            })
        else:
            # Fallback: use task record data
            tasks.append({
                'id': original_node_id or task_record.id,
                'name': task_record.name or f'Task {task_record.id[:8]}',
                'type': task_record.context.get('task_type', 'unknown') if task_record.context else 'unknown',
                'description': task_record.description or '',
            })
    return tasks

@router.get("/workflow-executions")
async def get_workflow_executions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all workflow executions (admin/process_owner view)"""
    try:
        # Query workflow executions with joins to get workflow names and user names
        query = (
            select(WorkflowExecutionTable, WorkflowTemplateTable, UserTable)
            .join(WorkflowTemplateTable, WorkflowExecutionTable.workflow_template_id == WorkflowTemplateTable.id)
            .join(UserTable, WorkflowExecutionTable.initiated_by == UserTable.id)
            .order_by(WorkflowExecutionTable.started_at.desc())
        )

        result = await db.execute(query)
        executions = result.all()

        # Debug logging for template_data
        result_list = []
        for execution, template, user in executions:
            template_data = template.template_data or {}
            print(f"📊 Monitoring API (/workflow-executions): Execution {execution.id}")
            print(f"   Template data keys: {list(template_data.keys())}")
            print(f"   Has nodes: {'nodes' in template_data}")
            print(f"   Has edges: {'edges' in template_data}")
            if 'nodes' in template_data:
                print(f"   Nodes count: {len(template_data.get('nodes', []))}")
            if 'edges' in template_data:
                edges = template_data.get('edges', [])
                print(f"   Edges count: {len(edges)}")
                if edges:
                    print(f"   First edge sample: {edges[0]}")

            result_list.append({
                "id": execution.id,
                "workflow_template_id": execution.workflow_template_id,
                "workflow_name": template.name,
                "status": execution.status,
                "current_tasks": await get_task_details_with_original_ids(
                    execution.current_tasks or [], template_data, execution.id, db
                ),
                "completed_tasks": await get_task_details_with_original_ids(
                    execution.completed_tasks or [], template_data, execution.id, db
                ),
                "failed_tasks": await get_task_details_with_original_ids(
                    execution.failed_tasks or [], template_data, execution.id, db
                ),
                "template_data": template_data,  # Include workflow structure (nodes/edges)
                "started_at": execution.started_at.isoformat(),
                "estimated_completion": execution.estimated_completion.isoformat() if execution.estimated_completion else None,
                "actual_completion": execution.actual_completion.isoformat() if execution.actual_completion else None,
                "initiated_by": execution.initiated_by,
                "initiated_by_name": user.full_name or user.email,
            })

        return result_list
    except Exception as e:
        # If there's an error, log it and return empty list
        print(f"Error fetching workflow executions: {e}")
        import traceback
        traceback.print_exc()
        return []

@router.get("/workflow-executions/me")
async def get_my_workflow_executions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get workflow executions for current user"""
    try:
        # Query workflow executions for the current user
        query = (
            select(WorkflowExecutionTable, WorkflowTemplateTable, UserTable)
            .join(WorkflowTemplateTable, WorkflowExecutionTable.workflow_template_id == WorkflowTemplateTable.id)
            .join(UserTable, WorkflowExecutionTable.initiated_by == UserTable.id)
            .where(WorkflowExecutionTable.initiated_by == current_user.id)
            .order_by(WorkflowExecutionTable.started_at.desc())
        )

        result = await db.execute(query)
        executions = result.all()

        # Debug logging for template_data
        result_list = []
        for execution, template, user in executions:
            template_data = template.template_data or {}
            print(f"📊 Monitoring API (/workflow-executions/me): Execution {execution.id}")
            print(f"   Template data keys: {list(template_data.keys())}")
            print(f"   Has nodes: {'nodes' in template_data}")
            print(f"   Has edges: {'edges' in template_data}")
            if 'nodes' in template_data:
                print(f"   Nodes count: {len(template_data.get('nodes', []))}")
            if 'edges' in template_data:
                edges = template_data.get('edges', [])
                print(f"   Edges count: {len(edges)}")
                if edges:
                    print(f"   First edge sample: {edges[0]}")

            result_list.append({
                "id": execution.id,
                "workflow_template_id": execution.workflow_template_id,
                "workflow_name": template.name,
                "status": execution.status,
                "current_tasks": await get_task_details_with_original_ids(
                    execution.current_tasks or [], template_data, execution.id, db
                ),
                "completed_tasks": await get_task_details_with_original_ids(
                    execution.completed_tasks or [], template_data, execution.id, db
                ),
                "failed_tasks": await get_task_details_with_original_ids(
                    execution.failed_tasks or [], template_data, execution.id, db
                ),
                "template_data": template_data,  # Include workflow structure (nodes/edges)
                "started_at": execution.started_at.isoformat(),
                "estimated_completion": execution.estimated_completion.isoformat() if execution.estimated_completion else None,
                "actual_completion": execution.actual_completion.isoformat() if execution.actual_completion else None,
                "initiated_by": execution.initiated_by,
                "initiated_by_name": user.full_name or user.email,
            })

        return result_list
    except Exception as e:
        # If there's an error, log it and return empty list
        print(f"Error fetching workflow executions: {e}")
        import traceback
        traceback.print_exc()
        return []

@router.get("/agent-organizations")
async def get_agent_organizations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all agent organizations (admin/process_owner view)"""
    try:
        from app.db.postgres import AgentOrganizationTable

        # Query agent organizations with user information
        query = (
            select(AgentOrganizationTable, UserTable)
            .join(UserTable, AgentOrganizationTable.created_by == UserTable.id, isouter=True)
            .order_by(AgentOrganizationTable.created_at.desc())
        )

        result = await db.execute(query)
        organizations = result.all()

        return [
            {
                "id": org.id,
                "name": org.name,
                "description": org.description,
                "status": org.status,
                "agents_data": org.agents_data,
                "connections_data": org.connections_data,
                "usage_count": org.usage_count,
                "created_by": org.created_by,
                "created_by_name": user.full_name or user.email if user else "Unknown",
                "last_activity": org.updated_at.isoformat() if org.updated_at else org.created_at.isoformat(),
            }
            for org, user in organizations
        ]
    except Exception as e:
        # If there's an error, log it and return empty list
        print(f"Error fetching agent organizations: {e}")
        return []

@router.get("/agent-organizations/me")
async def get_my_agent_organizations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get agent organizations for current user"""
    try:
        from app.db.postgres import AgentOrganizationTable

        # Query agent organizations for the current user
        query = (
            select(AgentOrganizationTable, UserTable)
            .join(UserTable, AgentOrganizationTable.created_by == UserTable.id, isouter=True)
            .where(AgentOrganizationTable.created_by == current_user.id)
            .order_by(AgentOrganizationTable.created_at.desc())
        )

        result = await db.execute(query)
        organizations = result.all()

        return [
            {
                "id": org.id,
                "name": org.name,
                "description": org.description,
                "status": org.status,
                "agents_data": org.agents_data,
                "connections_data": org.connections_data,
                "usage_count": org.usage_count,
                "created_by": org.created_by,
                "created_by_name": user.full_name or user.email if user else "Unknown",
                "last_activity": org.updated_at.isoformat() if org.updated_at else org.created_at.isoformat(),
            }
            for org, user in organizations
        ]
    except Exception as e:
        # If there's an error, log it and return empty list
        print(f"Error fetching agent organizations: {e}")
        return []
