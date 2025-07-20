# Import to ensure UserTable is registered with Base metadata
from .postgres import UserTable, Base, engine, init_db, test_db_connection

__all__ = ['UserTable', 'Base', 'engine', 'init_db', 'test_db_connection']