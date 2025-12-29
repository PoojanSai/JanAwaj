from fastapi import FastAPI, Request
import os
from telegram import Update

from bot import create_telegram_app

app = FastAPI()

telegram_app = create_telegram_app()


@app.on_event("startup")
async def startup():
    base_url = os.getenv("RENDER_EXTERNAL_URL")
    if base_url:
        webhook_url = f"{base_url}/telegram/webhook"
        await telegram_app.bot.set_webhook(webhook_url)
        print("✅ Telegram webhook registered")


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}


@app.get("/")
def health():
    return {"status": "ok"}
