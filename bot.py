import os
from threading import Thread
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters
)

from ai import speech_to_text, identify_department
from database import SessionLocal
from models import Complaint
from location_utils import get_location_details
from email_service import send_email
from letter_generator import generate_letter


BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ✅ TEST MODE EMAIL (sender + receiver)
TEST_EMAIL = "syedzunaid600@gmail.com"

# ✅ DEFAULT FALLBACK COMPLAINT
DEFAULT_COMPLAINT_TEXT = "Water supply issue in my area"


# -------------------- VOICE HANDLER --------------------
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.voice:
        return

    await update.message.reply_text(
        "📝 Complaint received. Processing in background..."
    )

    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)

    # Get stored location
    lat, lon = context.user_data.get("location", (None, None))
    if not lat:
        await update.message.reply_text(
            "📍 Please send your location first, then send the voice complaint."
        )
        return

    audio_path = f"voice_{update.message.from_user.id}.ogg"

    # 🔹 Try downloading voice
    try:
        await file.download_to_drive(audio_path)
    except Exception as e:
        print("Voice download timeout, using default complaint")

        Thread(
            target=process_complaint_with_text,
            args=(
                update.message.from_user.id,
                update.message.from_user.first_name,
                DEFAULT_COMPLAINT_TEXT,
                lat,
                lon
            ),
            daemon=True
        ).start()

        await update.message.reply_text(
            "⚠️ Voice processing took too long. Using default complaint (Water Issue)."
        )
        return

    # 🔹 Normal processing with STT
    Thread(
        target=process_complaint,
        args=(
            update.message.from_user.id,
            update.message.from_user.first_name,
            audio_path,
            lat,
            lon
        ),
        daemon=True
    ).start()

    await update.message.reply_text(
        "✅ Your complaint has been recorded successfully."
    )


# -------------------- BACKGROUND PROCESS (VOICE) --------------------
def process_complaint(user_id, user_name, audio_path, lat, lon):
    try:
        # 1️⃣ Speech → Text
        text = speech_to_text(audio_path)

        if not text or not text.strip():
            print("STT failed, using default complaint")
            text = DEFAULT_COMPLAINT_TEXT

        # Continue with common flow
        process_common_flow(user_id, user_name, text, lat, lon)

    except Exception as e:
        print("Background processing error:", e)


# -------------------- BACKGROUND PROCESS (DEFAULT TEXT) --------------------
def process_complaint_with_text(user_id, user_name, text, lat, lon):
    try:
        process_common_flow(user_id, user_name, text, lat, lon)
    except Exception as e:
        print("Default complaint processing error:", e)


# -------------------- COMMON PROCESSING LOGIC --------------------
def process_common_flow(user_id, user_name, text, lat, lon):
    # Identify department
    department = identify_department(text)

    # Reverse geocoding
    district, state = get_location_details(lat, lon)

    # Generate letter
    letter = generate_letter(
        name=user_name,
        issue=text,
        department=department,
        district=district,
        state=state
    )

    # Store in DB
    db = SessionLocal()
    complaint = Complaint(
        user_id=str(user_id),
        text=text,
        category=department,
        target_email=TEST_EMAIL,
        status="OPEN"
    )
    db.add(complaint)
    db.commit()
    db.close()

    # Send email
    send_email(
        to_email=TEST_EMAIL,
        subject="Citizen Grievance Submission (AUTO MODE)",
        body=letter
    )


# -------------------- LOCATION HANDLER --------------------
async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.location:
        return

    location = update.message.location
    context.user_data["location"] = (location.latitude, location.longitude)

    await update.message.reply_text(
        "📍 Location received successfully.\nNow send your voice complaint."
    )


# -------------------- START BOT --------------------
def start_bot():
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .read_timeout(30)
        .write_timeout(30)
        .connect_timeout(30)
        .pool_timeout(30)
        .build()
    )

    app.add_handler(MessageHandler(filters.LOCATION, handle_location))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    app.run_polling()
