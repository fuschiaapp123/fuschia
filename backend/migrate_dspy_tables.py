"""
Migration script to create DSPy evaluation tables
Run this script to add DSPy evaluation persistence to the database
"""

import asyncio
from app.db.postgres import engine, Base, DSPyEvaluationConfigTable, DSPyEvaluationResultTable


async def create_dspy_tables():
    """Create DSPy evaluation tables in the database"""
    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
        print("✅ DSPy evaluation tables created successfully!")
        print("   - dspy_evaluation_configs")
        print("   - dspy_evaluation_results")


if __name__ == "__main__":
    print("Creating DSPy evaluation tables...")
    asyncio.run(create_dspy_tables())
    print("\nMigration complete! DSPy examples will now persist across server restarts.")
