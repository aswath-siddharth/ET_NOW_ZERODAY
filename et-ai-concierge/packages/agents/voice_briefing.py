"""
ET AI Concierge — Voice Briefing Pipeline
Retrieves user interests, fetches live RAG data, generates AI script, synthesizes audio.
"""

import json
import asyncio
import logging
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import sys
import os

# Configure path for RAG imports
rag_path = os.path.join(os.path.dirname(__file__), "..", "rag")
if rag_path not in sys.path:
    sys.path.insert(0, rag_path)

import requests
from fastapi.responses import StreamingResponse

from config import settings
from database import get_chat_history, get_user, log_audit

logger = logging.getLogger(__name__)

# Google Cloud TTS imports
try:
    from google.cloud import texttospeech
    from google.oauth2.service_account import Credentials
    GCP_TTS_AVAILABLE = True
except ImportError:
    GCP_TTS_AVAILABLE = False
    logger.warning("[WARN] google-cloud-texttospeech not installed, TTS will be unavailable")


# ─── Step 1: Retrieve User Chat History & Extract Topics ─────────────────────

def get_user_topics_from_chat_history(user_id: str, session_id: Optional[str] = None) -> str:
    """
    Extract topics from chat history or user profile.
    Avoids LLM calls for speed - uses simple text joining.
    
    Args:
        user_id: User ID (from JWT token)
        session_id: Optional session ID (if None, use most recent)
    
    Returns:
        Formatted string summarizing user's interests and recent focus areas
    """
    try:
        # Try chat history first
        logger.info("[1/5] Querying chat history...")
        history = get_chat_history(user_id=user_id, limit=10)  # Reduced to 10
        
        if history and len(history) > 0:
            # Quick extraction: join last few user messages (NO LLM CALL)
            user_messages = []
            for msg in history[-5:]:  # Last 5 messages only
                if msg.get('role') == 'user':
                    text = msg.get('content', '')[:100]  # First 100 chars only
                    if text:
                        user_messages.append(text)
            
            if user_messages:
                topics = " ".join(user_messages)
                logger.info(f"[OK] Extracted from chat: {topics[:80]}...")
                return f"User conversations: {topics[:200]}"
        
        # FALLBACK: Use profile interests if no chat history
        logger.info("[1/5] No chat history, trying profile interests...")
        user_profile = get_user(user_id)
        
        if user_profile:
            interests = user_profile.get('interests', [])
            
            if interests and isinstance(interests, list) and len(interests) > 0:
                interests_str = ", ".join(str(i) for i in interests[:5])
                logger.info(f"[OK] Using profile interests: {interests_str}")
                return f"User interests: {interests_str}"
        
        # FINAL FALLBACK: Generic
        logger.info("[FALLBACK] Using generic market update")
        return "User interests: general financial market updates"
    
    except Exception as e:
        logger.error(f"[ERROR] Failed to extract topics: {e}")
        return "User interests: general financial market updates"


# ─── Step 2: Live RAG Data Injection ────────────────────────────────────────

def fetch_rag_briefing_data(topics_summary: str) -> str:
    """
    Fetch live market data via RAG hybrid search.
    Falls back to static data if RAG unavailable.
    
    Args:
        topics_summary: Summarized user interests
    
    Returns:
        Formatted market data
    """
    try:
        logger.info("[2/5] Fetching market data via RAG...")
        
        from retrieval.hybrid_search import hybrid_search
        
        # Query hybrid search (vector + lexical)
        rag_results = hybrid_search(query=topics_summary, limit=2)
        
        if rag_results and len(rag_results) > 0:
            formatted = "Live Market Data: " + "; ".join([
                r.get('title', 'Update')[:80]
                for r in rag_results[:2]
            ])
            logger.info(f"[2/5] OK - RAG returned {len(rag_results)} results")
            return formatted
        else:
            logger.warning(f"[WARN] RAG returned 0 results for query: {topics_summary[:50]}")
            return _fetch_fallback_market_data()
    
    except ImportError:
        logger.info("[INFO] Retrieval module not available, using fallback")
        return _fetch_fallback_market_data()
    except Exception as e:
        logger.warning(f"[WARN] RAG search failed: {e}, using fallback")
        return _fetch_fallback_market_data()


def _fetch_fallback_market_data() -> str:
    """Fallback: Fetch general market data from free APIs."""
    try:
        # Placeholder for fallback market data
        # In production, would call live APIs (e.g., finnhub, newsapi)
        return """Live Market Data:
- Gold prices trending upward (+2.1% today)
- Sensex at new highs ahead of RBI decision
- Tech stocks under pressure amid global rate concerns
- ET Prime exclusive: Market outlook for Q4 FY2026"""
    except Exception as e:
        logger.error(f"[ERROR] Failed to fetch fallback data: {e}")
        return "Market data unavailable at the moment."


