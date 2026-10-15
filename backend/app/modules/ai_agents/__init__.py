"""
AeroAI AI Agents Module.
Houses the Stage 7 AeroAI Unified AI Agent, tool registry, router, and audit logger.
"""

from app.modules.ai_agents.tools import tool_registry, BaseAgentTool
from app.modules.ai_agents.router import intent_router, RoutingDecision
from app.modules.ai_agents.formatter import response_formatter
from app.modules.ai_agents.logger import agent_audit_logger
from app.modules.ai_agents.unified_agent import aeroai_agent, AeroAIUnifiedAgent, AgentResponse

__all__ = [
    "aeroai_agent",
    "AeroAIUnifiedAgent",
    "AgentResponse",
    "tool_registry",
    "intent_router",
    "response_formatter",
    "agent_audit_logger"
]
