"""
Lightweight local web UI for the Binance Futures Testnet trading bot.
"""

import argparse
import json
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from html import escape
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from bot.client import BinanceClientError, TESTNET_BASE_URL
from bot.logging_config import setup_logging
from bot.orders import OrderManager
from bot.validators import ValidationError, validate_order_input


logger = setup_logging()
LOG_PATH = Path("logs/trading_bot.log")

DEFAULT_FORM = {
    "symbol": "BTCUSDT",
    "side": "BUY",
    "order_type": "MARKET",
    "quantity": "0.001",
    "price": "",
}


@dataclass
class ViewState:
    form: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_FORM))
    notice_type: str | None = None
    notice_title: str = ""
    notice_message: str = ""
    request_summary: dict[str, Any] | None = None
    response_summary: dict[str, Any] | None = None
    raw_response: dict[str, Any] | None = None


def parse_args() -> argparse.Namespace:
    """Parse local UI server options."""
    parser = argparse.ArgumentParser(description="Run the local trading bot web UI.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind. Defaults to 127.0.0.1.")
    parser.add_argument("--port", default=8000, type=int, help="Port to bind. Defaults to 8000.")
    return parser.parse_args()


def html(value: Any) -> str:
    """Escape a value for safe HTML output."""
    return escape("" if value is None else str(value), quote=True)


