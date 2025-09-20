"""
Tool Registry Service for DSPy function calling
"""

import os
import json
import uuid
import time
import inspect
import hashlib
import tempfile
import traceback
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import structlog
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from app.db.postgres import AsyncSessionLocal, ToolFunctionTable, AgentToolAssociationTable, ToolExecutionLogTable

from app.models.tool_registry import (
    ToolFunction, 
    AgentToolAssociation, 
    ToolExecutionLog,
    ToolRegistryRequest,
    ToolRegistryResponse,
    ToolExecutionRequest,
    ToolExecutionResponse,
    ToolStatus,
    ToolCategory,
    FunctionParameter
)

logger = structlog.get_logger()


class ToolRegistryService:
    """Service for managing and executing tools for DSPy agents"""
    
    def __init__(self):
        self.logger = logger.bind(service="ToolRegistryService")
        
        # In-memory cache for tools (will be loaded from database)
        self.tools: Dict[str, ToolFunction] = {}
        self.agent_associations: Dict[str, List[AgentToolAssociation]] = {}
        
        # Compiled functions cache
        self.compiled_functions: Dict[str, Callable] = {}
        
        # Initialize database and load tools
        self._initialize_service()
    
    def _initialize_service(self) -> None:
        """Initialize service with database migration and setup"""
        try:
            # Try to load tools from database first
            import asyncio
            if asyncio._get_running_loop() is not None:
                # We're in async context, schedule the migration
                asyncio.create_task(self._migrate_and_load())
            else:
                # We're in sync context, run async migration
                asyncio.run(self._migrate_and_load())
        except Exception as e:
            self.logger.error("Failed to initialize service", error=str(e))
    
    async def _migrate_and_load(self) -> None:
        """Migrate from JSON file and load tools from database"""
        try:
            await self._migrate_from_json_if_needed()
            await self._load_tools_from_database()
            await self._register_default_tools_async()
        except Exception as e:
            self.logger.error("Migration and load failed", error=str(e))
    
    async def _migrate_from_json_if_needed(self) -> None:
        """Migrate tools from JSON file to database if needed"""
        json_path = Path("tools_registry.json")
        
        # Check if database is empty and JSON file exists
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(ToolFunctionTable).limit(1))
            db_has_tools = result.first() is not None
            
            if not db_has_tools and json_path.exists():
                self.logger.info("Migrating tools from JSON file to database")
                
                with open(json_path, 'r') as f:
                    data = json.load(f)
                    
                for tool_data in data.get('tools', []):
                    try:
                        # Convert to database model
                        db_tool = ToolFunctionTable(
                            id=tool_data['id'],
                            name=tool_data['name'],
                            description=tool_data['description'],
                            category=tool_data.get('category', 'custom'),
                            function_code=tool_data['function_code'],
                            parameters=tool_data.get('parameters', []),
                            return_type=tool_data.get('return_type', 'Any'),
                            status=tool_data.get('status', 'active'),
                            created_by=tool_data.get('created_by', 'system'),
                            version=tool_data.get('version', 1),
                            tags=tool_data.get('tags', []),
                            created_at=datetime.fromisoformat(tool_data['created_at']) if tool_data.get('created_at') else datetime.utcnow(),
                            updated_at=datetime.fromisoformat(tool_data['updated_at']) if tool_data.get('updated_at') else datetime.utcnow()
                        )
                        session.add(db_tool)
                    except Exception as e:
                        self.logger.error("Failed to migrate tool", tool_id=tool_data.get('id'), error=str(e))
                
                await session.commit()
                self.logger.info("Migration completed", migrated_tools=len(data.get('tools', [])))
                
                # Backup and remove JSON file
                backup_path = json_path.with_suffix('.json.backup')
                json_path.rename(backup_path)
                self.logger.info("JSON file backed up and removed", backup_path=str(backup_path))
    
    async def _load_tools_from_database(self) -> None:
        """Load tools from database into memory cache"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(ToolFunctionTable))
                db_tools = result.scalars().all()
                
                for db_tool in db_tools:
                    tool = ToolFunction(
                        id=db_tool.id,
                        name=db_tool.name,
                        description=db_tool.description,
                        category=db_tool.category,
                        function_code=db_tool.function_code,
                        parameters=db_tool.parameters or [],
                        return_type=db_tool.return_type,
                        status=db_tool.status,
                        created_by=db_tool.created_by,
                        created_at=db_tool.created_at,
                        updated_at=db_tool.updated_at,
                        version=db_tool.version,
                        tags=db_tool.tags or []
                    )
                    self.tools[tool.id] = tool
                    self._compile_tool_function(tool)
                
                self.logger.info("Loaded tools from database", count=len(self.tools))
        except Exception as e:
            self.logger.error("Failed to load tools from database", error=str(e))
    
    async def _log_execution_async(self, log_id: str, tool_id: str, agent_id: str, execution_id: str,
                                 input_parameters: Dict[str, Any], output_result: Any, 
                                 execution_time_ms: int, success: bool, error_message: Optional[str] = None) -> None:
        """Log tool execution to database asynchronously"""
        try:
            async with AsyncSessionLocal() as session:
                log_entry = ToolExecutionLogTable(
                    id=log_id,
                    tool_id=tool_id,
                    agent_id=agent_id,
                    execution_id=execution_id,
                    input_parameters=input_parameters,
                    output_result=output_result,
                    execution_time_ms=execution_time_ms,
                    success=success,
                    error_message=error_message
                )
                session.add(log_entry)
                await session.commit()
        except Exception as e:
            self.logger.error("Failed to save execution log to database", 
                            log_id=log_id, tool_id=tool_id, error=str(e))
    
    async def _register_default_tools_async(self) -> None:
        """Register some default useful tools asynchronously"""
        default_tools = [
            {
                "name": "get_current_time",
                "description": "Get the current timestamp",
                "category": ToolCategory.DATA_RETRIEVAL,
                "function_code": """def get_current_time():
    \"\"\"Get the current timestamp\"\"\"
    from datetime import datetime
    return datetime.utcnow().isoformat()""",
                "parameters": [],
                "return_type": "str",
                "tags": ["time", "utility"]
            },
            {
                "name": "calculate_sum",
                "description": "Calculate the sum of two numbers",
                "category": ToolCategory.CALCULATION,
                "function_code": """def calculate_sum(a: float, b: float) -> float:
    \"\"\"Calculate the sum of two numbers\"\"\"
    return a + b""",
                "parameters": [
                    FunctionParameter(name="a", type="float", description="First number", required=True),
                    FunctionParameter(name="b", type="float", description="Second number", required=True)
                ],
                "return_type": "float",
                "tags": ["math", "calculation"]
            },
            {
                "name": "validate_email",
                "description": "Validate email address format",
                "category": ToolCategory.VALIDATION,
                "function_code": """def validate_email(email: str) -> bool:
    \"\"\"Validate email address format\"\"\"
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))""",
                "parameters": [
                    FunctionParameter(name="email", type="str", description="Email address to validate", required=True)
                ],
                "return_type": "bool",
                "tags": ["validation", "email"]
            }
        ]
        
        for tool_def in default_tools:
            try:
                request = ToolRegistryRequest(**tool_def)
                await self.register_tool_async(request, created_by="system")
            except Exception as e:
                self.logger.error("Failed to register default tool", tool=tool_def.get("name"), error=str(e))
    
    def register_tool(self, request: ToolRegistryRequest, created_by: str) -> ToolRegistryResponse:
        """Register a new tool (sync wrapper for async method)"""
        import asyncio
        return asyncio.run(self.register_tool_async(request, created_by))
    
    async def register_tool_async(self, request: ToolRegistryRequest, created_by: str) -> ToolRegistryResponse:
        """Register a new tool asynchronously"""
        try:
            # Check if tool with same name already exists
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ToolFunctionTable).where(ToolFunctionTable.name == request.name)
                )
                existing_tool = result.first()
                if existing_tool:
                    return ToolRegistryResponse(
                        success=False,
                        message=f"Tool with name '{request.name}' already exists",
                        errors=[f"Tool '{request.name}' is already registered"]
                    )
            
            # Generate unique ID
            tool_id = str(uuid.uuid4())
            
            # Validate and compile function
            validation_result = self._validate_function_code(request.function_code, request.name)
            if not validation_result['valid']:
                return ToolRegistryResponse(
                    success=False,
                    message="Function validation failed",
                    errors=validation_result['errors']
                )
            
            # Create tool object for memory cache
            tool = ToolFunction(
                id=tool_id,
                name=request.name,
                description=request.description,
                category=request.category,
                function_code=request.function_code,
                parameters=request.parameters,
                return_type=request.return_type,
                status=ToolStatus.ACTIVE,
                created_by=created_by,
                tags=request.tags
            )
            
            # Compile function
            if not self._compile_tool_function(tool):
                return ToolRegistryResponse(
                    success=False,
                    message="Failed to compile function",
                    errors=["Function compilation failed"]
                )
            
            # Save to database
            async with AsyncSessionLocal() as session:
                db_tool = ToolFunctionTable(
                    id=tool_id,
                    name=request.name,
                    description=request.description,
                    category=request.category.value if isinstance(request.category, ToolCategory) else request.category,
                    function_code=request.function_code,
                    parameters=[param.dict() if hasattr(param, 'dict') else param for param in request.parameters],
                    return_type=request.return_type,
                    status=ToolStatus.ACTIVE.value,
                    created_by=created_by,
                    version=1,
                    tags=request.tags
                )
                session.add(db_tool)
                await session.commit()
            
            # Add to memory cache
            self.tools[tool_id] = tool
            
            self.logger.info("Tool registered successfully", tool_id=tool_id, name=request.name)
            return ToolRegistryResponse(
                success=True,
                message="Tool registered successfully",
                tool=tool
            )
                
        except Exception as e:
            self.logger.error("Failed to register tool", error=str(e))
            return ToolRegistryResponse(
                success=False,
                message=f"Registration failed: {str(e)}",
                errors=[str(e)]
            )

    def update_tool(self, tool_id: str, request: ToolRegistryRequest, updated_by: str) -> ToolRegistryResponse:
        """Update an existing tool (sync wrapper for async method)"""
        import asyncio
        return asyncio.run(self.update_tool_async(tool_id, request, updated_by))
    
    async def update_tool_async(self, tool_id: str, request: ToolRegistryRequest, updated_by: str) -> ToolRegistryResponse:
        """Update an existing tool asynchronously"""
        try:
            # Check if tool exists in database
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ToolFunctionTable).where(ToolFunctionTable.id == tool_id)
                )
                db_tool = result.scalar_one_or_none()
                if not db_tool:
                    return ToolRegistryResponse(
                        success=False,
                        message="Tool not found",
                        errors=[f"Tool {tool_id} does not exist"]
                    )
                
                # Check if new name conflicts with another tool
                if request.name != db_tool.name:
                    name_check = await session.execute(
                        select(ToolFunctionTable).where(
                            ToolFunctionTable.name == request.name,
                            ToolFunctionTable.id != tool_id
                        )
                    )
                    if name_check.first():
                        return ToolRegistryResponse(
                            success=False,
                            message=f"Tool with name '{request.name}' already exists",
                            errors=[f"Another tool with name '{request.name}' is already registered"]
                        )
            
            # Validate and compile function
            validation_result = self._validate_function_code(request.function_code, request.name)
            if not validation_result['valid']:
                return ToolRegistryResponse(
                    success=False,
                    message="Function validation failed",
                    errors=validation_result['errors']
                )
            
            # Create updated tool object
            updated_tool = ToolFunction(
                id=tool_id,
                name=request.name,
                description=request.description,
                category=request.category,
                function_code=request.function_code,
                parameters=request.parameters,
                return_type=request.return_type,
                status=ToolStatus.ACTIVE,
                created_by=db_tool.created_by,
                created_at=db_tool.created_at,
                updated_at=datetime.utcnow(),
                version=db_tool.version + 1,
                tags=request.tags
            )
            
            # Compile function
            if not self._compile_tool_function(updated_tool):
                return ToolRegistryResponse(
                    success=False,
                    message="Failed to compile updated function",
                    errors=["Function compilation failed"]
                )
            
            # Update in database
            async with AsyncSessionLocal() as session:
                await session.execute(
                    update(ToolFunctionTable)
                    .where(ToolFunctionTable.id == tool_id)
                    .values(
                        name=request.name,
                        description=request.description,
                        category=request.category.value if isinstance(request.category, ToolCategory) else request.category,
                        function_code=request.function_code,
                        parameters=[param.dict() if hasattr(param, 'dict') else param for param in request.parameters],
                        return_type=request.return_type,
                        tags=request.tags,
                        version=db_tool.version + 1,
                        updated_at=datetime.utcnow()
                    )
                )
                await session.commit()
            
            # Update memory cache
            self.tools[tool_id] = updated_tool
            
            self.logger.info("Tool updated successfully", tool_id=tool_id, name=request.name, version=updated_tool.version)
            return ToolRegistryResponse(
                success=True,
                message="Tool updated successfully",
                tool=updated_tool
            )
                
        except Exception as e:
            self.logger.error("Failed to update tool", tool_id=tool_id, error=str(e))
            return ToolRegistryResponse(
                success=False,
                message=f"Update failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _validate_function_code(self, code: str, expected_name: str) -> Dict[str, Any]:
        """Validate function code"""
        errors = []
        
        try:
            # Parse the code
            import ast
            tree = ast.parse(code)
            
            # Find function definitions
            functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            if not functions:
                errors.append("No function definition found")
                return {'valid': False, 'errors': errors}
            
            # Check if expected function name exists
            function_names = [f.name for f in functions]
            if expected_name not in function_names:
                errors.append(f"Function '{expected_name}' not found. Found: {function_names}")
            
            # Basic security checks
            dangerous_imports = ['os', 'subprocess', 'sys', 'eval', 'exec', '__import__']
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in dangerous_imports:
                            errors.append(f"Dangerous import detected: {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module in dangerous_imports:
                        errors.append(f"Dangerous import detected: {node.module}")
            
            # Check for dangerous function calls
            dangerous_calls = ['eval', 'exec', 'open', '__import__']
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id in dangerous_calls:
                        errors.append(f"Dangerous function call detected: {node.func.id}")
            
        except SyntaxError as e:
            errors.append(f"Syntax error: {str(e)}")
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return {'valid': len(errors) == 0, 'errors': errors}
    
    def _compile_tool_function(self, tool: ToolFunction) -> bool:
        """Compile and cache tool function"""
        try:
            # Create a safe execution environment
            safe_globals = {
                '__builtins__': {
                    'len': len, 'str': str, 'int': int, 'float': float, 'bool': bool,
                    'list': list, 'dict': dict, 'tuple': tuple, 'set': set,
                    'min': min, 'max': max, 'sum': sum, 'abs': abs,
                    'round': round, 'sorted': sorted, 'reversed': reversed,
                    'range': range, 'enumerate': enumerate, 'zip': zip,
                    'isinstance': isinstance, 'hasattr': hasattr, 'getattr': getattr,
                    'ValueError': ValueError, 'TypeError': TypeError, 'KeyError': KeyError,
                    'IndexError': IndexError, 'AttributeError': AttributeError
                },
                # Safe imports
                'datetime': __import__('datetime'),
                're': __import__('re'),
                'json': __import__('json'),
                'math': __import__('math'),
                'random': __import__('random')
            }
            print(f"-=->>> Compiling tool function: {tool.name}, tool code: {tool.function_code}")
            # Execute the function code
            exec(tool.function_code, safe_globals)
            
            # Extract the compiled function
            if tool.name in safe_globals:
                self.compiled_functions[tool.id] = safe_globals[tool.name]
                self.logger.info("Tool function compiled successfully", tool_id=tool.id, name=tool.name)
                return True
            else:
                self.logger.error("Function not found after compilation", tool_id=tool.id, name=tool.name)
                return False
                
        except Exception as e:
            self.logger.error("Failed to compile tool function", tool_id=tool.id, error=str(e))
            return False
    
    def execute_tool(self, request: ToolExecutionRequest) -> ToolExecutionResponse:
        """Execute a tool function"""
        start_time = time.time()
        log_id = str(uuid.uuid4())
        
        try:
            # Check if tool exists
            if request.tool_id not in self.tools:
                return ToolExecutionResponse(
                    success=False,
                    result=None,
                    execution_time_ms=0,
                    error_message=f"Tool {request.tool_id} not found"
                )
            
            tool = self.tools[request.tool_id]
            
            # Check if tool is active
            if tool.status != ToolStatus.ACTIVE:
                return ToolExecutionResponse(
                    success=False,
                    result=None,
                    execution_time_ms=0,
                    error_message=f"Tool {tool.name} is not active"
                )
            
            # Get compiled function
            if request.tool_id not in self.compiled_functions:
                self._compile_tool_function(tool)
                if request.tool_id not in self.compiled_functions:
                    return ToolExecutionResponse(
                        success=False,
                        result=None,
                        execution_time_ms=0,
                        error_message="Tool function compilation failed"
                    )
            
            func = self.compiled_functions[request.tool_id]
            
            # Validate parameters
            validation_result = self._validate_execution_parameters(tool, request.parameters)
            if not validation_result['valid']:
                return ToolExecutionResponse(
                    success=False,
                    result=None,
                    execution_time_ms=0,
                    error_message=f"Parameter validation failed: {validation_result['error']}"
                )
            
            # Execute function with timeout
            result = self._execute_with_timeout(func, request.parameters, timeout=30)
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Log execution to database
            try:
                import asyncio
                asyncio.create_task(self._log_execution_async(
                    log_id=log_id,
                    tool_id=request.tool_id,
                    agent_id=request.agent_id or "unknown",
                    execution_id=request.execution_id or str(uuid.uuid4()),
                    input_parameters=request.parameters,
                    output_result=result,
                    execution_time_ms=int(execution_time_ms),
                    success=True,
                    error_message=None
                ))
            except Exception as e:
                self.logger.warning("Failed to log execution to database", error=str(e))
            
            self.logger.info(
                "Tool executed successfully",
                tool_id=request.tool_id,
                tool_name=tool.name,
                execution_time_ms=execution_time_ms
            )
            
            return ToolExecutionResponse(
                success=True,
                result=result,
                execution_time_ms=execution_time_ms,
                log_id=log_id
            )
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            error_message = str(e)
            
            # Log failed execution to database
            try:
                import asyncio
                asyncio.create_task(self._log_execution_async(
                    log_id=log_id,
                    tool_id=request.tool_id,
                    agent_id=request.agent_id or "unknown",
                    execution_id=request.execution_id or str(uuid.uuid4()),
                    input_parameters=request.parameters,
                    output_result=None,
                    execution_time_ms=int(execution_time_ms),
                    success=False,
                    error_message=error_message
                ))
            except Exception as e:
                self.logger.warning("Failed to log failed execution to database", error=str(e))
            
            self.logger.error("Tool execution failed", tool_id=request.tool_id, error=error_message)
            
            return ToolExecutionResponse(
                success=False,
                result=None,
                execution_time_ms=execution_time_ms,
                error_message=error_message,
                log_id=log_id
            )
    
    def _validate_execution_parameters(self, tool: ToolFunction, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate execution parameters against tool definition"""
        try:
            # Check required parameters
            for param in tool.parameters:
                if param.required and param.name not in parameters:
                    return {
                        'valid': False,
                        'error': f"Required parameter '{param.name}' is missing"
                    }
            
            # Type validation (basic)
            for param_name, param_value in parameters.items():
                param_def = next((p for p in tool.parameters if p.name == param_name), None)
                if param_def:
                    expected_type = param_def.type.lower()
                    if expected_type == 'str' and not isinstance(param_value, str):
                        return {
                            'valid': False,
                            'error': f"Parameter '{param_name}' should be string, got {type(param_value).__name__}"
                        }
                    elif expected_type == 'int' and not isinstance(param_value, int):
                        return {
                            'valid': False,
                            'error': f"Parameter '{param_name}' should be integer, got {type(param_value).__name__}"
                        }
                    elif expected_type == 'float' and not isinstance(param_value, (int, float)):
                        return {
                            'valid': False,
                            'error': f"Parameter '{param_name}' should be number, got {type(param_value).__name__}"
                        }
                    elif expected_type == 'bool' and not isinstance(param_value, bool):
                        return {
                            'valid': False,
                            'error': f"Parameter '{param_name}' should be boolean, got {type(param_value).__name__}"
                        }
            
            return {'valid': True, 'error': None}
            
        except Exception as e:
            return {'valid': False, 'error': f"Validation error: {str(e)}"}
    
    def _execute_with_timeout(self, func: Callable, parameters: Dict[str, Any], timeout: int = 30) -> Any:
        """Execute function with timeout protection"""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Function execution timed out after {timeout} seconds")
        
        # Set timeout
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        
        try:
            # Execute function
            result = func(**parameters)
            return result
        finally:
            # Clear timeout
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    
    def get_tools(self, category: Optional[ToolCategory] = None, status: Optional[ToolStatus] = None) -> List[ToolFunction]:
        """Get list of tools with optional filtering"""
        tools = list(self.tools.values())
        
        if category:
            tools = [t for t in tools if t.category == category]
        
        if status:
            tools = [t for t in tools if t.status == status]
        
        return sorted(tools, key=lambda x: x.name)
    
    def get_tool(self, tool_id: str) -> Optional[ToolFunction]:
        """Get a specific tool by ID"""
        return self.tools.get(tool_id)
    
    def delete_tool(self, tool_id: str) -> bool:
        """Delete a tool (sync wrapper for async method)"""
        import asyncio
        return asyncio.run(self.delete_tool_async(tool_id))
    
    async def delete_tool_async(self, tool_id: str) -> bool:
        """Delete a tool asynchronously"""
        try:
            # Check if tool exists
            if tool_id not in self.tools:
                return False
            
            # Delete from database
            async with AsyncSessionLocal() as session:
                await session.execute(
                    delete(ToolFunctionTable).where(ToolFunctionTable.id == tool_id)
                )
                await session.commit()
            
            # Remove from memory cache
            del self.tools[tool_id]
            if tool_id in self.compiled_functions:
                del self.compiled_functions[tool_id]
            
            self.logger.info("Tool deleted", tool_id=tool_id)
            return True
            
        except Exception as e:
            self.logger.error("Failed to delete tool", tool_id=tool_id, error=str(e))
            return False
    
    def associate_tool_with_agent(self, agent_id: str, tool_id: str, enabled: bool = True, priority: int = 0) -> bool:
        """Associate a tool with an agent"""
        if tool_id not in self.tools:
            return False
        
        association = AgentToolAssociation(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            tool_id=tool_id,
            enabled=enabled,
            priority=priority
        )
        
        if agent_id not in self.agent_associations:
            self.agent_associations[agent_id] = []
        
        # Remove existing association if any
        self.agent_associations[agent_id] = [
            a for a in self.agent_associations[agent_id] if a.tool_id != tool_id
        ]
        
        # Add new association
        self.agent_associations[agent_id].append(association)
        
        self.logger.info("Tool associated with agent", agent_id=agent_id, tool_id=tool_id)
        return True
    
    def get_agent_tools(self, agent_id: str) -> List[ToolFunction]:
        """Get tools associated with an agent"""
        logger.info(f"Retrieving tools for agent association: {self.agent_associations}")
        if agent_id not in self.agent_associations:
            return []
        
        tool_ids = [
            assoc.tool_id for assoc in self.agent_associations[agent_id] 
            if assoc.enabled
        ]
        
        return [self.tools[tool_id] for tool_id in tool_ids if tool_id in self.tools]
    
    def get_tools_for_dspy(self, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tools formatted for DSPy function calling"""
        if agent_id:
            tools = self.get_agent_tools(agent_id)
        else:
            tools = self.get_tools(status=ToolStatus.ACTIVE)
        
        dspy_tools = []
        for tool in tools:
            tool_spec = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
            
            # Add parameters
            for param in tool.parameters:
                tool_spec["function"]["parameters"]["properties"][param.name] = {
                    "type": param.type,
                    "description": param.description
                }
                if param.required:
                    tool_spec["function"]["parameters"]["required"].append(param.name)
            
            dspy_tools.append(tool_spec)
        
        return dspy_tools


# Global service instance
tool_registry_service = ToolRegistryService()