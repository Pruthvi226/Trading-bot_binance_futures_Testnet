# Submission Deliverables

This project is ready for submission. The live Binance Futures Testnet MARKET
and LIMIT evidence logs have been generated with the provided testnet API
credentials.

## Included Files

- `bot/` source package
- `cli.py` required command-line entry point
- `ui.py` optional lightweight local web UI
- `README.md` setup, usage, assumptions, troubleshooting, and examples
- `ACCEPTANCE_CHECKLIST.md` grading criteria self-review
- `SUBMISSION_SUMMARY.md` completed local and live verification summary
- `requirements.txt`
- `.env.example`
- `tests/` local test coverage
- `logs/examples/` folder for real order evidence logs

## Local Verification Already Completed

These checks passed locally:

```text
python -B -m unittest discover -s tests
```

Output:

```text
..........
----------------------------------------------------------------------
Ran 10 tests in 0.024s

OK
```

CLI help was verified:

```text
python -B cli.py --help
```

UI help was verified:

```text
python -B ui.py --help
```

The lightweight UI was also smoke-tested at:

```text
http://127.0.0.1:8000
```

## Regenerate Evidence Logs If Needed

### 1. Add Binance Futures Testnet credentials

Create `.env` from `.env.example`:

```powershell
Copy-Item .env.example .env
```

Edit `.env`:

```env
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret
BINANCE_BASE_URL=https://testnet.binancefuture.com
```

Use Binance Futures Testnet keys only. Do not use production Binance keys.

### 2. Activate your virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Generate MARKET order log

Run a small MARKET order on testnet:

```powershell
$env:TRADING_BOT_LOG_FILE = "logs/examples/market_order.log"
python -B cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
Remove-Item Env:TRADING_BOT_LOG_FILE
```

### 4. Generate LIMIT order log

Choose a valid limit price from the Binance Futures Testnet UI. Then run:

```powershell
$env:TRADING_BOT_LOG_FILE = "logs/examples/limit_order.log"
python -B cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 90000
Remove-Item Env:TRADING_BOT_LOG_FILE
```

If Binance rejects the price or precision, adjust `--price` and `--quantity`
based on the testnet symbol filters.

### 5. Confirm evidence files exist

```powershell
Get-ChildItem logs\examples
```

You should see:

```text
market_order.log
limit_order.log
```

Each log should include a successful API status code and an order response with
fields such as `orderId`, `status`, `executedQty`, and `avgPrice` when Binance
returns it.

### 6. Optional UI demo

Run the UI:

```powershell
python -B ui.py --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

Use Preview first, then Submit Order after validating the request.

### 7. Create a zip submission

After the real logs exist, create the submission zip:

```powershell
Compress-Archive -Force -DestinationPath Trading-Bot-Submission.zip -Path bot,tests,logs,cli.py,ui.py,README.md,DELIVERABLES.md,ACCEPTANCE_CHECKLIST.md,SUBMISSION_SUMMARY.md,requirements.txt,.env.example,.gitignore
```

Do not include `.env` in the zip. The `.gitignore` already excludes it.

## Final Submission Checklist

- Source code included
- README included
- ACCEPTANCE_CHECKLIST.md included
- SUBMISSION_SUMMARY.md included
- requirements.txt included
- `.env.example` included
- `.env` not included
- MARKET order log included at `logs/examples/market_order.log`
- LIMIT order log included at `logs/examples/limit_order.log`
- Local tests pass with `python -B -m unittest discover -s tests`
- Optional UI included and documented
