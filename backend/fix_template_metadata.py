#!/usr/bin/env python3
"""
Simple script to test and fix template metadata issues
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all imports work correctly"""
    print("🔍 Testing imports...")
    
    try:
        print("  - Testing basic imports...")
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
        from sqlalchemy.orm import DeclarativeBase
        from sqlalchemy import Column, String, Boolean, DateTime, text, Integer, JSON, ForeignKey
        print("    ✅ SQLAlchemy imports successful")
        
        print("  - Testing user model imports...")
        from app.models.user import UserRole
        print("    ✅ User model imports successful")
        
        print("  - Testing template model imports...")
        from app.models.template import TemplateType, TemplateComplexity, TemplateStatus
        print("    ✅ Template model imports successful")
        
        print("  - Testing Base class...")
        from app.db.postgres import Base
        print("    ✅ Base class import successful")
        
        print("  - Testing UserTable...")
        from app.db.postgres import UserTable
        print("    ✅ UserTable import successful")
        
        print("  - Testing TemplateTable...")
        from app.db.postgres import TemplateTable
        print("    ✅ TemplateTable import successful")
        
        # Check table definitions
        print(f"  - UserTable columns: {[col.name for col in UserTable.__table__.columns]}")
        print(f"  - TemplateTable columns: {[col.name for col in TemplateTable.__table__.columns]}")
        
        # Check if metadata is in TemplateTable columns (it shouldn't be)
        template_columns = [col.name for col in TemplateTable.__table__.columns]
        if 'metadata' in template_columns:
            print("    ❌ ERROR: 'metadata' column still exists in TemplateTable!")
            return False
        elif 'template_metadata' in template_columns:
            print("    ✅ 'template_metadata' column correctly renamed")
        else:
            print("    ⚠️  Neither 'metadata' nor 'template_metadata' found")
        
        print("✅ All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    if success:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("❌ Tests failed!")
        sys.exit(1)