def format_decimal(value: Any, suffix: str = "") -> str:
    """Format decimal strings in plain notation."""
    if value in (None, "", "N/A"):
        return "N/A"

    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return str(value)

    if not decimal_value.is_finite():
        return str(value)

    text = format(decimal_value.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text in ("", "-0"):
        text = "0"

    return f"{text}{suffix}"


def get_form_value(form: dict[str, list[str]], key: str, default: str = "") -> str:
    """Read the first form value from a parsed POST body."""
    values = form.get(key)
    if not values:
        return default
    return values[0].strip()


def read_recent_logs(max_lines: int = 90) -> list[str]:
    """Read the most recent log lines for the UI log panel."""
    if not LOG_PATH.exists():
        return ["No log file has been created yet."]

    with LOG_PATH.open("r", encoding="utf-8", errors="replace") as log_file:
        lines = log_file.readlines()

    return [line.rstrip() for line in lines[-max_lines:]] or ["Log file is empty."]


def render_notice(state: ViewState) -> str:
    """Render validation, success, or API status feedback."""
    if not state.notice_type:
        return ""

    return f"""
        <section class="notice notice-{html(state.notice_type)}" role="status">
            <div>
                <strong>{html(state.notice_title)}</strong>
                <span>{html(state.notice_message)}</span>
            </div>
        </section>
    """


def render_rows(rows: list[tuple[str, Any]], compact: bool = False) -> str:
    """Render label/value rows."""
    row_class = "kv-row compact" if compact else "kv-row"
    return "\n".join(
        f"""
        <div class="{row_class}">
            <span>{html(label)}</span>
            <strong>{html(value)}</strong>
        </div>
        """
        for label, value in rows
    )


def render_request_summary(order: dict[str, Any] | None) -> str:
    """Render the validated request summary."""
    if not order:
        return """
        <div class="empty-state">
            Validate or submit an order to see the normalized request.
        </div>
        """

    rows = [
        ("Symbol", order["symbol"]),
        ("Side", order["side"]),
        ("Type", order["type"]),
        ("Quantity", format_decimal(order["quantity"])),
    ]
    if order["type"] == "LIMIT":
        rows.append(("Price", format_decimal(order["price"], " USDT")))

    return render_rows(rows)


def render_response_summary(response: dict[str, Any] | None) -> str:
    """Render the normalized Binance response."""
    if not response:
        return """
        <div class="empty-state">
            Submitted order details will appear here.
        </div>
        """

    rows = [
        ("Order ID", response.get("orderId", "N/A")),
        ("Status", response.get("status", "N/A")),
        ("Symbol", response.get("symbol", "N/A")),
        ("Side", response.get("side", "N/A")),
        ("Type", response.get("type", "N/A")),
        ("Quantity", format_decimal(response.get("quantity"))),
        ("Executed Qty", format_decimal(response.get("executedQty"))),
    ]

    price = response.get("price")
    if price not in (None, "", "0", "0.0", "0.00", "0.00000000"):
        rows.append(("Price", format_decimal(price, " USDT")))

    avg_price = response.get("avgPrice")
    if avg_price not in (None, "", "N/A"):
        rows.append(("Average Price", format_decimal(avg_price, " USDT")))

    return render_rows(rows)


def render_raw_response(response: dict[str, Any] | None) -> str:
    """Render the raw API response JSON."""
    if not response:
        return '<pre class="code-panel muted">No raw response yet.</pre>'

    pretty = json.dumps(response, indent=2, sort_keys=True)
    return f'<pre class="code-panel">{html(pretty)}</pre>'


def render_logs() -> str:
    """Render recent file logs."""
    lines = "\n".join(html(line) for line in read_recent_logs())
    return f'<pre class="code-panel log-panel">{lines}</pre>'


def radio_button(name: str, value: str, label: str, selected: str) -> str:
    """Render one segmented radio option."""
    checked = "checked" if selected == value else ""
    return f"""
    <label class="segment-option">
        <input type="radio" name="{html(name)}" value="{html(value)}" {checked}>
        <span>{html(label)}</span>
    </label>
    """


def render_page(state: ViewState) -> str:
    """Render the complete UI page."""
    form = state.form
    return f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Trading Bot UI</title>
    <style>
        :root {{
            color-scheme: light;
            --bg: #f4f6f8;
            --surface: #ffffff;
            --surface-soft: #f8fafb;
            --ink: #172026;
            --muted: #64717c;
            --line: #d9e0e6;
            --accent: #006d77;
            --accent-strong: #00515a;
            --buy: #0f8a5f;
            --sell: #b42318;
            --warn: #b7791f;
            --danger-bg: #fff1f0;
            --danger-border: #ffccc7;
            --success-bg: #ecfdf3;
            --success-border: #abefc6;
            --info-bg: #eef8f9;
            --info-border: #a7d8de;
            --shadow: 0 14px 34px rgba(21, 30, 38, 0.08);
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            min-height: 100vh;
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: var(--bg);
            color: var(--ink);
        }}

        button,
        input {{
            font: inherit;
        }}

        .app-shell {{
            width: min(1180px, calc(100% - 32px));
            margin: 0 auto;
            padding: 24px 0 40px;
        }}

        .topbar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            padding: 16px 0 20px;
        }}

        .brand {{
            display: grid;
            gap: 4px;
        }}

        h1 {{
            margin: 0;
            font-size: 24px;
            line-height: 1.2;
            letter-spacing: 0;
        }}

        .subtitle {{
            margin: 0;
            color: var(--muted);
            font-size: 14px;
        }}

        .status-strip {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            justify-content: flex-end;
        }}

        .chip {{
            display: inline-flex;
            align-items: center;
            min-height: 32px;
            padding: 6px 10px;
            border: 1px solid var(--line);
            border-radius: 999px;
            background: var(--surface);
            color: var(--muted);
            font-size: 13px;
            white-space: nowrap;
        }}

        .chip strong {{
            color: var(--ink);
            margin-left: 6px;
        }}

        .layout {{
            display: grid;
            grid-template-columns: minmax(320px, 420px) minmax(0, 1fr);
            gap: 18px;
            align-items: start;
        }}

        .panel {{
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 8px;
            box-shadow: var(--shadow);
        }}

        .panel-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            padding: 16px 18px;
            border-bottom: 1px solid var(--line);
        }}

        .panel-title {{
            margin: 0;
            font-size: 15px;
            line-height: 1.2;
            letter-spacing: 0;
        }}

        .panel-body {{
            padding: 18px;
        }}

        .ticket-form {{
            display: grid;
            gap: 16px;
        }}

        .field {{
            display: grid;
            gap: 7px;
        }}

        .field label,
        .field-label {{
            font-size: 13px;
            font-weight: 700;
            color: #2f3a42;
        }}

        input[type="text"] {{
            width: 100%;
            min-height: 42px;
            border: 1px solid var(--line);
            border-radius: 6px;
            padding: 9px 11px;
            background: var(--surface);
            color: var(--ink);
            outline: none;
        }}

        input[type="text"]:focus {{
            border-color: var(--accent);
            box-shadow: 0 0 0 3px rgba(0, 109, 119, 0.12);
        }}

        input[type="text"]:disabled {{
            background: var(--surface-soft);
            color: #9aa5ad;
        }}

        .segment {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 6px;
            padding: 4px;
            border: 1px solid var(--line);
            border-radius: 8px;
            background: var(--surface-soft);
        }}

        .segment-option input {{
            position: absolute;
            opacity: 0;
            pointer-events: none;
        }}

        .segment-option span {{
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 36px;
            border-radius: 6px;
            color: var(--muted);
            font-size: 13px;
            font-weight: 800;
            cursor: pointer;
        }}

        .segment-option input:checked + span {{
            background: var(--surface);
            color: var(--ink);
            border: 1px solid var(--line);
            box-shadow: 0 3px 10px rgba(21, 30, 38, 0.07);
        }}

        .actions {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            padding-top: 2px;
        }}

        .button {{
            min-height: 42px;
            border: 1px solid transparent;
            border-radius: 6px;
            padding: 9px 12px;
            font-weight: 800;
            cursor: pointer;
        }}

        .button-primary {{
            background: var(--accent);
            color: #ffffff;
        }}

        .button-primary:hover {{
            background: var(--accent-strong);
        }}

        .button-secondary {{
            background: var(--surface);
            color: var(--ink);
            border-color: var(--line);
        }}

        .button-secondary:hover {{
            border-color: var(--accent);
        }}

        .stack {{
            display: grid;
            gap: 18px;
        }}

        .notice {{
            border-radius: 8px;
            border: 1px solid var(--info-border);
            background: var(--info-bg);
            padding: 12px 14px;
        }}

        .notice div {{
            display: grid;
            gap: 3px;
        }}

        .notice strong {{
            font-size: 13px;
        }}

        .notice span {{
            color: var(--muted);
            font-size: 14px;
            line-height: 1.45;
        }}

        .notice-success {{
            background: var(--success-bg);
            border-color: var(--success-border);
        }}

        .notice-error {{
            background: var(--danger-bg);
            border-color: var(--danger-border);
        }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 18px;
        }}

        .kv-row {{
            display: grid;
            grid-template-columns: minmax(110px, 38%) minmax(0, 1fr);
            gap: 12px;
            min-height: 36px;
            align-items: center;
            border-bottom: 1px solid var(--line);
        }}

        .kv-row:last-child {{
            border-bottom: 0;
        }}

        .kv-row span {{
            color: var(--muted);
            font-size: 13px;
        }}

        .kv-row strong {{
            min-width: 0;
            overflow-wrap: anywhere;
            font-size: 14px;
        }}

        .empty-state {{
            min-height: 140px;
            display: grid;
            place-items: center;
            border: 1px dashed var(--line);
            border-radius: 8px;
            color: var(--muted);
            text-align: center;
            padding: 18px;
            line-height: 1.45;
        }}

        .code-panel {{
            min-height: 160px;
            max-height: 340px;
            overflow: auto;
            margin: 0;
            padding: 14px;
            border: 1px solid var(--line);
            border-radius: 8px;
            background: #101418;
            color: #dce7ee;
            font: 12px/1.55 ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
            white-space: pre-wrap;
        }}

        .code-panel.muted {{
            color: #94a3ad;
        }}

        .log-panel {{
            max-height: 260px;
        }}

        @media (max-width: 900px) {{
            .layout,
            .summary-grid {{
                grid-template-columns: 1fr;
            }}

            .topbar {{
                align-items: flex-start;
                flex-direction: column;
            }}

            .status-strip {{
                justify-content: flex-start;
            }}
        }}

        @media (max-width: 520px) {{
            .app-shell {{
                width: min(100% - 20px, 1180px);
                padding-top: 12px;
            }}

            .actions {{
                grid-template-columns: 1fr;
            }}

            .panel-header,
            .panel-body {{
                padding-left: 14px;
                padding-right: 14px;
            }}
        }}
    </style>