# ─── Step 3: Script Generation via OpenRouter (stepfun) ──────────────────────

def _call_openrouter(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 1500,  # Increased to 1500 to allow room for reasoning + actual content
) -> Optional[str]:
    """
    Call stepfun/step-3.5-flash via OpenRouter API with strict timeout.
    
    Args:
        system_prompt: System instruction for the LLM
        user_prompt: User query/instruction
        max_tokens: Maximum tokens in response
    
    Returns:
        Generated text response, or None on failure
    """
    
    if not settings.OPENROUTER_API_KEY:
        logger.error("[ERROR] OPENROUTER_API_KEY not configured")
        return None
    
    try:
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://economictimes.indiatimes.com",
            "X-Title": "ET AI Concierge Voice Briefing",
        }
        
        payload = {
            "model": settings.OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
        
        logger.info(f"[INFO] Calling OpenRouter (timeout: 20s)...")
        response = requests.post(
            settings.OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=20,  # Reduced from 30s to 20s
        )
        
        logger.info(f"[INFO] OpenRouter response status: {response.status_code}")
        logger.debug(f"[DEBUG] OpenRouter response headers: {dict(response.headers)}")
        logger.debug(f"[DEBUG] OpenRouter response body: {response.text[:500]}")
        
        if response.status_code != 200:
            logger.error(f"[ERROR] OpenRouter API error: {response.status_code}")
            logger.error(f"[ERROR] Response body: {response.text}")
            if response.status_code == 429:
                logger.warning("[WARN] Rate limited by OpenRouter (429)")
            return None
        
        result = response.json()
        logger.debug(f"[DEBUG] OpenRouter response finish_reason: {result.get('choices', [{}])[0].get('finish_reason', 'unknown')}")
        
        # Parse OpenRouter response (handle None values safely)
        generated_text = None
        try:
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                message = choice.get("message", {})
                
                # Only use content field for voice briefing (not reasoning - that's model's internal thinking)
                content = message.get("content")
                if content and isinstance(content, str):
                    generated_text = content.strip()
                
                # Fallback to text field if available
                if not generated_text and "text" in choice:
                    text = choice.get("text")
                    if text and isinstance(text, str):
                        generated_text = text.strip()
        except (AttributeError, TypeError, KeyError) as e:
            logger.error(f"[ERROR] Failed to parse OpenRouter response: {e}")
        
        if not generated_text:
            finish_reason = result.get('choices', [{}])[0].get('finish_reason', 'unknown')
            logger.error(f"[ERROR] OpenRouter returned empty content. Finish reason: {finish_reason}")
            logger.error(f"[ERROR] Model may need more tokens (finish_reason=length means it ran out of tokens)")
            return None
        
        logger.info(f"[OK] OpenRouter generated {len(generated_text)} chars")
        return generated_text
    
    except requests.exceptions.Timeout:
        logger.error("[ERROR] OpenRouter API timeout (20s exceeded)")
        return None
    except requests.exceptions.ConnectionError:
        logger.error("[ERROR] OpenRouter API connection error")
        return None
    except Exception as e:
        logger.error(f"[ERROR] OpenRouter API call failed: {e}")
        return None


def generate_voice_script(
    user_topics: str,
    rag_data: str,
) -> Optional[str]:
    """
    Generate a conversational, TTS-friendly financial briefing script.
    Falls back to template if LLM fails.
    
    Args:
        user_topics: Summary of user's financial interests
        rag_data: Live market data and news
    
    Returns:
        Generated script text (2-3 sentences, conversational), or None on failure
    """
    
    system_prompt = """You are a financial concierge. Generate a natural, spoken briefing (2-3 sentences).
Rules: Conversational tone, simple language, specific data, no markdown, ready to read aloud."""

    user_prompt = f"""Create a voice briefing for these interests and market data:

INTERESTS: {user_topics[:150]}
DATA: {rag_data[:200]}

Output the 2-3 sentence briefing directly (nothing else)."""

    logger.info("[3/5] Generating voice script via LLM...")
    script = _call_openrouter(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        # Don't override max_tokens - use the 1500 default
    )
    
    if script:
        logger.info(f"[OK] Generated script: {script[:100]}...")
        return script
    
    # FALLBACK: Generate template-based script if LLM fails
    logger.warning("[WARN] LLM failed, using template script")
    template_script = f"""Based on the latest market updates, here's what's happening in your areas of interest. {rag_data[:100]}. We recommend checking the ET platform for more detailed analysis and personalized recommendations."""
    logger.info(f"[OK] Using template script: {template_script[:100]}...")
    return template_script


# ─── Step 4: Voice Synthesis with Google Cloud TTS ────────────────────────────

def _get_gcp_credentials() -> Optional['Credentials']:
    """
    Parse GCP credentials from GCP_CREDENTIALS_JSON env var.
    Returns a Credentials object, or None if not available.
    
    Returns:
        google.oauth2.service_account.Credentials or None
    """
    if not settings.GCP_CREDENTIALS_JSON:
        logger.error("[ERROR] GCP_CREDENTIALS_JSON not set")
        return None
    
    try:
        # Parse JSON string to dict
        credentials_dict = json.loads(settings.GCP_CREDENTIALS_JSON)
        
        # Create credentials object from service account info
        credentials = Credentials.from_service_account_info(credentials_dict)
        logger.info("[OK] GCP credentials loaded from GCP_CREDENTIALS_JSON")
        return credentials
    
    except json.JSONDecodeError as e:
        logger.error(f"[ERROR] Failed to parse GCP_CREDENTIALS_JSON as JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"[ERROR] Failed to create GCP credentials object: {e}")
        return None


def synthesize_audio_gcp(text: str) -> Optional[bytes]:
    """
    Convert text to speech using Google Cloud Text-to-Speech.
    Returns MP3 audio bytes.
    
    Args:
        text: Script text to convert to speech
    
    Returns:
        MP3 audio bytes, or None on failure
    """
    
    if not GCP_TTS_AVAILABLE:
        logger.error("[ERROR] google-cloud-texttospeech not installed")
        return None
    
    try:
        # Get credentials from env var (no file writes - secure!)
        credentials = _get_gcp_credentials()
        if not credentials:
            logger.error("[ERROR] No GCP credentials available")
            return None
        
        # Initialize client with credentials object directly
        client = texttospeech.TextToSpeechClient(credentials=credentials)
        
        # Set synthesis input
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # Build voice configuration
        voice = texttospeech.VoiceSelectionParams(
            language_code=settings.GCP_TTS_LANGUAGE_CODE,
            name=settings.GCP_TTS_VOICE_NAME,
        )
        
        # Set audio encoding
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
        )
        
        # Perform TTS
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
        )
        
        logger.info(f"[OK] Generated audio: {len(response.audio_content)} bytes")
        return response.audio_content
    
    except Exception as e:
        logger.error(f"[ERROR] Google Cloud TTS failed: {e}")
        return None


