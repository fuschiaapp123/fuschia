#!/usr/bin/env python3
"""
Database viewer for Fuschia Platform
"""

import requests
import json
import sys
from typing import Dict, Any


def pretty_print(data: Dict[str, Any], title: str = ""):
    """Pretty print JSON data"""
    if title:
        print(f"\n📊 {title}")
        print("=" * (len(title) + 4))
    
    try:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:
        print(data)


def check_backend():
    """Check if backend is running"""
    try:
        response = requests.get("http://localhost:8000/api/v1/templates/test", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def inspect_database():
    """Get database overview"""
    try:
        response = requests.get("http://localhost:8000/api/v1/db/inspect")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def get_table_data(table_name: str, limit: int = 5):
    """Get data from a specific table"""
    try:
        response = requests.get(
            f"http://localhost:8000/api/v1/db/table/{table_name}",
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def main():
    print("🔍 Fuschia Database Inspector")
    print("============================")
    
    # Check backend
    print("📡 Checking backend connection...")
    if not check_backend():
        print("❌ Backend is not running on http://localhost:8000")
        print("💡 Please start the backend first: cd backend && python app.py")
        sys.exit(1)
    
    print("✅ Backend is running")
    
    # Get database overview
    print("\n📊 Inspecting database...")
    overview = inspect_database()
    
    if "error" in overview:
        print(f"❌ Failed to inspect database: {overview['error']}")
        sys.exit(1)
    
    # Display overview
    pretty_print(overview, "Database Overview")
    
    # Show table summaries
    if "tables" in overview:
        print(f"\n📋 Found {overview['total_tables']} tables:")
        print("=" * 30)
        
        for table_name, table_info in overview["tables"].items():
            if "error" not in table_info:
                print(f"• {table_name}: {table_info['row_count']} rows, {len(table_info['columns'])} columns")
            else:
                print(f"• {table_name}: Error - {table_info['error']}")
    
    # Show specific table data
    tables_to_show = ["users", "templates"]
    
    for table in tables_to_show:
        if table in overview.get("tables", {}):
            print(f"\n👀 {table.title()} Table Data:")
            print("=" * (len(table) + 12))
            
            table_data = get_table_data(table, limit=3)
            if "error" not in table_data:
                if table_data["data"]:
                    for i, row in enumerate(table_data["data"], 1):
                        print(f"\nRow {i}:")
                        for col, value in row.items():
                            # Truncate long values
                            if isinstance(value, str) and len(value) > 100:
                                value = value[:100] + "..."
                            print(f"  {col}: {value}")
                else:
                    print("  No data found")
            else:
                print(f"  Error: {table_data['error']}")
    
    print("\n🎉 Database inspection complete!")
    print("\n💡 Available API endpoints:")
    print("  - GET /api/v1/db/inspect - Database overview")
    print("  - GET /api/v1/db/table/{table_name} - Table data")
    print("  - Add ?limit=N&offset=M for pagination")


if __name__ == "__main__":
    main()