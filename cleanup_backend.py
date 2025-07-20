#!/usr/bin/env python3

import os
import sys

# Define files to remove
files_to_remove = [
    "/Users/sanjay/Lab/Fuschia-alfa/backend/test_api_connectivity.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/test_cypher_endpoint.py", 
    "/Users/sanjay/Lab/Fuschia-alfa/backend/test_import.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/test_servicenow_connection.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/test_servicenow_simple.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/test_exact_issue.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/test_workflow_trigger.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/test_intent_detection.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/test_postgres_users.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/test_template_db.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/test_dynamic_intent.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/test_workflow_execution.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/test_imports.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/test_langchain_intent.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/final_servicenow_test.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/debug_db.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/debug_metadata.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/debug_servicenow.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/cypher_endpoint_example.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/view_database.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/view_database.sh",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/verify_langchain_integration.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/database_queries.sql",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/fix_db.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/fix_template_metadata.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/init_sqlite_db.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/migrate_templates_to_db.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/migrate_users_to_postgres.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/populate_sample_templates.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/reset_db.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/simple_init_db.py",
    "/Users/sanjay/Lab/Fuschia-alfa/backend/test_api_templates.sh"
]

def main():
    print("🧹 Fuschia Backend Cleanup - Removing Test & Debug Files")
    print("=" * 60)
    
    removed_files = []
    missing_files = []
    error_files = []
    
    for file_path in files_to_remove:
        filename = os.path.basename(file_path)
        
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                removed_files.append(filename)
                print(f"✅ Removed: {filename}")
            except OSError as e:
                error_files.append((filename, str(e)))
                print(f"❌ Error removing {filename}: {e}")
        else:
            missing_files.append(filename)
            print(f"⚠️  Not found: {filename}")
    
    print("\n" + "=" * 60)
    print("📊 CLEANUP SUMMARY")
    print("=" * 60)
    print(f"Total files processed: {len(files_to_remove)}")
    print(f"Files successfully removed: {len(removed_files)}")
    print(f"Files not found: {len(missing_files)}")
    print(f"Files with errors: {len(error_files)}")
    
    if removed_files:
        print("\n✅ Successfully removed files:")
        for category, files in [
            ("Test files", [f for f in removed_files if f.startswith('test_') or f == 'final_servicenow_test.py']),
            ("Debug files", [f for f in removed_files if f.startswith('debug_')]),
            ("Migration files", [f for f in removed_files if 'migrate' in f or 'init' in f or 'populate' in f]),
            ("Other files", [f for f in removed_files if not any(x in f for x in ['test_', 'debug_', 'migrate', 'init', 'populate'])])
        ]:
            if files:
                print(f"  {category}:")
                for f in files:
                    print(f"    - {f}")
    
    if missing_files:
        print(f"\n⚠️  Files not found ({len(missing_files)}):")
        for f in missing_files:
            print(f"    - {f}")
    
    if error_files:
        print(f"\n❌ Files with errors ({len(error_files)}):")
        for f, error in error_files:
            print(f"    - {f}: {error}")
    
    print("\n🎉 Cleanup completed!")
    print("The backend directory has been cleaned of test and debug files.")

if __name__ == "__main__":
    main()