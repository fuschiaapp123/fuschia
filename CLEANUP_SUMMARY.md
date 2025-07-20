# Backend Cleanup Summary

## Files to be Removed

Due to bash environment issues, the following files should be manually removed from the `/Users/sanjay/Lab/Fuschia-alfa/backend/` directory:

### Test Files (15 files):
- test_api_connectivity.py
- test_cypher_endpoint.py
- test_import.py
- test_servicenow_connection.py
- test_servicenow_simple.py
- test_exact_issue.py
- test_workflow_trigger.py
- test_intent_detection.py
- test_postgres_users.py
- test_template_db.py
- test_dynamic_intent.py
- test_workflow_execution.py
- test_imports.py
- test_langchain_intent.py
- final_servicenow_test.py

### Debug Files (3 files):
- debug_db.py
- debug_metadata.py
- debug_servicenow.py

### Other Extraneous Files (14 files):
- cypher_endpoint_example.py
- view_database.py
- view_database.sh
- verify_langchain_integration.py
- database_queries.sql
- fix_db.py
- fix_template_metadata.py
- init_sqlite_db.py
- migrate_templates_to_db.py
- migrate_users_to_postgres.py
- populate_sample_templates.py
- reset_db.py
- simple_init_db.py
- test_api_templates.sh

## Manual Cleanup Commands

To remove these files manually, run the following commands:

```bash
cd /Users/sanjay/Lab/Fuschia-alfa/backend

# Remove test files
rm -f test_api_connectivity.py test_cypher_endpoint.py test_import.py
rm -f test_servicenow_connection.py test_servicenow_simple.py test_exact_issue.py
rm -f test_workflow_trigger.py test_intent_detection.py test_postgres_users.py
rm -f test_template_db.py test_dynamic_intent.py test_workflow_execution.py
rm -f test_imports.py test_langchain_intent.py final_servicenow_test.py

# Remove debug files
rm -f debug_db.py debug_metadata.py debug_servicenow.py

# Remove other files
rm -f cypher_endpoint_example.py view_database.py view_database.sh
rm -f verify_langchain_integration.py database_queries.sql fix_db.py
rm -f fix_template_metadata.py init_sqlite_db.py migrate_templates_to_db.py
rm -f migrate_users_to_postgres.py populate_sample_templates.py reset_db.py
rm -f simple_init_db.py test_api_templates.sh
```

## Files to Keep

The following production files should remain:
- app.py (main Flask application)
- app/ directory (core application code)
- Dockerfile
- pyproject.toml
- requirements.txt
- scripts/ directory (production scripts)
- data/ directory
- venv/ directory (if needed)
- Documentation files (*.md)
- Database files (*.db)

## Total Files to Remove: 32

After cleanup, the backend directory should only contain production-ready code and configuration files.