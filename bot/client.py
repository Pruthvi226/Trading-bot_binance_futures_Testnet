"""
Binance Futures API Client
Handles authenticated requests to Binance Futures Testnet
"""

import os
import time
import hmac
import hashlib
from urllib.parse import urlencode
import requests
from dotenv import load_dotenv
from bot.logging_config import setup_logging


logger = setup_logging()
TESTNET_BASE_URL = "https://testnet.binancefuture.com"


class BinanceClientError(Exception):
    """Custom exception for Binance API errors"""
    pass


class BinanceClient:
    """
    Binance Futures Testnet API Client for placing orders.
    
    Handles authentication, request signing, and error handling.
    """
    
    def __init__(self):
        """Initialize the Binance client with API credentials from .env"""
        load_dotenv()
        
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.api_secret = os.getenv("BINANCE_API_SECRET")
        self.base_url = os.getenv("BINANCE_BASE_URL", TESTNET_BASE_URL).rstrip("/")
        self.recv_window = int(os.getenv("BINANCE_RECV_WINDOW", "5000"))
        self.session = requests.Session()
        self._time_offset_ms = 0
        
        # Validate that API credentials are set
        if not self.api_key:
            raise BinanceClientError(
                "BINANCE_API_KEY not found in environment variables. "
                "Please create a .env file with your API credentials."
            )
        if not self.api_secret:
            raise BinanceClientError(
                "BINANCE_API_SECRET not found in environment variables. "
                "Please create a .env file with your API credentials."
            )

        if self.base_url != TESTNET_BASE_URL:
            raise BinanceClientError(
                f"This assessment bot only supports Binance Futures Testnet: {TESTNET_BASE_URL}"
            )
        
        logger.info("Binance client initialized for Futures Testnet")

    def _sync_server_time(self):
        """
        Sync local timestamps with Binance server time.

        Binance rejects signed requests when the client timestamp is too far
        from server time. This keeps order placement more reliable on machines
        with slight clock drift.
        """
        try:
            start = self._get_local_timestamp()
            response = self.session.get(f"{self.base_url}/fapi/v1/time", timeout=5)
            end = self._get_local_timestamp()
            response.raise_for_status()
            server_time = int(response.json()["serverTime"])
            local_midpoint = int((start + end) / 2)
            self._time_offset_ms = server_time - local_midpoint
            logger.debug("Synced Binance server time offset: %sms", self._time_offset_ms)
        except (requests.exceptions.RequestException, KeyError, TypeError, ValueError) as e:
            self._time_offset_ms = 0
            logger.warning("Could not sync Binance server time; using local clock: %s", e)
    
    @staticmethod
    def _get_local_timestamp():
        """Get current local timestamp in milliseconds."""
        return int(time.time() * 1000)

    def _get_timestamp(self):
        """
        Get current timestamp in milliseconds.
        
        Returns:
            int: Timestamp in milliseconds
        """
        return self._get_local_timestamp() + self._time_offset_ms
    
    def _sign_request(self, query_string):
        """
        Sign a request using HMAC SHA256.
        
        Args:
            query_string (str): Query string to sign
            
        Returns:
            str: Signature
        """
        signature = hmac.new(
            self.api_secret.encode(),
            query_string.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _prepare_request(self, params):
        """
        Prepare and sign a request.
        
        Args:
            params (dict): Request parameters
            
        Returns:
            tuple: (query_string, headers)
        """
        # Add timestamp and receive window
        params["timestamp"] = self._get_timestamp()
        params["recvWindow"] = self.recv_window
        
        # Create query string
        query_string = urlencode(params)
        
        # Sign the request
        signature = self._sign_request(query_string)
        
        # Add signature to query string
        query_string += f"&signature={signature}"
        
        # Create headers with API key
        headers = {
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        return query_string, headers
    
    def place_order(self, symbol, side, order_type, quantity, price=None, time_in_force="GTC"):
        """
        Place an order on Binance Futures.
        
        Args:
            symbol (str): Trading symbol (e.g., BTCUSDT)
            side (str): Order side (BUY or SELL)
            order_type (str): Order type (MARKET or LIMIT)
            quantity (float): Order quantity
            price (float, optional): Order price (required for LIMIT)
            time_in_force (str): Time in force (default: GTC for LIMIT, not used for MARKET)
            
        Returns:
            dict: API response
            
        Raises:
            BinanceClientError: If API request fails
        """
        # Prepare request parameters
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
            "newOrderRespType": "RESULT",
        }
        
        # Add price and timeInForce for LIMIT orders
        if order_type == "LIMIT":
            params["price"] = price
            params["timeInForce"] = time_in_force
        
        self._sync_server_time()

        for attempt in range(2):
            signed_params = dict(params)
            query_string, headers = self._prepare_request(signed_params)

            # Log request details without signature or API secret.
            logger.info("POST %s/fapi/v1/order", self.base_url)
            logger.debug("Order request params: %s", signed_params)

            url = f"{self.base_url}/fapi/v1/order?{query_string}"

            try:
                response = self.session.post(url, headers=headers, timeout=10)
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error: {str(e)}")
                raise BinanceClientError(f"Network error: {str(e)}")
            
            # Log response status
            logger.info("API response status code: %s", response.status_code)
            
            # Parse response
            try:
                response_data = response.json()
            except ValueError as e:
                logger.error("Failed to parse response body: %s", response.text)
                raise BinanceClientError(f"Failed to parse response: {str(e)}")
            
            # Check for API errors
            if response.status_code != 200:
                if response_data.get("code") == -1021 and attempt == 0:
                    logger.warning("Timestamp rejected by Binance; syncing server time and retrying once")
                    self._sync_server_time()
                    continue

                error_message = response_data.get("msg", "Unknown error")
                logger.error(
                    "API error response: status=%s message=%s body=%s",
                    response.status_code,
                    error_message,
                    response_data,
                )
                raise BinanceClientError(
                    f"Failed to place order: {error_message} (Status: {response.status_code})"
                )
            
            # Log successful response
            logger.info("Order placed successfully: %s", response_data)
            
            return response_data

        raise BinanceClientError("Failed to place order after retrying timestamp synchronization")
