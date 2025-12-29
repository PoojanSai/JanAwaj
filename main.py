from fastapi import FastAPI
from bot import start_bot
import threading

app = FastAPI()

@app.on_event("startup")
def start_services():
    # Start Telegram bot in background thread
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.daemon = True
    bot_thread.start()

@app.get("/")
def health():
    return {"status": "ok"}
