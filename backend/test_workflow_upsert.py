#!/usr/bin/env python3
"""
Test script to verify workflow upsert functionality
"""
import asyncio
import sys
import os
sys.path.append('/Users/sanjay/Lab/Fuschia-alfa/backend')

from app.services.template_service import template_service
from app.models.template import TemplateCreate, TemplateType, TemplateComplexity

async def test_workflow_upsert():
    """Test the workflow upsert functionality"""
    print("Testing Workflow Upsert Functionality...")
    
    # Test data
    template_data = TemplateCreate(
        name="Test Workflow",
        description="A test workflow for upsert testing",
        category="Testing",
        template_type=TemplateType.WORKFLOW,
        complexity=TemplateComplexity.SIMPLE,
        estimated_time="15 minutes",
        tags=["test", "upsert"],
        preview_steps=["Step 1: Test", "Step 2: Verify"],
        template_data={"nodes": [], "edges": []},
        metadata={"test": True}
    )
    
    user_id = "test_user_123"
    
    try:
        print("\n1. First save (should create new template)...")
        template1 = await template_service.upsert_template(template_data, user_id)
        print(f"✅ Created template: {template1.id} - {template1.name}")
        
        print("\n2. Second save with same name (should update existing)...")
        # Modify the description
        template_data.description = "Updated description for upsert test"
        template_data.tags = ["test", "upsert", "updated"]
        
        template2 = await template_service.upsert_template(template_data, user_id)
        print(f"✅ Updated template: {template2.id} - {template2.name}")
        
        # Verify it's the same template ID
        if template1.id == template2.id:
            print(f"✅ SUCCESS: Template was updated (same ID: {template1.id})")
            print(f"   Original description: {template1.description}")
            print(f"   Updated description: {template2.description}")
        else:
            print(f"❌ FAILED: New template created instead of update")
            print(f"   Original ID: {template1.id}")
            print(f"   New ID: {template2.id}")
        
        print("\n3. Testing with different user (should create new template)...")
        template3 = await template_service.upsert_template(template_data, "different_user_456")
        print(f"✅ Created template for different user: {template3.id}")
        
        if template3.id != template1.id:
            print(f"✅ SUCCESS: Different template created for different user")
        else:
            print(f"❌ FAILED: Same template returned for different user")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_workflow_upsert())