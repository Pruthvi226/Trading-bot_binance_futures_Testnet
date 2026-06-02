# Binance Futures Testnet Trading Bot

A compact Python trading bot for Binance Futures Testnet USDT-M. It places
MARKET and LIMIT orders through direct REST API calls, validates user input,
prints clear execution output, and writes useful logs for review.

This repository was built for the Python Developer trading bot assessment.

## Assessment Status

| Criterion | Status | Evidence |
| --- | --- | --- |
| Places orders on testnet | Complete | `logs/examples/market_order.log`, `logs/examples/limit_order.log` |
| MARKET and LIMIT orders | Complete | CLI supports both via `--type MARKET` and `--type LIMIT` |
| BUY and SELL sides | Complete | CLI supports both via `--side BUY` and `--side SELL` |
| CLI input validation | Complete | `argparse` plus custom validators in `bot/validators.py` |
| Structured code | Complete | API client, order manager, validators, logger, CLI, and UI are separated |
| Error handling | Complete | Validation, API, network, JSON, credential, and timestamp errors |
| Logging | Complete | Sanitized request, response, status code, and error logs |
| README and runnable instructions | Complete | Setup, usage, tests, UI, logs, and troubleshooting included |
| Bonus | Complete | Rich CLI output and lightweight local web UI |

## Live Testnet Verification

The included evidence logs were generated against Binance Futures Testnet with
real testnet credentials.

| Type | Symbol | Side | Quantity | Price | Status | Order ID | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MARKET | BTCUSDT | BUY | 0.001 | Market | FILLED | `13810031316` | `logs/examples/market_order.log` |
| LIMIT | BTCUSDT | SELL | 0.001 | 70500 | NEW | `13810059602` | `logs/examples/limit_order.log` |

The evidence logs were checked to confirm that the API key and secret were not
written to disk.

## Features

- Direct REST integration with Binance Futures Testnet
- HMAC SHA256 signed requests
- Testnet-only base URL guard
- Binance server-time sync before signed orders
- One-time retry for timestamp drift errors
- `newOrderRespType=RESULT` for clearer execution responses
- MARKET and LIMIT order placement
- BUY and SELL support
- Decimal-safe quantity and price validation
- Rich terminal output with request and response tables
- Rotating file logger
- Optional lightweight local web UI
- Unit tests for validation, response formatting, and UI behavior

## Project Structure

```text
.
|-- bot/
|   |-- __init__.py
|   |-- client.py              # Binance Futures REST client and signing
|   |-- logging_config.py      # Rotating file logger
|   |-- orders.py              # Order workflow and response formatting
|   `-- validators.py          # Input validation and decimal normalization
|-- logs/
|   |-- .gitkeep
|   `-- examples/
|       |-- market_order.log   # Live MARKET order evidence
|       |-- limit_order.log    # Live LIMIT order evidence
|       `-- README.md
|-- tests/
|   |-- __init__.py
|   |-- test_orders.py
|   |-- test_ui.py
|   `-- test_validators.py
|-- .env.example
|-- .gitignore
|-- ACCEPTANCE_CHECKLIST.md
|-- DELIVERABLES.md
|-- SUBMISSION_SUMMARY.md
|-- cli.py                    # Required CLI entry point
|-- ui.py                     # Optional local web UI
|-- requirements.txt
`-- README.md
```

## Requirements

- Python 3.8 or newer
- Binance Futures Testnet account
- Binance Futures Testnet API key and secret

Install dependencies:

```powershell
pip install -r requirements.txt
```

Dependencies:

```text
requests
python-dotenv
rich
```

## Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create `.env` from the example file:

```powershell
Copy-Item .env.example .env
```

Edit `.env`:

```env
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret
BINANCE_BASE_URL=https://testnet.binancefuture.com
```

Only Futures Testnet credentials should be used. The application refuses any
base URL other than:

```text
https://testnet.binancefuture.com
```

## CLI Usage

Show help:

```powershell
python -B cli.py --help
```

Place a MARKET BUY order:

```powershell
python -B cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

Place a MARKET SELL order:

```powershell
python -B cli.py --symbol BTCUSDT --side SELL --type MARKET --quantity 0.001
```

Place a LIMIT BUY order:

```powershell
python -B cli.py --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.001 --price 60000
```

Place a LIMIT SELL order:

```powershell
python -B cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 70500
```

## CLI Output

The CLI prints a request summary before submitting the order:

```text
------------------------ Binance Futures Testnet Order ------------------------

ORDER REQUEST
+-----------------------------------------------------------------------------+
| Symbol                                 | BTCUSDT                            |
| Side                                   | BUY                                |
| Type                                   | MARKET                             |
| Quantity                               | 0.001                              |
+-----------------------------------------------------------------------------+
```

Successful responses show the key fields required for review:

```text
ORDER RESPONSE
+-----------------------------------------------------------------------------+
| Order ID                               | 13810031316                        |
| Status                                 | FILLED                             |
| Symbol                                 | BTCUSDT                            |
| Side                                   | BUY                                |
| Type                                   | MARKET                             |
| Quantity                               | 0.001                              |
| Executed Qty                           | 0.001                              |
| Average Price                          | 69524.7 USDT                       |
+-----------------------------------------------------------------------------+
```

## Lightweight Web UI

The optional UI reuses the same validators and order manager as the CLI.

Run it locally:

```powershell
python -B ui.py --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

UI capabilities:

- MARKET and LIMIT order ticket
- BUY and SELL segmented controls
- Preview mode for validation without placing an order
- Submit mode for live Futures Testnet order placement
- Request summary
- Normalized response summary
- Raw JSON response viewer
- Recent log viewer

The UI uses Python's standard library HTTP server, so there is no web framework
dependency.

## Logging

Default runtime log:

```text
logs/trading_bot.log
```

Assessment evidence logs:

```text
logs/examples/market_order.log
logs/examples/limit_order.log
```

Capture a specific command to a specific evidence file:

```powershell
$env:TRADING_BOT_LOG_FILE = "logs/examples/market_order.log"
python -B cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
Remove-Item Env:TRADING_BOT_LOG_FILE
```

Logged:

- order workflow start
- Binance endpoint
- sanitized request parameters
- response status code
- response body
- validation failures
- API failures
- network failures
- timestamp sync warnings

Not logged:

- API secret
- request signature
- `.env` contents

## Validation Rules

| Argument | Rule |
| --- | --- |
| `--symbol` | Required, normalized to uppercase, alphanumeric, must end in `USDT` |
| `--side` | Required, must be `BUY` or `SELL` |
| `--type` | Required, must be `MARKET` or `LIMIT` |
| `--quantity` | Required, positive finite decimal |
| `--price` | Required for LIMIT orders, positive finite decimal |

MARKET orders ignore `--price`. Quantities and prices are normalized as decimal
strings before being sent to Binance to avoid floating point precision issues.

## Error Handling

The application handles and reports:

- invalid input
- missing credentials
- non-testnet base URLs
- Binance API errors
- network failures
- invalid JSON responses
- timestamp drift errors
- unexpected exceptions

## Tests

Run all local tests:

```powershell
python -B -m unittest discover -s tests
```

Verified result:

```text
Ran 10 tests

OK
```

## Implementation Notes

- `bot/client.py` owns REST calls, signing, server-time sync, and Binance errors.
- `bot/orders.py` owns order execution flow and response formatting.
- `bot/validators.py` owns user input validation and decimal normalization.
- `bot/logging_config.py` owns rotating file logging.
- `cli.py` owns the assessment-required command-line interface.
- `ui.py` owns the optional local web interface.
- LIMIT orders use `timeInForce=GTC`.
- Orders request `newOrderRespType=RESULT`.
- Average price is displayed from Binance `avgPrice` when available; otherwise
  it can be derived from `cumQuote / executedQty`.

## Security

- `.env` is excluded by `.gitignore`.
- `.env.example` contains placeholders only.
- API secret and signatures are not logged.
- The client is hard-guarded to Futures Testnet.
- Evidence logs were checked for key leakage.

## Troubleshooting

### `BINANCE_API_KEY not found`

Create `.env` from `.env.example` and add Binance Futures Testnet credentials.

### `Invalid API-key`

Confirm that you are using Futures Testnet keys, not production Binance keys.
Also confirm that the key has Futures trading permission.

### `Price is required for LIMIT orders`

Add a positive `--price`:

```powershell
python -B cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 70500
```

### Binance rejects quantity or precision

Check the current symbol filters on Binance Futures Testnet and adjust
`--quantity` or `--price`.

### Timestamp error

The client syncs with Binance server time and retries timestamp failures once.
If the error persists, check the machine clock and internet connection.

## Submission Notes

The repository contains:

- source code
- requirements file
- setup and usage instructions
- local tests
- live MARKET and LIMIT evidence logs
- acceptance checklist
- submission summary

Do not commit or submit `.env`.
