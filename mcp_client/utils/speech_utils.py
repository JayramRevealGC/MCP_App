import os
import hashlib
import tempfile
import streamlit as st
from faster_whisper import WhisperModel

from .chat_utils import get_current_chat

###########
# Helpers #
###########
def has_cuda() -> bool:
    # library-agnostic check (Torch optional)
    try:
        import torch
        return torch.cuda.is_available()
    except Exception:
        # If torch isn't installed, fall back to env hints
        return bool(os.environ.get("CUDA_VISIBLE_DEVICES"))

def sha1_bytes(b: bytes) -> str:
    h = hashlib.sha1()
    h.update(b)
    return h.hexdigest()

def add_user_message(text: str, audio_bytes: bytes | None = None):
    message = {"role": "user", "content": text, "audio": audio_bytes}
    
    # Get current chat
    current_chat = get_current_chat()
    
    if current_chat:
        # Add to existing chat's messages
        if "messages" not in current_chat:
            current_chat["messages"] = []
        current_chat["messages"].append(message)
    else:
        # Fallback: add to session_state.messages if no active chat
        if "messages" not in st.session_state:
            st.session_state.messages = []
        st.session_state.messages.append(message)

###############
# Cache Model #
###############
@st.cache_resource(show_spinner="Loading Whisper model…")
def load_model_cached(model: str, device: str, compute_type: str):
    return WhisperModel(model, device=device, compute_type=compute_type)

#########################
# Sidebar Configuration #
#########################
def render_speech_settings():
    """
    Render sidebar with model settings and controls.
    Initializes session state, provides model configuration options,
    and loads the Whisper model with selected settings.
    
    Returns:
        WhisperModel: The loaded Whisper model instance
    """
    # Initialize session state defaults
    if "device" not in st.session_state:
        st.session_state.device = "cuda" if has_cuda() else "cpu"
    if "compute_type" not in st.session_state:
        st.session_state.compute_type = "float16" if st.session_state.device == "cuda" else "int8"
    if "model_size" not in st.session_state:
        st.session_state.model_size = "small"
    if "last_audio_hash" not in st.session_state:
        st.session_state.last_audio_hash = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Configuration options
    model_list = ["tiny", "base", "small", "medium", "large-v3"]
    device_list = ["cpu", "cuda"]
    compute_type_list = ["int8", "float16", "float32"]
    
    # Render sidebar UI
    with st.sidebar:
        st.header("Speech Settings")
        
        # Model configuration selectors
        model_size = st.selectbox(
            "Model", 
            model_list, 
            index=model_list.index(st.session_state.model_size)
        )
        device = st.selectbox(
            "Device", 
            device_list, 
            index=device_list.index(st.session_state.device)
        )
        compute_type = st.selectbox(
            "Precision", 
            compute_type_list, 
            index=compute_type_list.index(st.session_state.compute_type)
        )
        
        # Persist user choices
        st.session_state.device = device
        st.session_state.compute_type = compute_type
        st.session_state.model_size = model_size
        
        # Load model with selected settings
        model = load_model_cached(
            st.session_state.model_size, 
            st.session_state.device, 
            st.session_state.compute_type
        )
        
        # Show success message
        st.success(
            f"Model loaded: Whisper {st.session_state.model_size} "
            f"on {st.session_state.device} ({st.session_state.compute_type})"
        )
        
        return model

#####################
# Chat Display Area #
#####################
def render_chat_history():
    """
    Render the conversation history from session state.
    Displays user messages with optional audio playback.
    """    
    for msg in st.session_state.messages:
        with st.chat_message("user"):
            st.write(msg["content"])
            if msg.get("audio"):
                with st.expander("🎧 Audio clip"):
                    st.audio(msg["audio"])
    
    st.write("---")

###################
# Audio Component #
###################
def render_audio_transcription(model) -> None:
    """
    Render audio input component and handle automatic transcription.
    
    Args:
        model: The loaded WhisperModel instance for transcription
        
    Features:
        - Records audio at 48kHz sample rate
        - Automatically transcribes new audio
        - Caches transcriptions by audio hash to avoid re-processing
        - Adds transcribed text to chat history
    """
    
    # Transcription cache (per audio hash)
    @st.cache_data(show_spinner="Procressing audio…")
    def transcribe_bytes_cached(wav_bytes: bytes, *, beam_size: int = 5) -> dict[str, any]:
        """
        Transcribe audio bytes using cached Whisper model.
        
        Args:
            wav_bytes: Audio data in WAV format
            beam_size: Beam search size for transcription accuracy
            
        Returns:
            Dict containing 'text' and 'language' keys
        """
        # Save to temp file for faster-whisper
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(wav_bytes)
            tmp_path = tmp.name
        
        segments, info = model.transcribe(tmp_path, beam_size=beam_size)
        text = " ".join(seg.text for seg in segments).strip()
        
        return {"text": text, "language": info.language}
    
    # Audio input component
    audio = st.audio_input("Record audio", sample_rate=48000)
    success_msg = st.empty()
    
    # Auto-transcribe logic
    if audio:
        wav_bytes = audio.getvalue()
        audio_hash = sha1_bytes(wav_bytes)
        
        # Only transcribe if this is new audio
        if audio_hash != st.session_state.last_audio_hash:
            success_msg.success("Audio captured.")
            
            with st.spinner("Transcribing…"):
                try:
                    result = transcribe_bytes_cached(wav_bytes)
                    st.session_state.last_audio_hash = audio_hash
                    transcript = result["text"]
                    
                    # Add to chat history
                    add_user_message(transcript, audio_bytes=wav_bytes)
                    
                    success_msg.empty()  # Clear success message
                    st.rerun()  # Refresh to show the new message immediately
                    
                except Exception as e:
                    st.error(f"Transcription failed: {e}")

# ###########################
# # Optional: text chat box #
# ###########################
# user_text = st.chat_input("Type a message (optional)…")
# if user_text:
#     add_user_message(user_text)
#     st.rerun()

# st.caption("Local transcription with faster-whisper. The model loads once, and transcription starts automatically when recording stops.")
