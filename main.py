from fastapi import FastAPI, Request, HTTPException
import requests, os, csv
import math
from dotenv import load_dotenv

app = FastAPI()
load_dotenv("keys.env")  # or just ".env" if you're using a default-named file

ALPACA_KEY = os.getenv("ALPACA_KEY")
ALPACA_SECRET = os.getenv("ALPACA_SECRET")
BASE_URL = os.getenv("BASE_URL")
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

HEADERS = {
    "APCA-API-KEY-ID": ALPACA_KEY,
    "APCA-API-SECRET-KEY": ALPACA_SECRET
}

RISK_PERCENT = 0.01  # 1% of total equity per trade
TAKE_PROFIT_PERC = 0.015  # 1.5% TP
STOP_LOSS_PERC = 0.01     # 1.0% SL

# ---- Discord Messaging ----
def notify_discord(message):
    if not DISCORD_WEBHOOK:
        print("No Discord webhook configured.")
        return
    try:
        payload = {"content": message}
        r = requests.post(DISCORD_WEBHOOK, json=payload)
        if r.status_code != 204:
            print("Discord response error:", r.text)
    except Exception as e:
        print("Discord send failed:", e)

# ---- Equity-Based Position Sizing ----
def get_equity():
    try:
        r = requests.get(f"{BASE_URL}/v2/account", headers=HEADERS)
        r.raise_for_status()
        return float(r.json()["equity"])
    except Exception as e:
        notify_discord(f"❌ Failed to fetch equity: {e}")
        return 0

# ---- Local CSV Logging ----
def log_trade(symbol, qty, side, price, status):
    with open("trades_log.csv", mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([symbol, qty, side, price, status])
        
def round_down(value, decimals=2):
    factor = 10 ** decimals
    return math.floor(value * factor) / factor


# ---- Webhook Endpoint ----
@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        action = data.get("action")
        ticker = data.get("ticker")
        price = float(data.get("price", 0))

        if action not in ["buy", "sell"]:
            return {"status": "invalid action"}

        equity = get_equity()
        if equity == 0:
            raise ValueError("Equity not available")

        risk_amount = equity * RISK_PERCENT
        sl_price = price * (1 - STOP_LOSS_PERC) if action == "buy" else price * (1 + STOP_LOSS_PERC)
        qty = max(int(risk_amount / abs(price - sl_price)), 1)

        take_profit_price = price * (1 + TAKE_PROFIT_PERC) if action == "buy" else price * (1 - TAKE_PROFIT_PERC)
        stop_loss_price = sl_price

        order = {
            "symbol": ticker,
            "qty": qty,
            "side": action,
            "type": "market",
            "time_in_force": "gtc",
            "order_class": "bracket",
            "take_profit": {"limit_price": round(take_profit_price, 2)},
            "stop_loss": {"stop_price": round_down(stop_loss_price, 2)}
        }

        r = requests.post(f"{BASE_URL}/v2/orders", json=order, headers=HEADERS)
        response = r.json()
        print(f"{action.upper()} Order:", response)

        if r.status_code >= 400:
            notify_discord(f"❌ Order failed: {response}")
            raise HTTPException(status_code=400, detail="Order failed")

        # ✅ Clean Discord Message
        summary = (
            f"✅ **{action.upper()} order placed** for `{ticker}` at `${price}`\n"
            f"Qty: `{qty}` | TP: `{round(take_profit_price, 2)}` | SL: `{round(stop_loss_price, 2)}`"
        )
        notify_discord(summary)
        log_trade(ticker, qty, action, price, "submitted")

        return {"status": f"{action} order sent", "qty": qty}

    except Exception as e:
        error_msg = f"🔥 Webhook error: {e}"
        print(error_msg)
        notify_discord(error_msg)
        raise HTTPException(status_code=400, detail=str(e))
