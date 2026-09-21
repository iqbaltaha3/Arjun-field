"""Sarvam speech-to-text helpers for Arjun Field.

Long recordings are split in memory into <=25 second WAV chunks because
Sarvam's synchronous REST STT endpoint accepts at most 30 seconds/request.
The original recording is never written to disk.
"""

import io
import time
import requests
from pydub import AudioSegment

from config import SARVAM_API_KEY, SARVAM_STT_MODEL, SARVAM_STT_MODE

SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"
CHUNK_MS = 25_000
MAX_RECORDING_MS = 10 * 60 * 1000  # 10 minutes
REQUEST_TIMEOUT = 60
MAX_RETRIES = 3


def _transcribe_chunk(wav_bytes: bytes, chunk_number: int, total_chunks: int) -> str:
    if not SARVAM_API_KEY:
        raise RuntimeError("SARVAM_API_KEY is not configured.")

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            files = {
                "file": (f"field_note_{chunk_number:03d}.wav", io.BytesIO(wav_bytes), "audio/wav")
            }
            data = {
                "model": SARVAM_STT_MODEL,
                "mode": SARVAM_STT_MODE,
            }
            response = requests.post(
                SARVAM_STT_URL,
                headers={"api-subscription-key": SARVAM_API_KEY},
                files=files,
                data=data,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            transcript = response.json().get("transcript", "").strip()
            return transcript
        except requests.RequestException as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                time.sleep(1.5 * attempt)

    raise RuntimeError(
        f"Sarvam STT failed on chunk {chunk_number}/{total_chunks}: {last_error}"
    )


def transcribe(audio_bytes: bytes) -> str:
    """Transcribe one short recording using Sarvam REST STT."""
    return _transcribe_chunk(audio_bytes, 1, 1)


def transcribe_long(audio_bytes: bytes, progress_callback=None) -> str:
    """Transcribe a multi-minute recording by splitting it into short chunks.

    Audio is decoded and chunked in memory. Nothing is saved to disk.
    """
    if not audio_bytes:
        raise ValueError("The recording is empty.")
    if not SARVAM_API_KEY:
        raise RuntimeError("SARVAM_API_KEY is not configured.")

    try:
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
    except Exception as exc:
        raise RuntimeError(
            "Arjun could not read the recording. Please record again."
        ) from exc

    # Normalize to the format recommended for STT.
    audio = audio.set_channels(1).set_frame_rate(16_000)

    if len(audio) > MAX_RECORDING_MS:
        raise ValueError("Please keep a single field report under 10 minutes.")

    chunks = [audio[i:i + CHUNK_MS] for i in range(0, len(audio), CHUNK_MS)]
    transcripts = []
    total = len(chunks)

    for index, chunk in enumerate(chunks, start=1):
        buffer = io.BytesIO()
        chunk.export(buffer, format="wav", parameters=["-ac", "1", "-ar", "16000"])
        text = _transcribe_chunk(buffer.getvalue(), index, total)
        if text:
            transcripts.append(text)
        if progress_callback:
            progress_callback(index, total)

    return " ".join(transcripts).strip()