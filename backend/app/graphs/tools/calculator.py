"""
Calculator tool for the agent.
"""

from langchain_core.tools import tool


@tool
def calculator_tool(expression: str) -> str:
    """
    Evaluate a mathematical expression.

    Args:
        expression: Mathematical expression to evaluate (e.g., "2 + 2", "100 * 0.15")

    Returns:
        Result of the calculation as a string
    """
    try:
        # Safe evaluation of mathematical expressions
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error calculating: {str(e)}"


__all__ = ["calculator_tool"]
