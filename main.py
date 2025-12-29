from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import ApplicationBuilder
import os

from bot import handle_voice, handle_location

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

app = FastAPI()

telegram_app = (
    ApplicationBuilder()
    .token(BOT_TOKEN)
    .build()
)

telegram_app.add_handler(
    MessageHandler(filters.LOCATION, handle_location)
)
telegram_app.add_handler(
    MessageHandler(filters.VOICE, handle_voice)
)

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
