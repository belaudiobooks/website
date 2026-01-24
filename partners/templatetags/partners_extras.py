"""Template filters for partners app."""

from decimal import Decimal
from django import template

register = template.Library()


@register.filter
def format_royalty(value: Decimal) -> str:
    """Format royalty percentage, removing unnecessary decimal places.

    Examples:
        20.00 -> "20%"
        10.50 -> "10.50%"
        15.25 -> "15.25%"
    """
    if value == value.to_integral_value():
        return f"{int(value)}%"
    return f"{value}%"
