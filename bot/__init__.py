"""
Trading Bot Package
Simplified trading bot for Binance Futures Testnet USDT-M
"""

__version__ = "1.0.0"
__author__ = "Internship Candidate"

from bot.client import BinanceClient
from bot.orders import OrderManager
from bot.validators import validate_order_input

__all__ = ["BinanceClient", "OrderManager", "validate_order_input"]
