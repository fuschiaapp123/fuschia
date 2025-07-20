#!/usr/bin/env python3
"""
Migration script to populate PostgreSQL database with workflow and agent templates
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.postgres import init_db
from app.services.template_service import template_service
from app.models.template import TemplateCreate, TemplateType, TemplateComplexity, TemplateStatus


# Built-in workflow templates data
WORKFLOW_TEMPLATES = [
    {
        "name": "Employee Onboarding",
        "description": "Automate the complete employee onboarding process from form submission to IT setup",
        "category": "HR",
        "template_type": TemplateType.WORKFLOW,
        "complexity": TemplateComplexity.MEDIUM,
        "estimated_time": "2-3 hours",
        "tags": ["HR", "Onboarding", "IT Setup"],
        "preview_steps": [
            "New hire form submitted",
            "Create user accounts",
            "Send welcome email",
            "Assign equipment",
            "Schedule orientation"
        ],
        "template_data": {
            "nodes": [
                {
                    "id": "1",
                    "type": "workflowStep",
                    "position": {"x": 100, "y": 100},
                    "data": {
                        "label": "New Hire Form Submitted",
                        "type": "trigger",
                        "description": "Triggers when new employee form is submitted",
                        "objective": "Capture new hire information and initiate onboarding",
                        "completionCriteria": "Form data validated and stored"
                    }
                },
                {
                    "id": "2",
                    "type": "workflowStep",
                    "position": {"x": 100, "y": 250},
                    "data": {
                        "label": "Create IT Accounts",
                        "type": "action",
                        "description": "Create email, system accounts, and access permissions",
                        "objective": "Provision all necessary IT resources for new employee",
                        "completionCriteria": "All accounts created and access granted"
                    }
                },
                {
                    "id": "3",
                    "type": "workflowStep",
                    "position": {"x": 100, "y": 400},
                    "data": {
                        "label": "Send Welcome Email",
                        "type": "action",
                        "description": "Send welcome email with first day information",
                        "objective": "Provide new hire with essential first day details",
                        "completionCriteria": "Welcome email delivered and confirmed read"
                    }
                },
                {
                    "id": "4",
                    "type": "workflowStep",
                    "position": {"x": 300, "y": 250},
                    "data": {
                        "label": "Assign Equipment",
                        "type": "action",
                        "description": "Reserve and assign laptop, phone, and other equipment",
                        "objective": "Ensure new hire has all necessary equipment",
                        "completionCriteria": "Equipment assigned and ready for pickup"
                    }
                },
                {
                    "id": "5",
                    "type": "workflowStep",
                    "position": {"x": 200, "y": 550},
                    "data": {
                        "label": "Onboarding Complete",
                        "type": "end",
                        "description": "Mark onboarding process as complete",
                        "objective": "Finalize onboarding and notify stakeholders",
                        "completionCriteria": "All tasks completed and documented"
                    }
                }
            ],
            "edges": [
                {"id": "e1-2", "source": "1", "target": "2", "type": "smoothstep"},
                {"id": "e1-4", "source": "1", "target": "4", "type": "smoothstep"},
                {"id": "e2-3", "source": "2", "target": "3", "type": "smoothstep"},
                {"id": "e3-5", "source": "3", "target": "5", "type": "smoothstep"},
                {"id": "e4-5", "source": "4", "target": "5", "type": "smoothstep"}
            ]
        },
        "metadata": {
            "author": "Fuschia System",
            "version": "1.0.0",
            "created": datetime.utcnow().isoformat()
        }
    },
    {
        "name": "IT Incident Management",
        "description": "Automated IT incident triage and resolution workflow with escalation rules",
        "category": "IT Operations",
        "template_type": TemplateType.WORKFLOW,
        "complexity": TemplateComplexity.ADVANCED,
        "estimated_time": "30 minutes",
        "tags": ["IT", "Support", "Escalation"],
        "preview_steps": [
            "Incident reported",
            "Auto-classify severity",
            "Assign to team",
            "Send notifications",
            "Track resolution"
        ],
        "template_data": {
            "nodes": [
                {
                    "id": "1",
                    "type": "workflowStep",
                    "position": {"x": 100, "y": 100},
                    "data": {
                        "label": "Incident Reported",
                        "type": "trigger",
                        "description": "Incident ticket created in support system",
                        "objective": "Capture incident details and begin triage process",
                        "completionCriteria": "Incident logged with all required information"
                    }
                },
                {
                    "id": "2",
                    "type": "workflowStep",
                    "position": {"x": 100, "y": 250},
                    "data": {
                        "label": "Classify Severity",
                        "type": "condition",
                        "description": "Automatically determine incident severity level",
                        "objective": "Classify incident priority for proper routing",
                        "completionCriteria": "Severity level assigned (P1, P2, P3, P4)"
                    }
                },
                {
                    "id": "3",
                    "type": "workflowStep",
                    "position": {"x": 300, "y": 200},
                    "data": {
                        "label": "Assign to L1 Support",
                        "type": "action",
                        "description": "Route to Level 1 support team",
                        "objective": "Assign to appropriate support team based on severity",
                        "completionCriteria": "Ticket assigned and support team notified"
                    }
                },
                {
                    "id": "4",
                    "type": "workflowStep",
                    "position": {"x": 300, "y": 350},
                    "data": {
                        "label": "Escalate to L2",
                        "type": "condition",
                        "description": "Escalate if SLA breach risk or complexity",
                        "objective": "Prevent SLA breaches through timely escalation",
                        "completionCriteria": "Escalation criteria evaluated and acted upon"
                    }
                },
                {
                    "id": "5",
                    "type": "workflowStep",
                    "position": {"x": 500, "y": 250},
                    "data": {
                        "label": "Send Notifications",
                        "type": "action",
                        "description": "Notify stakeholders of incident status",
                        "objective": "Keep relevant parties informed of incident progress",
                        "completionCriteria": "All notifications sent and delivered"
                    }
                },
                {
                    "id": "6",
                    "type": "workflowStep",
                    "position": {"x": 400, "y": 500},
                    "data": {
                        "label": "Incident Resolved",
                        "type": "end",
                        "description": "Mark incident as resolved and close ticket",
                        "objective": "Close incident and update knowledge base",
                        "completionCriteria": "Resolution documented and ticket closed"
                    }
                }
            ],
            "edges": [
                {"id": "e1-2", "source": "1", "target": "2", "type": "smoothstep"},
                {"id": "e2-3", "source": "2", "target": "3", "type": "smoothstep"},
                {"id": "e3-4", "source": "3", "target": "4", "type": "smoothstep"},
                {"id": "e3-5", "source": "3", "target": "5", "type": "smoothstep"},
                {"id": "e4-5", "source": "4", "target": "5", "type": "smoothstep"},
                {"id": "e5-6", "source": "5", "target": "6", "type": "smoothstep"}
            ]
        },
        "metadata": {
            "author": "Fuschia System",
            "version": "1.0.0",
            "created": datetime.utcnow().isoformat()
        }
    },
    {
        "name": "Purchase Request Approval",
        "description": "Automated workflow for purchase request approval with budget validation",
        "category": "Finance",
        "template_type": TemplateType.WORKFLOW,
        "complexity": TemplateComplexity.MEDIUM,
        "estimated_time": "1-2 hours",
        "tags": ["Finance", "Approval", "Budget"],
        "preview_steps": [
            "Purchase request submitted",
            "Validate budget",
            "Manager approval",
            "Procurement processing",
            "Order placed"
        ],
        "template_data": {
            "nodes": [
                {
                    "id": "1",
                    "type": "workflowStep",
                    "position": {"x": 100, "y": 100},
                    "data": {
                        "label": "Purchase Request Submitted",
                        "type": "trigger",
                        "description": "New purchase request form submitted",
                        "objective": "Capture purchase request details",
                        "completionCriteria": "Request validated and logged"
                    }
                },
                {
                    "id": "2",
                    "type": "workflowStep",
                    "position": {"x": 100, "y": 250},
                    "data": {
                        "label": "Budget Validation",
                        "type": "condition",
                        "description": "Check if budget is available for purchase",
                        "objective": "Ensure sufficient budget before approval",
                        "completionCriteria": "Budget availability confirmed"
                    }
                },
                {
                    "id": "3",
                    "type": "workflowStep",
                    "position": {"x": 300, "y": 200},
                    "data": {
                        "label": "Manager Approval",
                        "type": "action",
                        "description": "Route to manager for approval",
                        "objective": "Obtain necessary management approval",
                        "completionCriteria": "Manager approval received"
                    }
                },
                {
                    "id": "4",
                    "type": "workflowStep",
                    "position": {"x": 500, "y": 200},
                    "data": {
                        "label": "Procurement Processing",
                        "type": "action",
                        "description": "Process through procurement department",
                        "objective": "Handle procurement logistics",
                        "completionCriteria": "Procurement processed and vendor selected"
                    }
                }
            ],
            "edges": [
                {"id": "e1-2", "source": "1", "target": "2", "type": "smoothstep"},
                {"id": "e2-3", "source": "2", "target": "3", "type": "smoothstep"},
                {"id": "e3-4", "source": "3", "target": "4", "type": "smoothstep"}
            ]
        },
        "metadata": {
            "author": "Fuschia System",
            "version": "1.0.0",
            "created": datetime.utcnow().isoformat()
        }
    }
]

# Built-in agent templates data
AGENT_TEMPLATES = [
    {
        "name": "IT Service Desk Agent",
        "description": "Multi-agent organization for IT support with escalation hierarchy",
        "category": "IT Support",
        "template_type": TemplateType.AGENT,
        "complexity": TemplateComplexity.ADVANCED,
        "estimated_time": "45 minutes",
        "tags": ["IT", "Support", "ServiceNow", "Escalation"],
        "preview_steps": [
            "Front desk agent receives request",
            "Route to IT service manager",
            "Assign to specialist agent",
            "Execute service tools",
            "Provide resolution"
        ],
        "template_data": {
            "nodes": [
                {
                    "id": "1",
                    "label": "Front Desk Agent",
                    "type": "start",
                    "description": "First line agent that responds to all queries",
                    "tools": []
                },
                {
                    "id": "2",
                    "label": "IT Service Manager",
                    "type": "supervisor",
                    "description": "Supervises IT support operations",
                    "tools": []
                },
                {
                    "id": "3",
                    "label": "Incident Management Agent",
                    "type": "specialist",
                    "description": "Handles incident creation and management",
                    "tools": ["Get Incident", "Create Incident"]
                },
                {
                    "id": "4",
                    "label": "Change Management Agent",
                    "type": "specialist",
                    "description": "Handles change requests and approvals",
                    "tools": ["Get Change", "Create Change"]
                }
            ],
            "edges": [
                {"id": "e1-2", "source": "1", "target": "2", "type": "flow"},
                {"id": "e2-3", "source": "2", "target": "3", "type": "flow"},
                {"id": "e2-4", "source": "2", "target": "4", "type": "flow"}
            ]
        },
        "metadata": {
            "author": "Fuschia System",
            "version": "1.0.0",
            "created": datetime.utcnow().isoformat()
        }
    },
    {
        "name": "HR Service Agent",
        "description": "Human resources support agent organization for employee queries",
        "category": "HR Support",
        "template_type": TemplateType.AGENT,
        "complexity": TemplateComplexity.MEDIUM,
        "estimated_time": "30 minutes",
        "tags": ["HR", "Payroll", "Benefits", "Employee"],
        "preview_steps": [
            "Employee query received",
            "Route to HR manager",
            "Assign to HR specialist",
            "Process request",
            "Provide response"
        ],
        "template_data": {
            "nodes": [
                {
                    "id": "1",
                    "label": "Front Desk Agent",
                    "type": "start",
                    "description": "Initial contact point for HR queries",
                    "tools": []
                },
                {
                    "id": "2",
                    "label": "HR Service Manager",
                    "type": "supervisor",
                    "description": "Manages HR service operations",
                    "tools": []
                },
                {
                    "id": "3",
                    "label": "Payroll Specialist",
                    "type": "specialist",
                    "description": "Handles payroll-related queries",
                    "tools": ["Get Payroll", "Create Payroll"]
                },
                {
                    "id": "4",
                    "label": "Benefits Specialist",
                    "type": "specialist",
                    "description": "Manages employee benefits inquiries",
                    "tools": ["Get Benefit", "Create Benefit"]
                }
            ],
            "edges": [
                {"id": "e1-2", "source": "1", "target": "2", "type": "flow"},
                {"id": "e2-3", "source": "2", "target": "3", "type": "flow"},
                {"id": "e2-4", "source": "2", "target": "4", "type": "flow"}
            ]
        },
        "metadata": {
            "author": "Fuschia System",
            "version": "1.0.0",
            "created": datetime.utcnow().isoformat()
        }
    },
    {
        "name": "Customer Service Agent",
        "description": "Customer service organization for billing and account support",
        "category": "Customer Service",
        "template_type": TemplateType.AGENT,
        "complexity": TemplateComplexity.MEDIUM,
        "estimated_time": "25 minutes",
        "tags": ["Customer", "Billing", "Support", "Account"],
        "preview_steps": [
            "Customer inquiry received",
            "Route to service manager",
            "Assign to specialist",
            "Resolve customer issue",
            "Follow up"
        ],
        "template_data": {
            "nodes": [
                {
                    "id": "1",
                    "label": "Customer Service Agent",
                    "type": "start",
                    "description": "Handles initial customer contact",
                    "tools": []
                },
                {
                    "id": "2",
                    "label": "Billing Specialist",
                    "type": "specialist",
                    "description": "Manages billing inquiries and disputes",
                    "tools": ["Get Billing", "Create Billing"]
                },
                {
                    "id": "3",
                    "label": "Account Specialist",
                    "type": "specialist",
                    "description": "Handles account management requests",
                    "tools": ["Get Order", "Create Order"]
                }
            ],
            "edges": [
                {"id": "e1-2", "source": "1", "target": "2", "type": "flow"},
                {"id": "e1-3", "source": "1", "target": "3", "type": "flow"}
            ]
        },
        "metadata": {
            "author": "Fuschia System",
            "version": "1.0.0",
            "created": datetime.utcnow().isoformat()
        }
    }
]


async def migrate_templates():
    """Migrate templates to PostgreSQL database"""
    print("🚀 Starting template migration to PostgreSQL...")
    
    try:
        # Initialize database
        print("📊 Initializing database...")
        await init_db()
        print("✅ Database initialized successfully")
        
        # Migrate workflow templates
        print(f"📋 Migrating {len(WORKFLOW_TEMPLATES)} workflow templates...")
        for template_data in WORKFLOW_TEMPLATES:
            try:
                template = TemplateCreate(**template_data)
                created_template = await template_service.create_template(
                    template_data=template,
                    created_by="system"
                )
                print(f"  ✅ Created workflow template: {created_template.name}")
            except Exception as e:
                print(f"  ❌ Failed to create workflow template {template_data['name']}: {e}")
        
        # Migrate agent templates
        print(f"🤖 Migrating {len(AGENT_TEMPLATES)} agent templates...")
        for template_data in AGENT_TEMPLATES:
            try:
                template = TemplateCreate(**template_data)
                created_template = await template_service.create_template(
                    template_data=template,
                    created_by="system"
                )
                print(f"  ✅ Created agent template: {created_template.name}")
            except Exception as e:
                print(f"  ❌ Failed to create agent template {template_data['name']}: {e}")
        
        # Verify migration
        print("🔍 Verifying migration...")
        all_templates = await template_service.search_templates(limit=100)
        workflow_count = len([t for t in all_templates.templates if t.template_type == TemplateType.WORKFLOW])
        agent_count = len([t for t in all_templates.templates if t.template_type == TemplateType.AGENT])
        
        print(f"📊 Migration Summary:")
        print(f"  - Total templates: {all_templates.total_count}")
        print(f"  - Workflow templates: {workflow_count}")
        print(f"  - Agent templates: {agent_count}")
        print(f"  - Categories: {', '.join(all_templates.categories_found)}")
        
        print("🎉 Template migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(migrate_templates())