from flask import Flask, request
import requests
import os
import json

app = Flask(__name__)  # Must be before any @app.route decorator

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WALLETS_FILE = "wallets.json"

# Initialize wallets file if it doesn't exist
if not os.path.exists(WALLETS_FILE):
    with open(WALLETS_FILE, "w") as f:
        json.dump([], f)

def load_wallets():
    with open(WALLETS_FILE, "r") as f:
        return json.load(f)

def save_wallets(wallets):
    with open(WALLETS_FILE, "w") as f:
        json.dump(wallets, f)

def send_telegram_message(text, chat_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
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
    wallets = load_wallets()
    for tx in data.get("transactions", []):
        if tx.get("type") == "SWAP":
            wallet = tx.get("accountData", {}).get("owner", "")
            if wallet in wallets:
                e = tx.get("events", {}).get("swap", {})
                msg = (
                    f"🟢 *Swap Detected*\n"
                    f"Wallet: `{wallet}`\n"
                    f"In: {e.get('amountIn')} of {e.get('tokenIn', {}).get('mint')}\n"
                    f"Out: {e.get('amountOut')} of {e.get('tokenOut', {}).get('mint')}"
                )
                chat_id = os.getenv("TELEGRAM_CHAT_ID")
                if chat_id:
                    send_telegram_message(msg, chat_id)
    return "", 200

@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    data = request.json
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id", "")

    if text.startswith("/addwallet "):
        wallet = text[len("/addwallet "):].strip()
        wallets = load_wallets()
        if wallet not in wallets:
            wallets.append(wallet)
            save_wallets(wallets)
            send_telegram_message(f"✅ Wallet `{wallet}` added.", chat_id)
        else:
            send_telegram_message("⚠️ Wallet already tracked.", chat_id)

    elif text.startswith("/removewallet "):
        wallet = text[len("/removewallet "):].strip()
        wallets = load_wallets()
        if wallet in wallets:
            wallets.remove(wallet)
            save_wallets(wallets)
            send_telegram_message(f"🗑️ Wallet `{wallet}` removed.", chat_id)
        else:
            send_telegram_message("⚠️ Wallet not found.", chat_id)

    elif text == "/list":
        wallets = load_wallets()
        if wallets:
            msg = "*Tracked Wallets:*\n" + "\n".join(wallets)
        else:
            msg = "No wallets added yet."
        send_telegram_message(msg, chat_id)

    else:
        send_telegram_message("Unknown command. Use /addwallet <wallet>, /removewallet <wallet>, or /list", chat_id)

    return "", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
