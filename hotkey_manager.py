import time
import logging
from pynput import keyboard
from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger("InternalWhisper.HotkeyManager")

class HotkeySignals(QObject):
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()
    hotkey_triggered = pyqtSignal()

class HotkeyManager:
    def __init__(self, config_manager):
        self.config = config_manager
        self.signals = HotkeySignals()
        self.listener = None
        self.current_keys = set()
        self.target_keys = set()
        self.is_pressed = False
        self.is_recording = False
        self.last_toggle_time = 0
        self.parse_hotkey(self.config.get("hotkey", "ctrl+alt"))

    def parse_hotkey(self, hotkey_str):
        """Converts user hotkey string like 'ctrl+fn' or 'f8' into a set of canonical keys."""
        parts = [p.strip().lower() for p in hotkey_str.split('+')]
        keys = set()
        for p in parts:
            if p in ('ctrl', 'cntrl', 'control', 'lctrl', 'rctrl'):
                keys.add('ctrl')
            elif p in ('alt', 'lalt', 'ralt'):
                keys.add('alt')
            elif p in ('shift', 'lshift', 'rshift'):
                keys.add('shift')
            elif p in ('cmd', 'win', 'super'):
                keys.add('cmd')
            elif p in ('fn', 'function', 'fn_key'):
                keys.add('fn')
            else:
                keys.add(p)
        self.target_keys = keys
        logger.info(f"Parsed target hotkey: {self.target_keys}")

    def _normalize_key(self, key):
        """Helper to get standardized string representation of pynput key"""
        try:
            # Check pynput special keys
            if isinstance(key, keyboard.Key):
                name = key.name.lower()
                if 'ctrl' in name or 'control' in name:
                    return 'ctrl'
                if 'alt' in name:
                    return 'alt'
                if 'shift' in name:
                    return 'shift'
                if 'cmd' in name or 'win' in name:
                    return 'cmd'
                if 'fn' in name or 'function' in name:
                    return 'fn'
                return name
            elif isinstance(key, keyboard.KeyCode):
                if key.char:
                    char_lower = key.char.lower()
                    return char_lower
                if key.vk:
                    # Windows virtual key codes: Fn key often maps to 255 (0xFF) or 254
                    if key.vk in (255, 0xFF, 254, 0xFE):
                        return 'fn'
                    return f"vk_{key.vk}"
        except Exception:
            pass
            
        k_str = str(key).lower()
        if 'fn' in k_str or '255' in k_str:
            return 'fn'
        return k_str

    def _on_press(self, key):
        k_str = self._normalize_key(key)
        self.current_keys.add(k_str)
        logger.debug(f"Key down: '{k_str}'  |  held={self.current_keys}  |  target={self.target_keys}")

        # Check if target key combination is subset of currently pressed keys
        if self.target_keys and self.target_keys.issubset(self.current_keys):
            if not self.is_pressed:
                self.is_pressed = True
                mode = self.config.get("mode", "push_to_talk")
                
                if mode == "push_to_talk":
                    if not self.is_recording:
                        self.is_recording = True
                        logger.info("Hotkey pressed down -> Starting recording (Push-to-Talk)")
                        self.signals.recording_started.emit()
                elif mode == "toggle":
                    # Debounce toggle presses
                    now = time.time()
                    if now - self.last_toggle_time > 0.3:
                        self.last_toggle_time = now
                        if not self.is_recording:
                            self.is_recording = True
                            logger.info("Hotkey toggled -> Starting recording")
                            self.signals.recording_started.emit()
                        else:
                            self.is_recording = False
                            logger.info("Hotkey toggled -> Stopping recording")
                            self.signals.recording_stopped.emit()

    def _on_release(self, key):
        k_str = self._normalize_key(key)
        if k_str in self.current_keys:
            self.current_keys.remove(k_str)
            
        # If any target key is released in push-to-talk mode
        if self.is_pressed:
            if not self.target_keys.issubset(self.current_keys):
                self.is_pressed = False
                mode = self.config.get("mode", "push_to_talk")
                if mode == "push_to_talk" and self.is_recording:
                    self.is_recording = False
                    logger.info("Hotkey released -> Stopping recording (Push-to-Talk)")
                    self.signals.recording_stopped.emit()

    def start(self):
        if self.listener is None:
            self.listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self.listener.daemon = True
            self.listener.start()
            logger.info("Global hotkey listener started.")

    def stop(self):
        if self.listener:
            self.listener.stop()
            self.listener = None
            logger.info("Global hotkey listener stopped.")

    def update_hotkey(self, hotkey_str):
        self.parse_hotkey(hotkey_str)
