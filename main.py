from flask import Flask, request
import requests
import os
import json

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WALLETS_FILE = "wallets.json"

# Initialize wallet list
if not os.path.exists(WALLETS_FILE):
    with open(WALLETS_FILE, "w") as f:
        json.dump([], f)

def load_wallets():
    with open(WALLETS_FILE, "r") as f:
        return json.load(f)

def save_wallets(wallets):
    with open(WALLETS_FILE, "w") as f:
        json.dump(wallets, f)

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

@app.route("/", methods=["GET"])
def home():
    return "Bot is running", 200

@app.route("/webhook", methods=["POST"])
def helius_webhook():
    data = request.json
    for tx in data.get("transactions", []):
        if tx.get("type") == "SWAP":
            wallet = tx.get("accountData", {}).get("owner", "")
            wallets = load_wallets()
            if wallet in wallets:
                e = tx.get("events", {}).get("swap", {})
                msg = f"🟢 *Swap Detected*\nWallet: `{wallet}`\nIn: {e.get('amountIn')} of {e.get('tokenIn', {}).get('mint')}\nOut: {e.get('amountOut')} of {e.get('tokenOut', {}).get('mint')}"
                send_telegram_message(msg)
    return "", 200

@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    data = request.json
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id", "")

    if str(chat_id) != TELEGRAM_CHAT_ID:
        return "", 200  # Ignore others

    if text.startswith("/add "):
        wallet = text.split("/add ")[1].strip()
        wallets = load_wallets()
        if wallet not in wallets:
            wallets.append(wallet)
            save_wallets(wallets)
            send_telegram_message(f"✅ Wallet `{wallet}` added.")
        else:
            send_telegram_message("⚠️ Wallet already tracked.")

    elif text == "/list":
        wallets = load_wallets()
        if wallets:
            msg = "*Tracked Wallets:*\n" + "\n".join(wallets)
        else:
            msg = "No wallets added yet."
        send_telegram_message(msg)

    return "", 200

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
