"""
LangGraph graph for generating insights for dashboard pages.
"""

import logging
from typing import Dict, Any, TypedDict, Annotated, List

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from app.core.config import settings
from app.services.rag_service import get_relevant_context
from app.services.analytics_service import (
    get_order_analytics,
    get_campaign_analytics,
    get_consumer_analytics,
    get_feedback_analytics,
    get_menu_events_analytics,
)
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

# Agent configuration
MODEL_NAME = "gpt-4o-mini"
MAX_TOKENS = 1000
TEMPERATURE = 0.7

# System prompt for insights generation
INSIGHTS_SYSTEM_PROMPT = """You are an AI assistant that generates concise, actionable insights for restaurant managers based on analytics data.

Your task:
- Analyze the provided analytics data
- Identify key trends, patterns, and opportunities
- Provide 2-3 actionable insights (each 1-2 sentences)
- Focus on what matters most for business decisions
- Be specific with numbers and metrics when available
- Suggest concrete next steps

Guidelines:
- Be concise and direct
- Prioritize insights that can drive action
- Highlight both opportunities and concerns
- Use the restaurant's context from RAG data when relevant

Format your response as a single paragraph with 2-3 insights separated by periods."""


class InsightsState(TypedDict):
    """State for insights generation graph."""
    page_type: str
    store_id: str
    analytics_data: Dict[str, Any]
    rag_context: str
    insight: str




def retrieve_rag_context(state: InsightsState) -> Dict[str, Any]:
    """Retrieve relevant RAG context for insights."""
    store_id = state.get("store_id", "")
    page_type = state.get("page_type", "")
    
    # Build query based on page type
    query = f"restaurant {page_type} analytics trends performance"
    
    try:
        context = get_relevant_context(
            store_id=store_id,
            query=query,
            top_k=3,
        )
        return {"rag_context": context}
    except Exception as e:
        logger.error(f"Error retrieving RAG context: {e}")
        return {"rag_context": ""}


def generate_insight(state: InsightsState) -> Dict[str, Any]:
    """Generate insight using LLM."""
    try:
        model = ChatOpenAI(
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            api_key=settings.OPENAI_API_KEY,
        )
        
        analytics_data = state.get("analytics_data", {})
        rag_context = state.get("rag_context", "")
        page_type = state.get("page_type", "")
        
        # Build prompt
        system_msg = SystemMessage(content=INSIGHTS_SYSTEM_PROMPT)
        
        data_summary = f"Analytics Data for {page_type}:\n{str(analytics_data)[:1000]}"
        
        if rag_context and not rag_context.startswith("Error"):
            context_section = f"\n\nRelevant Context:\n{rag_context}"
        else:
            context_section = ""
        
        user_prompt = f"{data_summary}{context_section}\n\nGenerate insights based on this data."
        user_msg = HumanMessage(content=user_prompt)
        
        # Generate insight
        response = model.invoke([system_msg, user_msg])
        insight_text = response.content if hasattr(response, "content") else str(response)
        
        return {"insight": insight_text}
    
    except Exception as e:
        logger.error(f"Error generating insight: {e}", exc_info=True)
        return {"insight": f"Unable to generate insights at this time. Error: {str(e)}"}


# Build the graph
def create_insights_graph() -> StateGraph:
    """Create the LangGraph insights generation graph."""
    workflow = StateGraph(InsightsState)
    
    # Add nodes
    workflow.add_node("retrieve_rag", retrieve_rag_context)
    workflow.add_node("generate", generate_insight)
    
    # Set entry point
    workflow.set_entry_point("retrieve_rag")
    
    # Add edges
    workflow.add_edge("retrieve_rag", "generate")
    workflow.add_edge("generate", END)
    
    return workflow


# Create the graph instance
insights_graph = create_insights_graph().compile()

logger.info("Insights generation graph initialized successfully")


async def generate_insight_for_page(
    store_id: str, page_type: str
) -> str:
    """
    Generate insight for a dashboard page.
    
    Args:
        store_id: Store identifier
        page_type: Type of page (orders, campaigns, consumers, feedbacks, menu_events)
    
    Returns:
        Generated insight text
    """
    try:
        # Retrieve analytics data
        async with AsyncSessionLocal() as session:
            if page_type == "orders":
                analytics_data = await get_order_analytics(session=session, store_id=store_id)
            elif page_type == "campaigns":
                analytics_data = await get_campaign_analytics(session=session, store_id=store_id)
            elif page_type == "consumers":
                analytics_data = await get_consumer_analytics(session=session, store_id=store_id)
            elif page_type == "feedbacks":
                analytics_data = await get_feedback_analytics(session=session, store_id=store_id)
            elif page_type == "menu_events":
                analytics_data = await get_menu_events_analytics(session=session, store_id=store_id)
            else:
                analytics_data = {}
        
        # Prepare initial state
        initial_state: InsightsState = {
            "page_type": page_type,
            "store_id": store_id,
            "analytics_data": analytics_data,
            "rag_context": "",
            "insight": "",
        }
        
        # Run the graph
        final_state = None
        async for event in insights_graph.astream(initial_state):
            for node_name, node_output in event.items():
                if node_name == "generate":
                    final_state = node_output
        
        # Extract insight
        if final_state and "insight" in final_state:
            return final_state["insight"]
        
        # Fallback
        return "Insights are being generated. Please check back shortly."
    
    except Exception as e:
        logger.error(f"Error generating insight: {e}", exc_info=True)
        return f"Unable to generate insights at this time. Please try again later."


__all__ = ["generate_insight_for_page", "insights_graph"]