</head>
<body>
    <main class="app-shell">
        <header class="topbar">
            <div class="brand">
                <h1>Binance Futures Testnet Bot</h1>
                <p class="subtitle">Local order ticket for USDT-M MARKET and LIMIT orders.</p>
            </div>
            <div class="status-strip" aria-label="Runtime status">
                <span class="chip">Environment <strong>Testnet</strong></span>
                <span class="chip">Endpoint <strong>{html(TESTNET_BASE_URL)}</strong></span>
            </div>
        </header>

        <div class="layout">
            <section class="panel">
                <div class="panel-header">
                    <h2 class="panel-title">Order Ticket</h2>
                    <span class="chip">USDT-M</span>
                </div>
                <div class="panel-body">
                    <form class="ticket-form" method="post" action="/order">
                        <div class="field">
                            <label for="symbol">Symbol</label>
                            <input id="symbol" name="symbol" type="text" autocomplete="off" value="{html(form.get("symbol", ""))}" required>
                        </div>

                        <div class="field">
                            <span class="field-label">Side</span>
                            <div class="segment">
                                {radio_button("side", "BUY", "BUY", form.get("side", "BUY"))}
                                {radio_button("side", "SELL", "SELL", form.get("side", "BUY"))}
                            </div>
                        </div>

                        <div class="field">
                            <span class="field-label">Order Type</span>
                            <div class="segment">
                                {radio_button("order_type", "MARKET", "MARKET", form.get("order_type", "MARKET"))}
                                {radio_button("order_type", "LIMIT", "LIMIT", form.get("order_type", "MARKET"))}
                            </div>
                        </div>

                        <div class="field">
                            <label for="quantity">Quantity</label>
                            <input id="quantity" name="quantity" type="text" inputmode="decimal" autocomplete="off" value="{html(form.get("quantity", ""))}" required>
                        </div>

                        <div class="field" id="priceField">
                            <label for="price">Limit Price</label>
                            <input id="price" name="price" type="text" inputmode="decimal" autocomplete="off" value="{html(form.get("price", ""))}">
                        </div>

                        <div class="actions">
                            <button class="button button-secondary" type="submit" name="action" value="preview">Preview</button>
                            <button class="button button-primary" type="submit" name="action" value="submit">Submit Order</button>
                        </div>
                    </form>
                </div>
            </section>

            <section class="stack">
                {render_notice(state)}

                <section class="panel">
                    <div class="panel-header">
                        <h2 class="panel-title">Execution Snapshot</h2>
                    </div>
                    <div class="panel-body summary-grid">
                        <div>
                            <h3 class="panel-title">Request</h3>
                            {render_request_summary(state.request_summary)}
                        </div>
                        <div>
                            <h3 class="panel-title">Response</h3>
                            {render_response_summary(state.response_summary)}
                        </div>
                    </div>
                </section>

                <section class="panel">
                    <div class="panel-header">
                        <h2 class="panel-title">Raw Response</h2>
                    </div>
                    <div class="panel-body">
                        {render_raw_response(state.raw_response)}
                    </div>
                </section>

                <section class="panel">
                    <div class="panel-header">
                        <h2 class="panel-title">Recent Logs</h2>
                    </div>
                    <div class="panel-body">
                        {render_logs()}
                    </div>
                </section>
            </section>
        </div>
    </main>

    <script>
        const priceInput = document.querySelector("#price");
        const priceField = document.querySelector("#priceField");
        const typeInputs = document.querySelectorAll('input[name="order_type"]');

        function syncPriceInput() {{
            const selected = document.querySelector('input[name="order_type"]:checked').value;
            const isLimit = selected === "LIMIT";
            priceInput.disabled = !isLimit;
            priceInput.required = isLimit;
            priceField.style.opacity = isLimit ? "1" : "0.55";
        }}

        typeInputs.forEach((input) => input.addEventListener("change", syncPriceInput));
        syncPriceInput();
    </script>
