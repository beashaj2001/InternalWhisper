import sys
import os
import time
import signal
import winsound
import logging
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QBrush

from config import config
from audio_recorder import AudioRecorder
from hotkey_manager import HotkeyManager
from transcriber import Transcriber
from formatter import TextFormatter
from paster import TextPaster
from ui.floating_hud import FloatingHUD
from ui.settings_window import SettingsWindow

# Configure Logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("InternalWhisper.Main")

def create_tray_icon():
    """Generates a sleek 32x32 microphone icon programmatically for the system tray"""
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Outer dark circle background
    painter.setBrush(QBrush(QColor(18, 20, 28)))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(2, 2, 28, 28)
    
    # Inner cyan mic icon shape
    painter.setBrush(QBrush(QColor(0, 230, 255)))
    painter.drawRoundedRect(12, 7, 8, 12, 4, 4)
    
    # Mic stand arc
    painter.setPen(QColor(0, 230, 255))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawArc(9, 12, 14, 11, 0, -180 * 16)
    painter.drawLine(16, 23, 16, 26)
    painter.end()
    
    return QIcon(pixmap)

class InternalWhisperApp(QObject):
    def __init__(self, qapp):
        super().__init__()
        self.app = qapp
        self.config = config
        self.history_log = []

        # Core Services
        self.recorder = AudioRecorder()
        self.transcriber = Transcriber(self.config)
        self.formatter = TextFormatter(self.config)
        self.paster = TextPaster(self.config)
        self.hotkey_mgr = HotkeyManager(self.config)

        # UI Components
        self.hud = FloatingHUD(self.config)
        self.settings_win = None

        # VU Volume update timer for HUD
        self.vu_timer = QTimer(self)
        self.vu_timer.timeout.connect(self._update_hud_volume)

        # Wire up hotkey signals
        self.hotkey_mgr.signals.recording_started.connect(self._on_recording_started)
        self.hotkey_mgr.signals.recording_stopped.connect(self._on_recording_stopped)

        # System Tray Icon setup
        self._setup_tray()

        # Start hotkey listener
        self.hotkey_mgr.start()
        logger.info("InternalWhisper application initialized and running.")

    def _setup_tray(self):
        self.tray_icon = QSystemTrayIcon(create_tray_icon(), self.app)
        self.tray_icon.setToolTip("InternalWhisper - Voice-to-Text Dictation (Ctrl+Alt)")

        tray_menu = QMenu()
        
        title_action = tray_menu.addAction("🎙️ InternalWhisper v1.0")
        title_action.setEnabled(False)
        tray_menu.addSeparator()

        settings_action = tray_menu.addAction("⚙️ Settings & History")
        settings_action.triggered.connect(self.show_settings)

        self.pause_action = tray_menu.addAction("⏸️ Pause Hotkeys")
        self.pause_action.setCheckable(True)
        self.pause_action.triggered.connect(self._toggle_pause)

        tray_menu.addSeparator()
        exit_action = tray_menu.addAction("❌ Exit")
        exit_action.triggered.connect(self.quit_app)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_settings()

    def _toggle_pause(self, checked):
        if checked:
            self.hotkey_mgr.stop()
            self.tray_icon.setToolTip("InternalWhisper - PAUSED")
            logger.info("InternalWhisper paused.")
        else:
            self.hotkey_mgr.start()
            self.tray_icon.setToolTip("InternalWhisper - Active")
            logger.info("InternalWhisper resumed.")

    def _play_sound_chime(self, freq=800, dur=60):
        if self.config.get("play_sounds", True):
            try:
                winsound.Beep(freq, dur)
            except Exception:
                pass

    def _on_recording_started(self):
        if self.recorder.is_recording:
            return

        try:
            target_device = self.config.get("audio_device", None)
            self.recorder.start_recording(device_index=target_device)
            self._play_sound_chime(900, 50)
            self.hud.set_state_recording()
            self.vu_timer.start(40) # Update VU meter every 40ms
            logger.info("Started recording audio.")
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self.hud.set_state_error("Mic Access Error")

    def _update_hud_volume(self):
        if self.recorder.is_recording:
            vol = self.recorder.get_volume_level()
            self.hud.update_volume(vol)

    def _on_recording_stopped(self):
        if not self.recorder.is_recording:
            return

        self.vu_timer.stop()
        self._play_sound_chime(600, 50)
        
        audio_file = self.recorder.stop_recording()
        if not audio_file:
            self.hud.set_state_error("No Audio")
            return

        self.hud.set_state_transcribing()
        logger.info("Sending audio file for transcription...")

        self.transcriber.transcribe_async(
            audio_path=audio_file,
            on_finished=self._on_transcription_finished,
            on_error=self._on_transcription_error,
            on_status=self.hud.set_state_transcribing_msg
        )

    def _on_transcription_finished(self, raw_text):
        logger.info(f"Raw transcript received: '{raw_text}'")
        
        # Apply formatting (filler removal, punctuation, optional AI prompt)
        final_text = self.formatter.format_text(raw_text)
        logger.info(f"Final formatted text: '{final_text}'")

        # Auto-paste text into active cursor position
        success = self.paster.paste(final_text)

        # Save to history log
        now_str = datetime.now().strftime("%H:%M:%S")
        self.history_log.append({
            "timestamp": now_str,
            "text": final_text
        })
        if len(self.history_log) > self.config.get("history_max_items", 100):
            self.history_log.pop(0)

        # Notify user via HUD
        if success:
            self.hud.set_state_success("Pasted! ✓")
            self._play_sound_chime(1200, 70)
        else:
            self.hud.set_state_error("Paste Failed")

        if self.settings_win:
            self.settings_win.refresh_history()

    def _on_transcription_error(self, err_msg):
        logger.error(f"Transcription failure: {err_msg}")
        self.hud.set_state_error(err_msg)
        self._play_sound_chime(400, 150)

    def show_settings(self):
        if self.settings_win is None:
            self.settings_win = SettingsWindow(self.config, self.history_log)
        else:
            self.settings_win.refresh_history()
            
        self.settings_win.show()
        self.settings_win.raise_()
        self.settings_win.activateWindow()

    def quit_app(self):
        logger.info("Quitting InternalWhisper...")
        self.hotkey_mgr.stop()
        if self.recorder.is_recording:
            self.recorder.stop_recording()
        self.tray_icon.hide()
        self.app.quit()

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep app running in system tray

    whisper_app = InternalWhisperApp(app)

    # Allow graceful Ctrl+C shutdown from terminal
    def handle_sigint(*args):
        logger.info("Received interrupt signal, shutting down...")
        whisper_app.quit_app()

    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)

    # Python signal polling timer (Qt doesn't poll signals by default)
    sig_timer = QTimer()
    sig_timer.start(200)
    sig_timer.timeout.connect(lambda: None)  # Wakes event loop to process signals

    print()
    print("  ==============================================")
    print("   [MIC] InternalWhisper is running in the tray!")
    print("  ==============================================")
    print(f"   Hotkey: {whisper_app.config.get('hotkey', 'ctrl+fn').upper()}")
    print("   Look for the mic icon in your system tray")
    print("   (bottom-right of your Windows taskbar)")
    print("   Right-click the tray icon -> Settings to configure")
    print("  ==============================================")
    print()

    try:
        sys.exit(app.exec())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Application closed.")
        whisper_app.quit_app()

if __name__ == "__main__":
    main()
