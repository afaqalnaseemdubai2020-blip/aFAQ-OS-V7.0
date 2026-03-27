from fastapi import APIRouter
from app.modules.agents.router import agents_router

def get_router() -> APIRouter:
    return agents_router

__all__ = ["get_router", "agents_router"]
