import os
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
)

from ai import speech_to_text, identify_department
from database import SessionLocal
from models import Complaint
from location_utils import get_location_details
from email_service import send_email
from letter_generator import generate_letter


# ================= CONFIG =================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

TEST_EMAIL = "syedzunaid600@gmail.com"
DEFAULT_COMPLAINT_TEXT = "Water supply issue in my area"


# ================= HANDLERS =================
async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.location:
        return

    loc = update.message.location
    context.user_data["location"] = (loc.latitude, loc.longitude)

    await update.message.reply_text(
        "📍 Location received successfully.\nNow send your voice complaint."
    )


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.voice:
        return

    await update.message.reply_text(
        "📝 Complaint received. Processing..."
    )

    lat, lon = context.user_data.get("location", (None, None))
    if not lat:
        await update.message.reply_text(
            "📍 Please send your location first."
        )
        return

    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)
    audio_path = f"voice_{update.message.from_user.id}.ogg"

    try:
        await file.download_to_drive(audio_path)
        await asyncio.to_thread(
            process_complaint,
            update.message.from_user.id,
            update.message.from_user.first_name,
            audio_path,
            lat,
            lon,
        )
    except Exception:
        await asyncio.to_thread(
            process_complaint_with_text,
            update.message.from_user.id,
            update.message.from_user.first_name,
            DEFAULT_COMPLAINT_TEXT,
            lat,
            lon,
        )

        await update.message.reply_text(
            "⚠️ Voice processing failed. Using default complaint."
        )
        return

    await update.message.reply_text(
        "✅ Your complaint has been recorded successfully."
    )


# ================= PROCESSING LOGIC =================
def process_complaint(user_id, user_name, audio_path, lat, lon):
    try:
        text = speech_to_text(audio_path)
        if not text or not text.strip():
            text = DEFAULT_COMPLAINT_TEXT
        process_common_flow(user_id, user_name, text, lat, lon)
    except Exception as e:
        print("Voice processing error:", e)


def process_complaint_with_text(user_id, user_name, text, lat, lon):
    try:
        process_common_flow(user_id, user_name, text, lat, lon)
    except Exception as e:
        print("Text processing error:", e)


def process_common_flow(user_id, user_name, text, lat, lon):
    department = identify_department(text)
    district, state = get_location_details(lat, lon)

    letter = generate_letter(
        name=user_name,
        issue=text,
        department=department,
        district=district,
        state=state,
    )

    db = SessionLocal()
    complaint = Complaint(
        user_id=str(user_id),
        text=text,
        category=department,
        target_email=TEST_EMAIL,
        status="OPEN",
    )
    db.add(complaint)
    db.commit()
    db.close()

    send_email(
        to_email=TEST_EMAIL,
        subject="Citizen Grievance Submission (AUTO MODE)",
        body=letter,
    )


# ================= APPLICATION FACTORY =================
def create_telegram_app() -> Application:
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    return app
