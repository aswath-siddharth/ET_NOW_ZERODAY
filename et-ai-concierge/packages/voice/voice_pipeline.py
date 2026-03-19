"""
ET AI Concierge — Voice Pipeline
Groq Whisper STT → LangGraph Orchestrator → Edge TTS
Connected via FastAPI WebSockets.
"""
import json
import asyncio
import io
import tempfile
import os
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect

try:
    import edge_tts
except ImportError:
    edge_tts = None

try:
    from groq import Groq
except ImportError:
    Groq = None

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agents"))
from config import settings


# ─── Groq Whisper STT ─────────────────────────────────────────────────────────

async def transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe audio using Groq's Whisper API."""
    if Groq is None or not settings.GROQ_API_KEY:
        return "[STT unavailable — Groq not configured]"

    client = Groq(api_key=settings.GROQ_API_KEY)

    # Save to temp file (Groq API requires a file)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio_bytes)
        temp_path = f.name

    try:
        with open(temp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=("audio.wav", audio_file),
                model="whisper-large-v3",
                language="en",
                response_format="text",
            )
        return transcription.strip()
    except Exception as e:
        return f"[Transcription error: {e}]"
    finally:
        os.unlink(temp_path)


# ─── Edge TTS Synthesis ──────────────────────────────────────────────────────

async def synthesize_speech(text: str, voice: str = None) -> bytes:
    """Convert text to speech using Edge TTS."""
    if edge_tts is None:
        return b""

    voice = voice or settings.EDGE_TTS_VOICE

    communicate = edge_tts.Communicate(text, voice)
    audio_chunks = []

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])

    return b"".join(audio_chunks)


# ─── Voice WebSocket Handler ─────────────────────────────────────────────────

async def voice_websocket_handler(websocket: WebSocket):
    """
    Full voice pipeline over WebSocket:
    1. Receive audio bytes from client
    2. Transcribe via Groq Whisper
    3. Process through the orchestrator
    4. Synthesize response via Edge TTS
    5. Send audio + text back
    """
    await websocket.accept()

    try:
        while True:
            # Receive audio data from client
            data = await websocket.receive_bytes()

            # 1. STT: Transcribe audio
            transcript = await transcribe_audio(data)

            # Send transcript back immediately
            await websocket.send_json({
                "type": "transcript",
                "text": transcript,
            })

            # 2. Process: Call the orchestrator
            # Import here to avoid circular dependency
            from orchestrator import chat
            from state import ChatRequest, ModalityType

            request = ChatRequest(
                message=transcript,
                user_id="voice_user",
                modality=ModalityType.VOICE,
            )
            response = await chat(request)

            # 3. TTS: Synthesize speech
            audio_response = await synthesize_speech(response.message)

            # Send text response
            await websocket.send_json({
                "type": "response",
                "text": response.message,
                "agent_used": response.agent_used,
            })

            # Send audio response
            if audio_response:
                await websocket.send_bytes(audio_response)

    except WebSocketDisconnect:
        print("Voice client disconnected")
    except Exception as e:
        print(f"Voice pipeline error: {e}")
        try:
            await websocket.close()
        except Exception:
            pass


# ─── Register with FastAPI app ────────────────────────────────────────────────

def register_voice_routes(app):
    """Register voice WebSocket endpoint with an existing FastAPI app."""

    @app.websocket("/api/voice")
    async def voice_endpoint(websocket: WebSocket):
        await voice_websocket_handler(websocket)

    @app.get("/api/voice/tts")
    async def text_to_speech(text: str, voice: str = None):
        """HTTP endpoint for one-shot TTS."""
        audio = await synthesize_speech(text, voice)
        if not audio:
            return {"error": "TTS not available"}
        from fastapi.responses import Response
        return Response(content=audio, media_type="audio/mpeg")

    return app