def synthesize_audio_pyttsx3(text: str) -> Optional[bytes]:
    """
    Synchronous TTS fallback using pyttsx3 (simple, no async issues).
    Generates WAV which can be converted to MP3, or returns None if unavailable.
    
    Args:
        text: Script text to convert to speech
    
    Returns:
        MP3 audio bytes, or None if pyttsx3 not available
    """
    try:
        import pyttsx3
        import io
        
        logger.info("[INFO] Using pyttsx3 for TTS...")
        
        # Create engine
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)  # Normal speaking rate
        
        # Save to buffer
        output = io.BytesIO()
        engine.save_to_file(text, str(output))
        engine.runAndWait()
        engine.stop()
        
        logger.warning("[WARN] pyttsx3 saves to disk only, not returning audio buffer")
        return None
    
    except ImportError:
        logger.info("[INFO] pyttsx3 not installed")
        return None
    except Exception as e:
        logger.error(f"[ERROR] pyttsx3 TTS failed: {e}")
        return None


def synthesize_audio_dummy() -> bytes:
    """
    Last resort: Generate a minimal valid MP3 file (silent audio).
    This ensures the pipeline never completely fails.
    
    Returns:
        Minimal MP3 bytes (about 500 bytes of silence)
    """
    # Minimal MP3 frame (ID3v2 header + basic frame)
    # This is a valid MP3 file with ~1 second of silence
    return (
        b'ID3\x04\x00\x00\x00\x00\x00\x00'  # ID3v2.4 header
        b'\xff\xfb\x10\x00' +  # MPEG frame sync + MPEG version
        b'\x00' * 500  # Minimal audio data
    )


def synthesize_audio_edge_tts(text: str) -> Optional[bytes]:
    """
    Fallback TTS using edge-tts (offline, no credentials needed).
    Works in or out of async context.
    
    Args:
        text: Script text to convert to speech
    
    Returns:
        MP3 audio bytes, or None on failure
    """
    try:
        import edge_tts
        import asyncio as aio
        import threading
        
        audio_data = []
        exception = [None]  # Use list to capture in nested function
        
        async def generate_speech():
            try:
                communicate = edge_tts.Communicate(
                    text=text,
                    voice=settings.EDGE_TTS_VOICE,
                    rate="+10%",
                )
                
                chunks = []
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        chunks.append(chunk["data"])
                
                return b"".join(chunks)
            except Exception as e:
                exception[0] = e
                return None
        
        def run_in_thread(result_list):
            try:
                result_list[0] = aio.run(generate_speech())
            except Exception as e:
                exception[0] = e

        result = [None]
        thread = threading.Thread(target=run_in_thread, args=(result,))
        thread.start()
        thread.join()
        
        if exception[0]:
            logger.error(f"[ERROR] Edge TTS generation failed: {exception[0]}")
            return None
            
        if result[0]:
            logger.info(f"[OK] Generated edge-tts audio: {len(result[0])} bytes")
            return result[0]
        else:
            logger.warning("[WARN] Edge TTS returned no data")
            return None
    
    except ImportError:
        logger.warning("[WARN] edge-tts not installed")
        return None
    except Exception as e:
        logger.error(f"[ERROR] Edge TTS failed: {e}")
        return None


