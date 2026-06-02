"""
Command-line interface for the Binance Futures Testnet trading bot.
"""

import argparse
import sys
from decimal import Decimal, InvalidOperation
from textwrap import wrap
from typing import Any

from rich import box
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

from bot.client import BinanceClientError
from bot.logging_config import setup_logging
from bot.orders import OrderManager
from bot.validators import ValidationError, validate_order_input


logger = setup_logging()
console = Console(highlight=False, soft_wrap=True)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Place MARKET and LIMIT orders on Binance Futures Testnet USDT-M.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Market buy:
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

  Limit sell:
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 95000
        """,
    )

    parser.add_argument(
        "--symbol",
        required=True,
        help="Trading symbol, for example BTCUSDT or ETHUSDT.",
    )
    parser.add_argument(
        "--side",
        required=True,
        type=str.upper,
        choices=["BUY", "SELL"],
        help="Order side: BUY or SELL.",
    )
    parser.add_argument(
        "--type",
        required=True,
        type=str.upper,
        choices=["MARKET", "LIMIT"],
        dest="order_type",
        help="Order type: MARKET or LIMIT.",
    )
    parser.add_argument(
        "--quantity",
        required=True,
        help="Order quantity. Use decimal notation, for example 0.001.",
    )
    parser.add_argument(
        "--price",
        help="Limit price. Required for LIMIT orders and ignored for MARKET orders.",
    )

    return parser


def format_decimal(value: Any, suffix: str = "") -> str:
    """Format Binance decimal strings without losing precision."""
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


def add_row(table: Table, label: str, value: Any, style: str = "white") -> None:
    """Add one labeled row to a Rich table."""
    table.add_row(Text(label, style="bold white"), Text(str(value), style=style))


def wrapped_text(message: str, style: str, width: int = 72) -> Text:
    """Create Rich text that wraps predictably in Windows terminals."""
    text = Text()
    lines = wrap(str(message), width=width) or [str(message)]
    for index, line in enumerate(lines):
        text.append(line, style=style)
        if index < len(lines) - 1:
            text.append("\n")
    return text


def display_order_summary(order: dict[str, Any]) -> None:
    """Display the validated order request before execution."""
    side_style = "bold green" if order["side"] == "BUY" else "bold red"
    type_style = "yellow" if order["type"] == "MARKET" else "cyan"

    table = Table(
        title="[bold cyan]ORDER REQUEST[/bold cyan]",
        show_header=False,
        box=box.ASCII,
        border_style="cyan",
        expand=True,
    )

    add_row(table, "Symbol", order["symbol"], "cyan")
    add_row(table, "Side", order["side"], side_style)
    add_row(table, "Type", order["type"], type_style)
    add_row(table, "Quantity", format_decimal(order["quantity"]), "magenta")
    if order["type"] == "LIMIT":
        add_row(table, "Price", format_decimal(order["price"], " USDT"), "cyan")

    console.print(table)


def display_order_response(response: dict[str, Any]) -> None:
    """Display the key Binance order response fields."""
    status = response.get("status") or "N/A"
    side = response.get("side") or "N/A"
    order_type = response.get("type") or "N/A"

    status_style = "bold green" if status in {"FILLED", "PARTIALLY_FILLED", "NEW"} else "bold yellow"
    side_style = "bold green" if side == "BUY" else "bold red"
    type_style = "yellow" if order_type == "MARKET" else "cyan"

    table = Table(
        title="[bold green]ORDER RESPONSE[/bold green]",
        show_header=False,
        box=box.ASCII,
        border_style="green",
        expand=True,
    )

    add_row(table, "Order ID", response.get("orderId", "N/A"), "cyan")
    add_row(table, "Status", status, status_style)
    add_row(table, "Symbol", response.get("symbol", "N/A"), "cyan")
    add_row(table, "Side", side, side_style)
    add_row(table, "Type", order_type, type_style)
    add_row(table, "Quantity", format_decimal(response.get("quantity")), "magenta")

    price = response.get("price")
    if price not in (None, "", "0", "0.0", "0.00", "0.00000000"):
        add_row(table, "Price", format_decimal(price, " USDT"), "cyan")

    add_row(table, "Executed Qty", format_decimal(response.get("executedQty")), "bright_magenta")

    avg_price = response.get("avgPrice")
    if avg_price not in (None, "", "N/A"):
        add_row(table, "Average Price", format_decimal(avg_price, " USDT"), "bright_cyan")

    console.print(table)


def display_success(response: dict[str, Any]) -> None:
    """Display a concise success panel."""
    success_text = Text()
    success_text.append("Order placed successfully.\n", style="bold green")
    success_text.append("Order ID: ", style="bold white")
    success_text.append(f"{response.get('orderId', 'N/A')}\n", style="bold cyan")
    success_text.append("Status: ", style="bold white")
    success_text.append(str(response.get("status", "N/A")), style="bold green")

    console.print(
        Panel(
            success_text,
            title="[bold green]SUCCESS[/bold green]",
            title_align="left",
            border_style="green",
            box=box.ASCII,
        )
    )


def display_validation_error(error: ValidationError) -> None:
    """Display input validation feedback."""
    console.print()
    console.print(
        Panel(
            wrapped_text(f"Input validation failed: {error}", "bold red"),
            title="[bold red]VALIDATION ERROR[/bold red]",
            title_align="left",
            border_style="red",
            box=box.ASCII,
        )
    )
    console.print(Text("Fix checklist:", style="bold yellow"))
    console.print("  - Symbol must be uppercase and end with USDT, for example BTCUSDT.")
    console.print("  - Side must be BUY or SELL.")
    console.print("  - Type must be MARKET or LIMIT.")
    console.print("  - Quantity must be a positive decimal number.")
    console.print("  - Price is required for LIMIT orders and must be positive.")
    console.print()


def display_api_error(error: BinanceClientError) -> None:
    """Display Binance API or network error feedback."""
    console.print()
    console.print(
        Panel(
            wrapped_text(f"Order failed: {error}", "bold red"),
            title="[bold red]API ERROR[/bold red]",
            title_align="left",
            border_style="red",
            box=box.ASCII,
        )
    )
    console.print(Text("Troubleshooting:", style="bold yellow"))
    console.print("  - Confirm .env contains Binance Futures Testnet credentials.")
    console.print("  - Use testnet keys, not production Binance keys.")
    console.print("  - Check the symbol, balance, and order precision on the testnet account.")
    console.print("  - Review logs/trading_bot.log for the API status and response body.")
    console.print()


def main() -> int:
    """Run the CLI."""
    parser = create_argument_parser()
    args = parser.parse_args()

    try:
        validated_order = validate_order_input(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
        )

        console.print()
        console.rule("[bold cyan]Binance Futures Testnet Order[/bold cyan]")
        console.print()
        display_order_summary(validated_order)
        console.print()

        order_manager = OrderManager()
        with Live(
            Spinner("line", text="[cyan]Submitting order to testnet...[/cyan]"),
            console=console,
            transient=True,
            refresh_per_second=10,
        ):
            raw_response = order_manager.execute_order(
                symbol=validated_order["symbol"],
                side=validated_order["side"],
                order_type=validated_order["type"],
                quantity=validated_order["quantity"],
                price=validated_order["price"],
            )

        formatted_response = order_manager.format_order_response(raw_response)
        display_order_response(formatted_response)
        console.print()
        display_success(formatted_response)
        console.print()

        logger.info("Order execution completed successfully")
        return 0

    except ValidationError as error:
        logger.error("Validation error: %s", error)
        display_validation_error(error)
        return 1

    except BinanceClientError as error:
        logger.error("Binance API/client error: %s", error)
        display_api_error(error)
        return 1

    except KeyboardInterrupt:
        logger.warning("Operation cancelled by user")
        console.print()
        console.print("[yellow]Operation cancelled by user.[/yellow]")
        console.print()
        return 1

    except Exception as error:
        logger.exception("Unexpected error: %s", error)
        console.print()
        console.print(
            Panel(
                wrapped_text(f"Unexpected error: {error}", "bold red"),
                title="[bold red]ERROR[/bold red]",
                title_align="left",
                border_style="red",
                box=box.ASCII,
            )
        )
        console.print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
