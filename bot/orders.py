"""
Order management and execution
"""

from decimal import Decimal, InvalidOperation

from bot.client import BinanceClient, BinanceClientError
from bot.validators import validate_order_input, ValidationError
from bot.logging_config import setup_logging


logger = setup_logging()


class OrderManager:
    """
    Order manager for executing trading orders.
    Handles validation, execution, and response formatting.
    """
    
    def __init__(self, client=None):
        """Initialize order manager with an optional Binance client."""
        self.client = client

    def _get_client(self):
        """Create the Binance client only after order input has been validated."""
        if self.client is None:
            try:
                self.client = BinanceClient()
            except BinanceClientError as e:
                logger.error(f"Failed to initialize Binance client: {str(e)}")
                raise
        return self.client
    
    def execute_order(self, symbol, side, order_type, quantity, price=None):
        """
        Execute a trading order.
        
        Args:
            symbol (str): Trading symbol
            side (str): Order side (BUY or SELL)
            order_type (str): Order type (MARKET or LIMIT)
            quantity (float): Order quantity
            price (float, optional): Order price (required for LIMIT)
            
        Returns:
            dict: Order response with order details
            
        Raises:
            ValidationError: If input validation fails
            BinanceClientError: If API request fails
        """
        try:
            # Validate input
            validated_params = validate_order_input(
                symbol, side, order_type, quantity, price
            )
            
            logger.info(
                f"Executing {validated_params['type']} {validated_params['side']} order: "
                f"{validated_params['symbol']} x{validated_params['quantity']}"
            )
            
            # Execute order
            response = self._get_client().place_order(
                symbol=validated_params["symbol"],
                side=validated_params["side"],
                order_type=validated_params["type"],
                quantity=validated_params["quantity"],
                price=validated_params["price"]
            )
            
            return response
        
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            raise
        except BinanceClientError as e:
            logger.error(f"Binance client error: {str(e)}")
            raise
    
    @staticmethod
    def _calculate_average_price(response):
        """
        Calculate an average price when Binance omits avgPrice but returns fills.
        """
        avg_price = response.get("avgPrice")
        if avg_price not in (None, "", "0", "0.0", "0.00", "0.00000000"):
            return avg_price

        executed_qty = response.get("executedQty")
        cumulative_quote = response.get("cumQuote")
        if not executed_qty or not cumulative_quote:
            return avg_price

        try:
            executed = Decimal(str(executed_qty))
            quote = Decimal(str(cumulative_quote))
        except (InvalidOperation, ValueError):
            return avg_price

        if executed <= 0:
            return avg_price

        average = format((quote / executed).normalize(), "f")
        if "." in average:
            average = average.rstrip("0").rstrip(".")

        return average

    @classmethod
    def format_order_response(cls, response):
        """
        Format API response for display.
        
        Args:
            response (dict): API response data
            
        Returns:
            dict: Formatted response with key fields
        """
        return {
            "orderId": response.get("orderId"),
            "symbol": response.get("symbol"),
            "side": response.get("side"),
            "type": response.get("type"),
            "quantity": response.get("origQty") or response.get("quantity"),
            "price": response.get("price"),
            "status": response.get("status"),
            "executedQty": response.get("executedQty"),
            "avgPrice": cls._calculate_average_price(response),
            "timeInForce": response.get("timeInForce"),
            "updateTime": response.get("updateTime")
        }
