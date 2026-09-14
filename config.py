import os
import json
import logging

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(APP_DIR, "config.json")

DEFAULT_CONFIG = {
    "hotkey": "ctrl+alt",
    "mode": "push_to_talk",  # "push_to_talk" or "toggle"
    "backend": "local",      # "local" (FREE, offline), "openai", or "groq"
    "openai_api_key": "",
    "groq_api_key": "",
    "openai_model": "whisper-1",
    "groq_model": "whisper-large-v3-turbo",
    "local_model": "tiny",   # tiny (~75MB) | base (~142MB) | small (~461MB)
    "audio_device": None,    # None for default mic, or device index int
    "auto_paste": True,
    "play_sounds": True,
    "restore_clipboard": True,
    "paste_delay_ms": 100,
    "ai_formatting": False,
    "custom_prompt": "Clean up transcription, add proper punctuation and capitalization, remove filler words (um, uh, like), and output clean formatted text.",
    "hud_position": "top_center",
    "dark_mode": True,
    "history_max_items": 100
}

class ConfigManager:
    def __init__(self, filepath=CONFIG_FILE):
        self.filepath = filepath
        self.data = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
            except Exception as e:
                logging.error(f"Error loading config file: {e}")
        else:
            self.save()

    def save(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            logging.error(f"Error saving config file: {e}")

    def get(self, key, default=None):
        return self.data.get(key, default if default is not None else DEFAULT_CONFIG.get(key))

    def set(self, key, value):
        self.data[key] = value
        self.save()

    def update(self, kwargs):
        self.data.update(kwargs)
        self.save()

# Global config singleton instance
config = ConfigManager()
