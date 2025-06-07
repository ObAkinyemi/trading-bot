# Trading Bot Full Setup README

This README documents the complete journey of building, debugging, and deploying a fully automated Pine Script + FastAPI + Alpaca trading bot with webhook support, Discord notifications, and live paper trading capability.

---

## 🔧 Project Overview

* **Goal**: Create a fully automated trading bot that trades based on Pine Script signals (FVG, BOS, Candlestick, Support/Resistance) via Alpaca API.
* **Tools Used**:

  * Pine Script (TradingView)
  * FastAPI (Python backend)
  * Alpaca (Paper trading API)
  * Discord Webhook (for notifications)
  * Ngrok (for local testing)
  * Render (planned for deployment)

---

## 🧱 Project Architecture

1. **Pine Script Strategy**

   * Combines FVG, BOS, Engulfing Candles, and S/R
   * Fires alerts using `alertcondition()`
2. **Webhook Server** (`main.py`)

   * Accepts POST requests from TradingView
   * Validates and parses incoming JSON
   * Calculates position size using account equity
   * Sends market orders with bracket TP/SL to Alpaca
   * Notifies Discord of both errors and successful orders
   * Logs trades locally to `trades_log.csv`
3. **Deployment Options**

   * Tested locally using ngrok
   * Plan to deploy permanently to Render.com

---

## ✅ Accomplished Features

* ✅ Real-time Pine Script trade alerts
* ✅ Webhook API via FastAPI
* ✅ Alpaca market orders (with TP and SL via bracket orders)
* ✅ Equity-based dynamic position sizing
* ✅ Discord notifications (error + success)
* ✅ Logging trades to CSV
* ✅ Local testing via curl + ngrok

---

## 🛠️ Issues Encountered & How We Solved Them

### 1. **Webhook 404 Not Found**

* **Problem**: TradingView was hitting `/` instead of `/webhook`
* **Fix**: Ensured FastAPI had `@app.post("/webhook")` and confirmed the full URL in curl included `/webhook`

### 2. **Pine Script Alerts Not Firing Automatically**

* **Clarification**: Pine Script needs manual alert setup in TradingView
* **Fix**: Explained how to set alerts for `buySignal` and `sellSignal` conditions

### 3. **Ngrok Showing ERR\_NGROK\_3200 or Offline**

* **Problem**: Server or ngrok wasn’t running or timed out
* **Fix**: Restarted both FastAPI (`uvicorn`) and ngrok; updated the new ngrok URL in curl/TradingView

### 4. **FastAPI Terminal Shows 500 Internal Server Error**

* **Cause**: Calling `raise HTTPException(...)` without importing it
* **Fix**: Added `from fastapi import HTTPException`

### 5. **JSONDecodeError: Expecting value: line 1 column 1**

* **Cause**: curl was sending empty or malformed body
* **Fix**: Escaped double quotes properly in Bash:

  ```bash
  curl -X POST https://your-ngrok/webhook \
    -H "Content-Type: application/json" \
    -d "{\"ticker\":\"VWO\"}"
  ```

### 6. **Missing .env variables like BASE\_URL**

* **Cause**: Used `keys.env` file but didn't pass to `load_dotenv()`
* **Fix**: Changed to `load_dotenv("keys.env")`

### 7. **Webhook Response 400: Order Failed**

* **Cause**: Alpaca rejected order due to stop loss too close to entry price
* **Fix**: Replaced `round()` with a custom `round_down()` using `math.floor()`

### 8. **Alpaca Paper Account Balance = \$0**

* **Cause**: API keys were regenerated → new paper account created
* **Fix**: Opened a new paper account and reset it to \$100k

### 9. **Discord Not Receiving Notifications**

* **Cause**: `DISCORD_WEBHOOK` missing or invalid
* **Fix**: Added full webhook URL to `.env` and confirmed with test payload

### 10. **GitHub Push Failing with SSH**

* **Cause**: SSH key not properly added to GitHub account
* **Fix**: Verified SSH key with `ssh -T git@github.com` and added to GitHub settings

---

## 🔗 Pine Script Signal Behavior

* Small green upward-pointing triangles = buy signals (plotted using `plotshape()`)
* These fire alerts ONLY IF:

  * You create a TradingView alert using `buySignal`
  * You specify the correct webhook URL and JSON payload

---

## 🧾 How to Test the Bot with Curl

```bash
curl -X POST https://your-ngrok-url/webhook \
  -H "Content-Type: application/json" \
  -d "{\"action\":\"buy\", \"ticker\":\"VWO\", \"price\":48.24}"
```

---

## 🌐 Next Steps (Still Pending)

* ❌ Render deployment (Render push + environment vars not yet completed)
* ❌ Google Sheets logging integration (currently local CSV only)
* ❌ Automated backtesting or win/loss evaluation from logs

---

## 🚀 Conclusion

You now have a **fully automatic**, end-to-end Pine Script-powered trading bot that:

* Reacts to live chart conditions
* Places real orders with stop loss and take profit
* Manages position size based on risk
* Notifies you via Discord
* Logs trades for review

The final stretch is deployment + long-term optimization.

---

**Last synced:** June 7, 2025
**Status:** ✅ Core logic complete, 🟡 Deployment in progress
