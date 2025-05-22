@app.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    data = request.json
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id", "")

    if text.startswith("/addwallet "):
        wallet = text.split("/addwallet ")[1].strip()
        wallets = load_wallets()
        if wallet not in wallets:
            wallets.append(wallet)
            save_wallets(wallets)
            send_telegram_message(f"✅ Wallet `{wallet}` added.", chat_id)
        else:
            send_telegram_message("⚠️ Wallet already tracked.", chat_id)

    elif text.startswith("/removewallet "):
        wallet = text.split("/removewallet ")[1].strip()
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
