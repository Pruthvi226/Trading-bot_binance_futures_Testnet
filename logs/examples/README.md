# Order Log Evidence

Place the real Binance Futures Testnet order logs in this folder before
submitting the project.

Expected files:

```text
market_order.log
limit_order.log
```

Generate them after adding your `.env` credentials:

```powershell
$env:TRADING_BOT_LOG_FILE = "logs/examples/market_order.log"
python -B cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
Remove-Item Env:TRADING_BOT_LOG_FILE

$env:TRADING_BOT_LOG_FILE = "logs/examples/limit_order.log"
python -B cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 90000
Remove-Item Env:TRADING_BOT_LOG_FILE
```

If Binance rejects the limit order because of price, quantity, or precision,
adjust the command using current Futures Testnet symbol filters.

Do not commit or submit `.env`.
