"""
Input validators for trading orders
"""

import re
from decimal import Decimal, InvalidOperation


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def validate_symbol(symbol):
    """
    Validate trading symbol.
    
    Args:
        symbol (str): Trading symbol (e.g., BTCUSDT)
        
    Raises:
        ValidationError: If symbol is invalid
        
    Returns:
        str: Validated symbol
    """
    if not symbol:
        raise ValidationError("Symbol cannot be empty")
    
    symbol = str(symbol).strip().upper()
    
    if not symbol.endswith("USDT"):
        raise ValidationError("Symbol must end with 'USDT' (e.g., BTCUSDT)")
    
    if not re.match(r"^[A-Z0-9]+$", symbol):
        raise ValidationError("Symbol must contain only uppercase letters and numbers")
    
    return symbol


def validate_side(side):
    """
    Validate order side (BUY or SELL).
    
    Args:
        side (str): Order side
        
    Raises:
        ValidationError: If side is invalid
        
    Returns:
        str: Validated side
    """
    if not side:
        raise ValidationError("Side cannot be empty")
    
    side = str(side).strip().upper()
    
    if side not in ["BUY", "SELL"]:
        raise ValidationError("Side must be either 'BUY' or 'SELL'")
    
    return side


def validate_order_type(order_type):
    """
    Validate order type (MARKET or LIMIT).
    
    Args:
        order_type (str): Order type
        
    Raises:
        ValidationError: If order type is invalid
        
    Returns:
        str: Validated order type
    """
    if not order_type:
        raise ValidationError("Order type cannot be empty")
    
    order_type = str(order_type).strip().upper()
    
    if order_type not in ["MARKET", "LIMIT"]:
        raise ValidationError("Order type must be either 'MARKET' or 'LIMIT'")
    
    return order_type


def _normalize_positive_decimal(value, field_name):
    """Validate and normalize a positive decimal value for Binance params."""
    try:
        decimal_value = Decimal(str(value).strip())
    except (InvalidOperation, AttributeError, ValueError):
        raise ValidationError(f"{field_name} must be a valid number")

    if not decimal_value.is_finite():
        raise ValidationError(f"{field_name} must be a finite number")

    if decimal_value <= 0:
        raise ValidationError(f"{field_name} must be positive (greater than 0)")

    normalized = format(decimal_value.normalize(), "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")

    return normalized


def validate_quantity(quantity):
    """
    Validate order quantity.
    
    Args:
        quantity (float or str): Order quantity
        
    Raises:
        ValidationError: If quantity is invalid
        
    Returns:
        float: Validated quantity
    """
    return _normalize_positive_decimal(quantity, "Quantity")


def validate_price(price, order_type):
    """
    Validate order price (required for LIMIT, not for MARKET).
    
    Args:
        price (float or str or None): Order price
        order_type (str): Order type
        
    Raises:
        ValidationError: If price is invalid
        
    Returns:
        float or None: Validated price or None for MARKET orders
    """
    if order_type == "MARKET":
        return None
    
    if order_type == "LIMIT":
        if price is None:
            raise ValidationError("Price is required for LIMIT orders")
        
        return _normalize_positive_decimal(price, "Price")
    
    return None


def validate_order_input(symbol, side, order_type, quantity, price=None):
    """
    Validate all order input parameters.
    
    Args:
        symbol (str): Trading symbol
        side (str): Order side (BUY or SELL)
        order_type (str): Order type (MARKET or LIMIT)
        quantity (float): Order quantity
        price (float, optional): Order price (required for LIMIT)
        
    Raises:
        ValidationError: If any parameter is invalid
        
    Returns:
        dict: Dictionary with validated parameters
    """
    validated_symbol = validate_symbol(symbol)
    validated_side = validate_side(side)
    validated_type = validate_order_type(order_type)
    validated_quantity = validate_quantity(quantity)
    validated_price = validate_price(price, validated_type)
    
    return {
        "symbol": validated_symbol,
        "side": validated_side,
        "type": validated_type,
        "quantity": validated_quantity,
        "price": validated_price
    }