</body>
</html>
"""


def build_state_from_post(body: bytes) -> ViewState:
    """Handle order preview or submission from a POST body."""
    parsed = parse_qs(body.decode("utf-8"), keep_blank_values=True)
    form = {
        "symbol": get_form_value(parsed, "symbol", DEFAULT_FORM["symbol"]),
        "side": get_form_value(parsed, "side", DEFAULT_FORM["side"]).upper(),
        "order_type": get_form_value(parsed, "order_type", DEFAULT_FORM["order_type"]).upper(),
        "quantity": get_form_value(parsed, "quantity", DEFAULT_FORM["quantity"]),
        "price": get_form_value(parsed, "price", DEFAULT_FORM["price"]),
    }
    action = get_form_value(parsed, "action", "preview")
    state = ViewState(form=form)

    try:
        order = validate_order_input(
            symbol=form["symbol"],
            side=form["side"],
            order_type=form["order_type"],
            quantity=form["quantity"],
            price=form["price"] or None,
        )
        state.request_summary = order
        state.form.update(
            {
                "symbol": order["symbol"],
                "side": order["side"],
                "order_type": order["type"],
                "quantity": order["quantity"],
                "price": order["price"] or form["price"],
            }
        )

        if action == "preview":
            state.notice_type = "success"
            state.notice_title = "Order validated"
            state.notice_message = "The normalized request is ready to submit to Binance Futures Testnet."
            return state

        raw_response = OrderManager().execute_order(
            symbol=order["symbol"],
            side=order["side"],
            order_type=order["type"],
            quantity=order["quantity"],
            price=order["price"],
        )
        state.raw_response = raw_response
        state.response_summary = OrderManager.format_order_response(raw_response)
        state.notice_type = "success"
        state.notice_title = "Order submitted"
        state.notice_message = f"Binance returned status {state.response_summary.get('status', 'N/A')}."

    except ValidationError as error:
        logger.error("UI validation error: %s", error)
        state.notice_type = "error"
        state.notice_title = "Validation error"
        state.notice_message = str(error)

    except BinanceClientError as error:
        logger.error("UI API/client error: %s", error)
        state.notice_type = "error"
        state.notice_title = "API error"
        state.notice_message = str(error)

    except Exception as error:
        logger.exception("UI unexpected error: %s", error)
        state.notice_type = "error"
        state.notice_title = "Unexpected error"
        state.notice_message = str(error)

    return state


class TradingBotUiHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the local UI."""

    server_version = "TradingBotUI/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.respond_html(render_page(ViewState()))
            return

        if parsed.path == "/health":
            payload = json.dumps({"status": "ok", "service": "trading-bot-ui"}).encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if parsed.path == "/favicon.ico":
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/order":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length > 20_000:
            self.send_error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
            return

        body = self.rfile.read(content_length)
        state = build_state_from_post(body)
        self.respond_html(render_page(state))

    def respond_html(self, content: str) -> None:
        payload = content.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, message_format: str, *args: Any) -> None:
        logger.info("UI request: " + message_format, *args)


def main() -> None:
    """Start the local UI server."""
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), TradingBotUiHandler)
    url = f"http://{args.host}:{args.port}"
    logger.info("Starting local trading bot UI at %s", url)
    print(f"Trading bot UI running at {url}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping trading bot UI.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()