import time
import logging
import pyperclip
from pynput.keyboard import Controller, Key

logger = logging.getLogger("InternalWhisper.Paster")

class TextPaster:
    def __init__(self, config_manager):
        self.config = config_manager
        self.keyboard = Controller()

    def paste(self, text):
        if not text:
            return False

        auto_paste = self.config.get("auto_paste", True)
        restore_clip = self.config.get("restore_clipboard", True)
        delay_ms = self.config.get("paste_delay_ms", 100)

        # Copy text to clipboard regardless
        previous_clipboard = ""
        if restore_clip:
            try:
                previous_clipboard = pyperclip.paste()
            except Exception as e:
                logger.warning(f"Could not read previous clipboard: {e}")

        try:
            pyperclip.copy(text)
            logger.info(f"Copied text to clipboard: '{text[:30]}...'")

            if auto_paste:
                # Small pause before pasting to ensure clipboard update is registered by Windows
                time.sleep(0.05)
                
                # Simulate Ctrl + V
                with self.keyboard.pressed(Key.ctrl):
                    self.keyboard.press('v')
                    self.keyboard.release('v')

                logger.info("Executed Ctrl+V paste key sequence.")

                # Wait for target app to consume clipboard before restoring
                if restore_clip and previous_clipboard:
                    time.sleep(delay_ms / 1000.0)
                    pyperclip.copy(previous_clipboard)
                    logger.info("Restored original clipboard contents.")

            return True
        except Exception as e:
            logger.error(f"Error during auto-paste: {e}")
            return False
