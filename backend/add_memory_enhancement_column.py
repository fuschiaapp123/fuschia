#!/usr/bin/env python3
"""
Simple database migration to add use_memory_enhancement column.
This script directly adds the column without complex dependencies.
"""

import sqlite3
import os
import sys

def add_column_to_sqlite():
    """Add use_memory_enhancement column to SQLite database"""
    
    # Look for database files
    possible_db_paths = [
        'fuschia.db',
        'app.db', 
        'sqlite.db',
        'database.db',
        '../fuschia.db',
        '../app.db'
    ]
    
    db_path = None
    for path in possible_db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ Could not find SQLite database file")
        print("Please specify the database path manually")
        return False
    
    print(f"📁 Found database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='workflow_executions'
        """)
        
        if not cursor.fetchone():
            print("❌ workflow_executions table not found")
            return False
        
        print("✅ Found workflow_executions table")
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(workflow_executions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'use_memory_enhancement' in columns:
            print("✅ Column use_memory_enhancement already exists")
            return True
        
        print("🔄 Adding use_memory_enhancement column...")
        
        # Add the column
        cursor.execute("""
            ALTER TABLE workflow_executions 
            ADD COLUMN use_memory_enhancement BOOLEAN NOT NULL DEFAULT FALSE
        """)
        
        conn.commit()
        print("✅ Column added successfully!")
        
        # Verify
        cursor.execute("PRAGMA table_info(workflow_executions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'use_memory_enhancement' in columns:
            print("✅ Column verified successfully!")
            return True
        else:
            print("❌ Column verification failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    print("=" * 50)
    print("Memory Enhancement Column Migration")
    print("=" * 50)
    
    success = add_column_to_sqlite()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("The use_memory_enhancement column has been added.")
        print("\nRestart your backend server and try again.")
    else:
        print("\n💥 Migration failed!")
        print("Please check the error messages above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)