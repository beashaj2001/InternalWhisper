import os
import logging
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger("InternalWhisper.Transcriber")

class TranscriptionWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    status = pyqtSignal(str)   # Progress updates for HUD ("Downloading model...", etc.)

    def __init__(self, audio_path, config_manager):
        super().__init__()
        self.audio_path = audio_path
        self.config = config_manager

    def run(self):
        try:
            if not self.audio_path or not os.path.exists(self.audio_path):
                self.error.emit("Audio file not found or empty.")
                return

            backend = self.config.get("backend", "local").lower()
            logger.info(f"[Transcriber] Starting transcription with backend: '{backend}'")

            text = ""
            if backend == "openai":
                text = self._transcribe_openai()
            elif backend == "groq":
                text = self._transcribe_groq()
            else:
                text = self._transcribe_local()

            if text and text.strip():
                logger.info(f"[Transcriber] Final text: '{text[:80]}'")
                self.finished.emit(text.strip())
            else:
                self.error.emit("No speech detected. Please speak clearly and try again.")

        except Exception as e:
            logger.error(f"[Transcriber] Error: {e}", exc_info=True)
            self.error.emit(str(e)[:120])

        finally:
            try:
                if self.audio_path and os.path.exists(self.audio_path):
                    os.remove(self.audio_path)
            except Exception:
                pass

    def _transcribe_local(self):
        model_size = self.config.get("local_model", "tiny")

        # --- Primary: faster-whisper ---
        try:
            from faster_whisper import WhisperModel
            logger.info(f"[Local STT] Loading faster-whisper model '{model_size}'...")
            self.status.emit("Loading model...")

            model = WhisperModel(model_size, device="cpu", compute_type="int8")
            logger.info(f"[Local STT] Model loaded. Transcribing audio...")
            self.status.emit("Transcribing...")

            segments, info = model.transcribe(
                self.audio_path,
                beam_size=5,
                language="en",
                vad_filter=True,       # Skip silence automatically
                vad_parameters=dict(min_silence_duration_ms=300)
            )
            text = " ".join(seg.text for seg in segments).strip()
            logger.info(f"[Local STT] faster-whisper done. Detected language: {info.language} ({info.language_probability:.0%})")
            return text

        except ImportError:
            logger.warning("[Local STT] faster-whisper not installed, trying HuggingFace transformers...")

        # --- Fallback: HuggingFace transformers ---
        try:
            from transformers import pipeline
            import torch
            hf_model = f"openai/whisper-{model_size}"
            logger.info(f"[Local STT] Loading HuggingFace Whisper '{hf_model}'...")
            self.status.emit("Loading model (HuggingFace)...")
            pipe = pipeline("automatic-speech-recognition", model=hf_model, device="cpu", torch_dtype=torch.float32)
            self.status.emit("Transcribing...")
            result = pipe(self.audio_path)
            text = result.get("text", "").strip()
            logger.info(f"[Local STT] HuggingFace Whisper done: '{text[:60]}'")
            return text

        except Exception as e:
            raise RuntimeError(f"Local Whisper failed: {e}. Run: pip install faster-whisper")

    def _transcribe_openai(self):
        from openai import OpenAI
        api_key = self.config.get("openai_api_key", "").strip() or os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("OpenAI API Key missing. Go to Settings or switch to 'Local (Free)' backend.")
        model = self.config.get("openai_model", "whisper-1")
        client = OpenAI(api_key=api_key)
        with open(self.audio_path, "rb") as f:
            transcript = client.audio.transcriptions.create(model=model, file=f, response_format="text")
        return transcript if isinstance(transcript, str) else transcript.text

    def _transcribe_groq(self):
        from openai import OpenAI
        api_key = self.config.get("groq_api_key", "").strip() or os.environ.get("GROQ_API_KEY", "")
        if not api_key:
            raise ValueError("Groq API Key missing. Go to Settings or switch to 'Local (Free)' backend.")
        model = self.config.get("groq_model", "whisper-large-v3-turbo")
        client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
        with open(self.audio_path, "rb") as f:
            transcript = client.audio.transcriptions.create(model=model, file=f, response_format="text")
        return transcript if isinstance(transcript, str) else transcript.text


class Transcriber:
    def __init__(self, config_manager):
        self.config = config_manager
        self.current_worker = None

    def transcribe_async(self, audio_path, on_finished, on_error, on_status=None):
        self.current_worker = TranscriptionWorker(audio_path, self.config)
        self.current_worker.finished.connect(on_finished)
        self.current_worker.error.connect(on_error)
        if on_status:
            self.current_worker.status.connect(on_status)
        self.current_worker.start()
