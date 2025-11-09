"""
LangGraph agent for restaurant management AI assistant.
"""

import logging
from typing import Dict, Any, List, TypedDict, Annotated
from datetime import datetime

from langchain_core.messages import BaseMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, add_messages

from app.core.config import settings
from app.graphs.tools.calculator import calculator_tool
from app.graphs.tools.analytics import (
    get_order_analytics_tool,
    get_campaign_analytics_tool,
    get_consumer_analytics_tool,
    get_feedback_analytics_tool,
    get_menu_events_analytics_tool,
    get_top_menu_items_tool,
)
from app.graphs.tools.rag import search_historical_data
from app.graphs.nodes.rag import retrieve_rag_context
from app.graphs.nodes.tools import create_tools_node_dynamic

logger = logging.getLogger(__name__)

# Agent configuration
MODEL_NAME = "gpt-5-mini"  # Use cost-effective model
MAX_TOKENS = 8000
TEMPERATURE = 0.7

# System prompt for restaurant management assistant
SYSTEM_PROMPT = """You are an AI assistant helping restaurant managers make data-driven decisions.

Your capabilities:
- Analyze order trends, revenue, and customer behavior
- Review campaign performance and marketing metrics
- Understand customer feedback and satisfaction
- Access historical data through semantic search (RAG)
- Perform calculations and data analysis

Guidelines:
- Be concise and actionable in your responses
- Use specific numbers and metrics when available
- Suggest concrete improvements based on data
- If you don't have enough information, ask clarifying questions
- Always consider the restaurant's context and constraints
- You can call analytics tools without specifying store_id - it will be automatically provided
- Make sure to use the calculator tool for calculations and return the result with proper punctuation and formatting (one hundred and twenty = R$ 120,00)

When answering questions:
1. Use RAG search to find relevant historical context
2. Query analytics tools for current metrics (store_id is automatically included)
3. Synthesize information into actionable insights
4. Provide clear recommendations

Remember: You're helping a restaurant manager, so focus on practical, implementable advice."""


class AgentState(TypedDict):
    """State for the LangGraph agent."""

    messages: Annotated[List[BaseMessage], add_messages]
    store_id: str
    rag_context: str


def create_agent_model() -> ChatOpenAI:
    """Create the LLM model for the agent."""
    return ChatOpenAI(
        model=MODEL_NAME,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        api_key=settings.OPENAI_API_KEY,
    )


def create_system_message_with_context(
    rag_context: str, store_id: str = ""
) -> SystemMessage:
    """Create system message with RAG context injected."""
    if rag_context and rag_context.strip() and not rag_context.startswith("Error"):
        context_section = f"\n\nRelevant Context from Restaurant Data:\n{rag_context}\n"
    else:
        context_section = "\n\nNote: No specific context retrieved. Use your general knowledge and available tools.\n"

    localize = "IMPORTANT: Always answer in brazilian portuguese."

    date_time = (
        f"The current date and time is {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
    )

    full_prompt = SYSTEM_PROMPT + context_section + localize + date_time
    return SystemMessage(content=full_prompt)


def agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Main agent node that processes messages with tools.
    """
    try:
        model = create_agent_model()
        messages = state.get("messages", [])
        rag_context = state.get("rag_context", "")
        store_id = state.get("store_id", "")

        # Prepare messages with system prompt including RAG context and store_id
        system_msg = create_system_message_with_context(rag_context, store_id)
        agent_messages = [system_msg] + messages

        # Debug message ordering to catch malformed histories
        roles = [getattr(msg, "type", type(msg).__name__) for msg in agent_messages]
        logger.info(f"Agent invoking with message roles: {roles}")
        for idx, msg in enumerate(agent_messages):
            logger.info(
                "Message %s -> type=%s, class=%s",
                idx,
                getattr(msg, "type", type(msg).__name__),
                msg.__class__.__name__,
            )

        # Get available tools
        tools = [
            calculator_tool,
            get_order_analytics_tool,
            get_campaign_analytics_tool,
            get_consumer_analytics_tool,
            get_feedback_analytics_tool,
            get_menu_events_analytics_tool,
            get_top_menu_items_tool,
            search_historical_data,
        ]

        # Bind tools to model
        model_with_tools = model.bind_tools(tools)

        # Get response from model
        response = model_with_tools.invoke(agent_messages)

        return {"messages": [response]}

    except Exception as e:
        logger.error(f"Error in agent node: {e}", exc_info=True)
        error_message = AIMessage(
            content=f"I apologize, but I encountered an error processing your request: {str(e)}. Please try again."
        )
        return {"messages": [error_message]}


def should_continue(state: AgentState) -> str:
    """
    Determine if the agent should continue or end.
    """
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None

    if last_message and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "end"


# Tools node will be created dynamically to inject store_id


# Build the graph
def create_graph() -> StateGraph:
    """Create the LangGraph agent graph."""
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("retrieve_rag", retrieve_rag_context)
    workflow.add_node("agent", agent_node)
    workflow.add_node(
        "tools", create_tools_node_dynamic
    )  # Dynamic node that injects store_id

    # Set entry point
    workflow.set_entry_point("retrieve_rag")

    # Add edges
    workflow.add_edge("retrieve_rag", "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        },
    )
    workflow.add_edge("tools", "agent")

    return workflow


# Create the graph instance relying on platform-managed persistence
graph = create_graph().compile()

logger.info("LangGraph agent initialized successfully")


__all__ = ["graph", "AgentState", "create_graph"]
