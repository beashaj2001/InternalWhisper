import re
import os
import logging
from openai import OpenAI

logger = logging.getLogger("InternalWhisper.Formatter")

FILLER_WORDS_REGEX = re.compile(r'\b(um+|uh+|er+|ah+)\b', re.IGNORECASE)

class TextFormatter:
    def __init__(self, config_manager):
        self.config = config_manager

    def format_text(self, raw_text):
        if not raw_text:
            return ""

        text = raw_text.strip()
        
        # Basic cleanup: remove filler words & fix whitespace
        text = FILLER_WORDS_REGEX.sub('', text)
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text).strip()

        # Check if AI Formatting is enabled
        if self.config.get("ai_formatting", False):
            ai_text = self._format_with_ai(text)
            if ai_text:
                return ai_text

        return text

    def _format_with_ai(self, text):
        backend = self.config.get("backend", "openai").lower()
        api_key = ""
        base_url = None
        model = "gpt-4o-mini"

        if backend == "groq":
            api_key = self.config.get("groq_api_key", "").strip() or os.environ.get("GROQ_API_KEY", "")
            base_url = "https://api.groq.com/openai/v1"
            model = "llama-3.3-70b-versatile"
        else:
            api_key = self.config.get("openai_api_key", "").strip() or os.environ.get("OPENAI_API_KEY", "")
            model = "gpt-4o-mini"

        if not api_key:
            logger.warning("AI Formatting enabled but no API key configured. Skipping AI formatting.")
            return text

        system_prompt = self.config.get(
            "custom_prompt", 
            "Clean up transcription, add proper punctuation and capitalization, remove filler words, and format cleanly."
        )

        try:
            client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": f"{system_prompt}\nReturn ONLY the revised text without meta-commentary or intro."},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            formatted = response.choices[0].message.content.strip()
            return formatted if formatted else text
        except Exception as e:
            logger.error(f"AI Formatting error: {e}")
            return text
