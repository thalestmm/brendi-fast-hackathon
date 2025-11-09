"""
Formatting helpers shared by the agent and insights LangGraph flows.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Iterable

CurrencyValue = float

_EXACT_CURRENCY_KEYS = {
    "total_revenue",
    "average_order_value",
    "price",
    "total_price",
    "revenue",
}
_CURRENCY_SUFFIXES: Iterable[str] = ("_revenue", "_price")


def normalize_currency_for_llm(payload: Any) -> Any:
    """
    Normalize currency values expressed in cents so the LLM receives BRL amounts.

    Args:
        payload: Arbitrary data structure (dict/list/scalar) returned by analytics tools.

    Returns:
        A copy of ``payload`` with currency fields converted to floating point BRL amounts
        and an additional ``<key>_formatted`` entry containing a human-readable string.
    """
    if isinstance(payload, dict):
        normalized: dict[str, Any] = {}
        for key, value in payload.items():
            normalized_value = normalize_currency_for_llm(value)

            if _should_normalize_currency(key, value):
                converted = _convert_cents_to_brl(value)
                if converted is not None:
                    normalized[key] = float(converted)
                    normalized[f"{key}_formatted"] = _format_brl(converted)
                    continue

            normalized[key] = normalized_value

        return normalized

    if isinstance(payload, list):
        return [normalize_currency_for_llm(item) for item in payload]

    return payload


def _should_normalize_currency(key: str, value: Any) -> bool:
    if key in _EXACT_CURRENCY_KEYS:
        return True
    return any(key.endswith(suffix) for suffix in _CURRENCY_SUFFIXES)


def _convert_cents_to_brl(value: Any) -> Decimal | None:
    cents = _coerce_to_decimal(value)
    if cents is None:
        return None
    return (cents / Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _coerce_to_decimal(value: Any) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, str):
        cleaned = (
            value.replace("R$", "")
            .replace(" ", "")
            .replace(".", "")
            .replace(",", "")
            .strip()
        )
        if not cleaned:
            return None
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None
    return None


def _format_brl(amount: Decimal) -> str:
    integer_part, _, fractional_part = f"{amount:.2f}".partition(".")
    integer_with_sep = "{:,}".format(int(integer_part)).replace(",", ".")
    return f"R$ {integer_with_sep},{fractional_part}"