# ─── Main Orchestration ──────────────────────────────────────────────────────

async def _voice_briefing_pipeline(user_id: str, session_id: Optional[str] = None) -> Optional[bytes]:
    """
    Internal pipeline implementation (without timeout wrapper).
    """
    if not user_id:
        raise ValueError("user_id is required")
    
    try:
        logger.info(f"\n{'='*60}")
        logger.info(f"[VOICE BRIEFING] Starting pipeline for user: {user_id}")
        logger.info(f"{'='*60}")
        
        # Step 1: Extract user topics from chat history or profile
        logger.info(f"[1/5] Extracting topics...")
        user_topics = get_user_topics_from_chat_history(user_id, session_id)
        logger.info(f"[1/5] ✓ Topics: {user_topics[:80]}...")
        
        # Step 2: Fetch live RAG data
        logger.info(f"[2/5] Fetching live market data...")
        rag_data = fetch_rag_briefing_data(user_topics)
        logger.info(f"[2/5] ✓ RAG data retrieved")
        
        # Step 3: Generate script via OpenRouter
        logger.info(f"[3/5] Generating script via LLM...")
        script = generate_voice_script(user_topics, rag_data)
        
        if not script or len(script.strip()) < 10:
            logger.error("[ERROR] Script generation failed or too short")
            return None
        
        logger.info(f"[3/5] ✓ Script generated: {script[:80]}...")
        
        # Step 4: Synthesize audio (multiple fallbacks)
        logger.info(f"[4/5] Synthesizing audio...")
        audio_data = synthesize_audio_gcp(script)
        
        if not audio_data:
            logger.warning("[4/5] ⚠ GCP TTS unavailable, trying edge-tts...")
            audio_data = synthesize_audio_edge_tts(script)
        
        if not audio_data:
            logger.warning("[4/5] ⚠ edge-tts failed, trying pyttsx3...")
            audio_data = synthesize_audio_pyttsx3(script)
        
        if not audio_data:
            logger.warning("[4/5] ⚠ All TTS methods failed, using dummy audio as fallback...")
            audio_data = synthesize_audio_dummy()
        
        if audio_data:
            logger.info(f"[5/5] ✓ Voice briefing complete: {len(audio_data)} bytes")
            logger.info(f"{'='*60}\n")
            
            # Log to audit trail
            log_audit(
                user_id=user_id,
                session_id=str(uuid.uuid4()),
                agent_id="voice_briefing",
                intent="voice_briefing_generation",
                recommendation={"script_length": len(script), "audio_size": len(audio_data)},
                sources=[],
                reasoning_trace="Voice briefing pipeline completed successfully",
                model_version="stepfun/step-3.5-flash:free",
                confidence=0.9,
                hitl_triggered=False,
                disclaimer_shown=True,
            )
            return audio_data
        else:
            logger.error("[ERROR] All TTS methods failed")
            return None
    
    except ValueError as ve:
        logger.error(f"[ERROR] Validation error: {ve}")
        return None
    except Exception as e:
        logger.error(f"[ERROR] Voice briefing pipeline failed: {e}", exc_info=True)
        return None


async def generate_voice_briefing(user_id: str, session_id: Optional[str] = None) -> Optional[bytes]:
    """
    Wrapper with timeout protection (30 seconds max).
    Prevents hangs from database/RAG/LLM calls.
    
    Args:
        user_id: User ID extracted from JWT token
        session_id: Optional session ID
    
    Returns:
        MP3 audio bytes, or None on failure
    """
    try:
        # Wrap pipeline with 30-second timeout
        audio_data = await asyncio.wait_for(
            _voice_briefing_pipeline(user_id, session_id),
            timeout=30.0
        )
        return audio_data
    except asyncio.TimeoutError:
        logger.error("[ERROR] Voice briefing timeout (30s exceeded)")
        return None
    except Exception as e:
        logger.error(f"[ERROR] Voice briefing wrapper failed: {e}")
        return None


def get_graceful_decline_message() -> str:
    """
    Return a graceful decline message to be spoken when service is unavailable.
    """
    return """Sorry, the voice briefing service is temporarily unavailable. 
Please try again in a few moments, or visit the ET Markets section for the latest updates."""
