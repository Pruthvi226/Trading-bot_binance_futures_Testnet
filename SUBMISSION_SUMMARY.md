# Submission Summary

End-to-end Binance Futures Testnet verification has been completed with the
provided testnet API credentials.

## Local Verification

Command:

```powershell
python -B -m unittest discover -s tests
```

Result:

```text
Ran 10 tests

OK
```

## Live Testnet Orders

### MARKET Order

Command:

```powershell
$env:TRADING_BOT_LOG_FILE = "logs/examples/market_order.log"
python -B cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
Remove-Item Env:TRADING_BOT_LOG_FILE
```

Result:

```text
Order ID: 13810031316
Status: FILLED
Executed Qty: 0.001
Average Price: 69524.7 USDT
```

Evidence log:

```text
logs/examples/market_order.log
```

### LIMIT Order

Command:

```powershell
$env:TRADING_BOT_LOG_FILE = "logs/examples/limit_order.log"
python -B cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 70500
Remove-Item Env:TRADING_BOT_LOG_FILE
```

Result:

```text
Order ID: 13810059602
Status: NEW
Executed Qty: 0
Limit Price: 70500 USDT
```

Evidence log:

```text
logs/examples/limit_order.log
```

## Security Check

The evidence logs were checked for the provided API key and secret.

Result:

```text
key_leaked=False
secret_leaked=False
```

The `.env` file contains credentials for local execution only and must not be
submitted. `.env.example` has been restored to placeholder values.
