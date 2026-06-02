import unittest

from bot.orders import OrderManager


class FormatOrderResponseTest(unittest.TestCase):
    def test_formats_core_binance_fields(self):
        response = OrderManager.format_order_response(
            {
                "orderId": 123456,
                "symbol": "BTCUSDT",
                "side": "BUY",
                "type": "MARKET",
                "origQty": "0.001",
                "price": "0.00",
                "status": "FILLED",
                "executedQty": "0.001",
                "avgPrice": "62500.25",
                "timeInForce": "GTC",
                "updateTime": 1717330000000,
            }
        )

        self.assertEqual(response["orderId"], 123456)
        self.assertEqual(response["quantity"], "0.001")
        self.assertEqual(response["avgPrice"], "62500.25")

    def test_calculates_avg_price_from_cumulative_quote(self):
        response = OrderManager.format_order_response(
            {
                "orderId": 123456,
                "symbol": "BTCUSDT",
                "side": "BUY",
                "type": "MARKET",
                "origQty": "0.002",
                "price": "0.00",
                "status": "FILLED",
                "executedQty": "0.002",
                "avgPrice": "0.00",
                "cumQuote": "130.00",
            }
        )

        self.assertEqual(response["avgPrice"], "65000")


if __name__ == "__main__":
    unittest.main()
