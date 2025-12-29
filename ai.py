import os
import requests
import time

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

HEADERS = {
    "authorization": ASSEMBLYAI_API_KEY
}


def speech_to_text(audio_path: str):
    """
    Convert audio file to text using AssemblyAI.
    Returns None if transcription fails.
    """

    try:
        # 1️⃣ Upload audio
        with open(audio_path, "rb") as f:
            upload_response = requests.post(
                "https://api.assemblyai.com/v2/upload",
                headers=HEADERS,
                data=f,
                timeout=30
            )

        if upload_response.status_code != 200 or not upload_response.text:
            print("Audio upload failed")
            return None

        upload_data = upload_response.json()
        audio_url = upload_data.get("upload_url")

        if not audio_url:
            print("Upload URL missing")
            return None

        # 2️⃣ Request transcription
        transcript_response = requests.post(
            "https://api.assemblyai.com/v2/transcript",
            headers=HEADERS,
            json={"audio_url": audio_url},
            timeout=30
        )

        if transcript_response.status_code != 200 or not transcript_response.text:
            print("Transcript request failed")
            return None

        transcript_data = transcript_response.json()
        transcript_id = transcript_data.get("id")

        if not transcript_id:
            print("Transcript ID missing")
            return None

        # 3️⃣ Poll for result
        while True:
            status_response = requests.get(
                f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                headers=HEADERS,
                timeout=30
            )

            if status_response.status_code != 200 or not status_response.text:
                print("Status check failed")
                return None

            status_data = status_response.json()
            status = status_data.get("status")

            if status == "completed":
                text = status_data.get("text")
                return text

            if status == "error":
                print("Speech recognition failed:", status_data.get("error"))
                return None

            time.sleep(2)

    except Exception as e:
        print("Speech-to-text error:", e)
        return None


def identify_department(text: str) -> str:
    """
    Simple rule-based department identification.
    """

    if not text:
        return "General Grievance Cell"

    text = text.lower()

    if "water" in text:
        return "Water Supply Department"
    if "electricity" in text or "power" in text:
        return "Electricity Board"
    if "road" in text or "pothole" in text:
        return "Municipal Corporation"
    if "garbage" in text or "waste" in text:
        return "Sanitation Department"
    if "corruption" in text or "bribe" in text:
        return "Anti-Corruption Bureau"

    return "General Grievance Cell"
