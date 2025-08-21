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
        
        # In-memory storage for tools (in production, use database)
        self.tools: Dict[str, ToolFunction] = {}
        self.agent_associations: Dict[str, List[AgentToolAssociation]] = {}
        self.execution_logs: List[ToolExecutionLog] = []
        
        # Compiled functions cache
        self.compiled_functions: Dict[str, Callable] = {}
        
        # Load tools from storage on startup
        self._load_tools_from_storage()
        
        # Register default tools
        self._register_default_tools()
    
    def _load_tools_from_storage(self) -> None:
        """Load tools from persistent storage"""
        try:
            # For now, use simple file storage
            storage_path = Path("tools_registry.json")
            if storage_path.exists():
                with open(storage_path, 'r') as f:
                    data = json.load(f)
                    for tool_data in data.get('tools', []):
                        tool = ToolFunction(**tool_data)
                        self.tools[tool.id] = tool
                        self._compile_tool_function(tool)
                self.logger.info("Loaded tools from storage", count=len(self.tools))
        except Exception as e:
            self.logger.error("Failed to load tools from storage", error=str(e))
    
    def _save_tools_to_storage(self) -> None:
        """Save tools to persistent storage"""
        try:
            storage_path = Path("tools_registry.json")
            data = {
                'tools': [tool.dict() for tool in self.tools.values()],
                'updated_at': datetime.utcnow().isoformat()
            }
            with open(storage_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            self.logger.info("Saved tools to storage", count=len(self.tools))
        except Exception as e:
            self.logger.error("Failed to save tools to storage", error=str(e))
    
    def _register_default_tools(self) -> None:
        """Register some default useful tools"""
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
                self.register_tool(request, created_by="system")
            except Exception as e:
                self.logger.error("Failed to register default tool", tool=tool_def.get("name"), error=str(e))
    
    def register_tool(self, request: ToolRegistryRequest, created_by: str) -> ToolRegistryResponse:
        """Register a new tool"""
        try:
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
            
            # Create tool object
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
            
            # Compile and store
            if self._compile_tool_function(tool):
                self.tools[tool_id] = tool
                self._save_tools_to_storage()
                
                self.logger.info("Tool registered successfully", tool_id=tool_id, name=request.name)
                return ToolRegistryResponse(
                    success=True,
                    message="Tool registered successfully",
                    tool=tool
                )
            else:
                return ToolRegistryResponse(
                    success=False,
                    message="Failed to compile function",
                    errors=["Function compilation failed"]
                )
                
        except Exception as e:
            self.logger.error("Failed to register tool", error=str(e))
            return ToolRegistryResponse(
                success=False,
                message=f"Registration failed: {str(e)}",
                errors=[str(e)]
            )

    def update_tool(self, tool_id: str, request: ToolRegistryRequest, updated_by: str) -> ToolRegistryResponse:
        """Update an existing tool"""
        try:
            # Check if tool exists
            existing_tool = self.get_tool(tool_id)
            if not existing_tool:
                return ToolRegistryResponse(
                    success=False,
                    message="Tool not found",
                    errors=[f"Tool {tool_id} does not exist"]
                )
            
            # Check permissions (only creator or admin can update)
            # Note: For now, we skip permission check. In production, add user role check
            
            # Validate and compile function
            validation_result = self._validate_function_code(request.function_code, request.name)
            if not validation_result['valid']:
                return ToolRegistryResponse(
                    success=False,
                    message="Function validation failed",
                    errors=validation_result['errors']
                )
            
            # Update tool object with new data
            updated_tool = ToolFunction(
                id=tool_id,  # Keep the same ID
                name=request.name,
                description=request.description,
                category=request.category,
                function_code=request.function_code,
                parameters=request.parameters,
                return_type=request.return_type,
                status=ToolStatus.ACTIVE,
                created_by=existing_tool.created_by,  # Keep original creator
                created_at=existing_tool.created_at,  # Keep original creation time
                updated_at=datetime.utcnow(),  # Update the timestamp
                version=existing_tool.version + 1,  # Increment version
                tags=request.tags
            )
            
            # Compile and store
            if self._compile_tool_function(updated_tool):
                self.tools[tool_id] = updated_tool
                self._save_tools_to_storage()
                
                self.logger.info("Tool updated successfully", tool_id=tool_id, name=request.name, version=updated_tool.version)
                return ToolRegistryResponse(
                    success=True,
                    message="Tool updated successfully",
                    tool=updated_tool
                )
            else:
                return ToolRegistryResponse(
                    success=False,
                    message="Failed to compile updated function",
                    errors=["Function compilation failed"]
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
            
            # Log execution
            log_entry = ToolExecutionLog(
                id=log_id,
                tool_id=request.tool_id,
                agent_id=request.agent_id or "unknown",
                execution_id=request.execution_id or str(uuid.uuid4()),
                input_parameters=request.parameters,
                output_result=result,
                execution_time_ms=execution_time_ms,
                success=True,
                error_message=None
            )
            self.execution_logs.append(log_entry)
            
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
            
            # Log failed execution
            log_entry = ToolExecutionLog(
                id=log_id,
                tool_id=request.tool_id,
                agent_id=request.agent_id or "unknown",
                execution_id=request.execution_id or str(uuid.uuid4()),
                input_parameters=request.parameters,
                output_result=None,
                execution_time_ms=execution_time_ms,
                success=False,
                error_message=error_message
            )
            self.execution_logs.append(log_entry)
            
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
        """Delete a tool"""
        if tool_id in self.tools:
            del self.tools[tool_id]
            if tool_id in self.compiled_functions:
                del self.compiled_functions[tool_id]
            self._save_tools_to_storage()
            self.logger.info("Tool deleted", tool_id=tool_id)
            return True
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