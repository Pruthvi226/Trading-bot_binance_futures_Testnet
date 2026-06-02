import unittest

from bot.validators import ValidationError, validate_order_input


class ValidateOrderInputTest(unittest.TestCase):
    def test_market_order_is_normalized(self):
        order = validate_order_input(
            symbol="btcusdt",
            side="buy",
            order_type="market",
            quantity="0.00100",
        )

        self.assertEqual(
            order,
            {
                "symbol": "BTCUSDT",
                "side": "BUY",
                "type": "MARKET",
                "quantity": "0.001",
                "price": None,
            },
        )

    def test_limit_order_requires_price(self):
        with self.assertRaises(ValidationError):
            validate_order_input(
                symbol="BTCUSDT",
                side="BUY",
                order_type="LIMIT",
                quantity="0.001",
            )

    def test_limit_order_price_is_normalized(self):
        order = validate_order_input(
            symbol="ETHUSDT",
            side="SELL",
            order_type="LIMIT",
            quantity="0.1000",
            price="2500.0000",
        )

        self.assertEqual(order["quantity"], "0.1")
        self.assertEqual(order["price"], "2500")

    def test_rejects_non_usdt_symbol(self):
        with self.assertRaises(ValidationError):
            validate_order_input(
                symbol="BTC",
                side="BUY",
                order_type="MARKET",
                quantity="0.001",
            )

    def test_rejects_non_positive_quantity(self):
        with self.assertRaises(ValidationError):
            validate_order_input(
                symbol="BTCUSDT",
                side="BUY",
                order_type="MARKET",
                quantity="0",
            )


if __name__ == "__main__":
    unittest.main()
