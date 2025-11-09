"""
Custom tool node that injects store_id from state into tool calls.
"""

import logging
from typing import Dict, Any

from langchain_core.messages import ToolMessage, AIMessage
from langgraph.prebuilt import ToolNode

logger = logging.getLogger(__name__)


def create_tools_node_with_store_id(store_id: str):
    """
    Create a ToolNode that automatically injects store_id into tool calls.

    Args:
        store_id: Store ID to inject into tool calls

    Returns:
        ToolNode instance
    """
    from app.graphs.tools.calculator import calculator_tool
    from app.graphs.tools.analytics import (
        get_order_analytics_tool,
        get_campaign_analytics_tool,
        get_consumer_analytics_tool,
        get_feedback_analytics_tool,
        get_menu_events_analytics_tool,
    )
    from app.graphs.tools.rag import search_historical_data

    tools = [
        calculator_tool,
        get_order_analytics_tool,
        get_campaign_analytics_tool,
        get_consumer_analytics_tool,
        get_feedback_analytics_tool,
        get_menu_events_analytics_tool,
        search_historical_data,
    ]

    # Create tool node
    tool_node = ToolNode(tools)

    # Wrap the tool node's invoke method to inject store_id
    original_invoke = tool_node.invoke

    def inject_store_id(state: Dict[str, Any]) -> Dict[str, Any]:
        """Inject store_id into tool calls before execution."""
        messages = state.get("messages", [])
        modified_messages = []

        for msg in messages:
            if (
                isinstance(msg, AIMessage)
                and hasattr(msg, "tool_calls")
                and msg.tool_calls
            ):
                # Modify tool calls to include store_id
                modified_tool_calls = []
                for tool_call in msg.tool_calls:
                    tool_name = tool_call.get("name", "")
                    tool_args = tool_call.get("args", {})

                    # Inject store_id for analytics and RAG tools
                    if tool_name in [
                        "get_order_analytics_tool",
                        "get_campaign_analytics_tool",
                        "get_consumer_analytics_tool",
                        "get_feedback_analytics_tool",
                        "get_menu_events_analytics_tool",
                        "search_historical_data",
                    ]:
                        if "store_id" not in tool_args:
                            tool_args["store_id"] = store_id
                            logger.debug(
                                f"Injected store_id={store_id} into {tool_name}"
                            )

                    modified_tool_calls.append(
                        {
                            **tool_call,
                            "args": tool_args,
                        }
                    )

                # Create modified message
                modified_msg = AIMessage(
                    content=msg.content,
                    tool_calls=modified_tool_calls,
                    id=msg.id,
                )
                modified_messages.append(modified_msg)
            else:
                modified_messages.append(msg)

        # Call original invoke with modified state
        modified_state = {**state, "messages": modified_messages}
        return original_invoke(modified_state)

    # Replace invoke method
    tool_node.invoke = inject_store_id

    return tool_node


def create_tools_node_dynamic(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dynamic tool node that extracts store_id from state and injects it.

    This is used as a node function in the graph.
    """
    store_id = state.get("store_id", "")
    messages = state.get("messages", [])

    if not store_id:
        logger.warning("No store_id in state, tools may fail")

    # Get tools
    from app.graphs.tools.calculator import calculator_tool
    from app.graphs.tools.analytics import (
        get_order_analytics_tool,
        get_campaign_analytics_tool,
        get_consumer_analytics_tool,
        get_feedback_analytics_tool,
        get_menu_events_analytics_tool,
    )
    from app.graphs.tools.rag import search_historical_data

    tools = [
        calculator_tool,
        get_order_analytics_tool,
        get_campaign_analytics_tool,
        get_consumer_analytics_tool,
        get_feedback_analytics_tool,
        get_menu_events_analytics_tool,
        search_historical_data,
    ]

    # Find tool calls in messages
    tool_messages = []
    for msg in messages:
        if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
            for tool_call in msg.tool_calls:
                tool_name = tool_call.get("name", "")
                tool_args = tool_call.get(
                    "args", {}
                ).copy()  # Make a copy to avoid modifying original

                # Inject store_id for analytics and RAG tools (always override if present)
                if tool_name in [
                    "get_order_analytics_tool",
                    "get_campaign_analytics_tool",
                    "get_consumer_analytics_tool",
                    "get_feedback_analytics_tool",
                    "get_menu_events_analytics_tool",
                    "search_historical_data",
                ]:
                    tool_args["store_id"] = store_id
                    logger.debug(f"Injected store_id={store_id} into {tool_name}")

                # Find the tool and execute it
                tool = None
                for t in tools:
                    if t.name == tool_name:
                        tool = t
                        break

                if tool:
                    try:
                        result = tool.invoke(tool_args)
                        tool_messages.append(
                            ToolMessage(
                                content=str(result),
                                tool_call_id=tool_call.get("id"),
                            )
                        )
                    except Exception as e:
                        logger.error(
                            f"Error executing tool {tool_name}: {e}", exc_info=True
                        )
                        tool_messages.append(
                            ToolMessage(
                                content=f"Error: {str(e)}",
                                tool_call_id=tool_call.get("id"),
                            )
                        )
                else:
                    logger.warning(f"Tool {tool_name} not found")
                    tool_messages.append(
                        ToolMessage(
                            content=f"Tool {tool_name} not found",
                            tool_call_id=tool_call.get("id"),
                        )
                    )

    return {"messages": tool_messages}


__all__ = ["create_tools_node_dynamic", "create_tools_node_with_store_id"]
