# Acceptance Criteria Checklist

Use this file as a final self-review before submitting the assessment.

## 1. Correctness: Places Orders Successfully On Testnet

Status: ready for live verification.

Implementation:

- Uses Binance Futures Testnet base URL only: `https://testnet.binancefuture.com`.
- Sends signed `POST /fapi/v1/order` requests.
- Requests Binance `RESULT` order responses for clearer execution details.
- Supports MARKET and LIMIT orders.
- Supports BUY and SELL sides.
- LIMIT orders include `timeInForce=GTC`.
- Signed requests include `timestamp` and `recvWindow`.
- Client syncs with Binance server time before placing an order.
- Client retries once if Binance rejects the timestamp.

Required final proof:

- Run one real MARKET order with your testnet API key.
- Run one real LIMIT order with your testnet API key.
- Save logs as:
  - `logs/examples/market_order.log`
  - `logs/examples/limit_order.log`

## 2. Code Quality: Readability, Structure, Reuse

Status: complete.

Project structure:

- `bot/client.py`: Binance REST client, request signing, server-time sync, API errors.
- `bot/orders.py`: order execution workflow and response formatting.
- `bot/validators.py`: input normalization and validation.
- `bot/logging_config.py`: reusable rotating logger.
- `cli.py`: assessment-required command-line interface.
- `ui.py`: optional lightweight local web UI.
- `tests/`: local unit tests for validators, order formatting, and UI behavior.

The CLI and UI both reuse the same validators and order manager.

## 3. Validation And Error Handling

Status: complete.

Validation covers:

- symbol required, normalized to uppercase, alphanumeric, and ending in `USDT`
- side restricted to `BUY` or `SELL`
- type restricted to `MARKET` or `LIMIT`
- quantity required and positive
- price required and positive for LIMIT orders
- MARKET orders ignore price

Error handling covers:

- invalid user input
- missing API credentials
- wrong base URL
- Binance API errors
- network failures
- invalid JSON responses
- timestamp drift retry
- unexpected exceptions

## 4. Logging Quality: Useful, Not Noisy

Status: complete.

Logs are written to `logs/trading_bot.log`.

Useful details logged:

- order workflow start
- endpoint used
- sanitized order params
- Binance response status code
- Binance response body
- validation errors
- API errors
- network errors
- timestamp sync warnings

Sensitive details not logged:

- API secret
- request signature
- `.env` contents

## 5. Clear README And Runnable Instructions

Status: complete.

Docs included:

- `README.md`: setup, CLI examples, UI usage, logging, validation rules, troubleshooting.
- `DELIVERABLES.md`: exact final commands for testnet logs and zip creation.
- `logs/examples/README.md`: where to place real order log evidence.

Local verification command:

```powershell
python -B -m unittest discover -s tests
```

Final live verification commands are documented in `DELIVERABLES.md`.
