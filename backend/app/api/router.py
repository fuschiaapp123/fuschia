from fastapi import APIRouter
from app.api.endpoints import auth, users, knowledge, chat, servicenow, workflows, workflow_execution

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(servicenow.router, prefix="/servicenow", tags=["servicenow"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(workflow_execution.router, prefix="/workflow-execution", tags=["workflow-execution"])