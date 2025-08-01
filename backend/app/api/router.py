from fastapi import APIRouter
from app.api.endpoints import auth, users, knowledge, chat, servicenow, workflows, workflow_execution, workflow_executions, agents, database, websocket

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(servicenow.router, prefix="/servicenow", tags=["servicenow"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(workflow_execution.router, prefix="/workflow-execution", tags=["workflow-execution"])
api_router.include_router(workflow_executions.router, prefix="/executions", tags=["workflow-executions"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(database.router, prefix="/database", tags=["database"])
api_router.include_router(websocket.router, tags=["websocket"])