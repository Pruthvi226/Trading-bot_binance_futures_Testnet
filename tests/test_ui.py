import unittest

from ui import ViewState, build_state_from_post, render_page


class UiStateTest(unittest.TestCase):
    def test_preview_normalizes_valid_limit_order(self):
        state = build_state_from_post(
            b"symbol=btcusdt&side=buy&order_type=limit&quantity=0.00100&price=60000.000&action=preview"
        )

        self.assertEqual(state.notice_type, "success")
        self.assertEqual(state.request_summary["symbol"], "BTCUSDT")
        self.assertEqual(state.request_summary["side"], "BUY")
        self.assertEqual(state.request_summary["type"], "LIMIT")
        self.assertEqual(state.request_summary["quantity"], "0.001")
        self.assertEqual(state.request_summary["price"], "60000")

    def test_preview_reports_validation_error(self):
        state = build_state_from_post(
            b"symbol=BTCUSDT&side=BUY&order_type=LIMIT&quantity=0.001&action=preview"
        )

        self.assertEqual(state.notice_type, "error")
        self.assertEqual(state.notice_title, "Validation error")
        self.assertIn("Price is required", state.notice_message)

    def test_render_page_contains_order_ticket(self):
        page = render_page(ViewState())

        self.assertIn("Binance Futures Testnet Bot", page)
        self.assertIn("Order Ticket", page)
        self.assertIn("Submit Order", page)


if __name__ == "__main__":
    unittest.main()
