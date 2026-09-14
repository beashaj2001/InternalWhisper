import sys
import os
import pyperclip
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, QRadioButton, 
    QTextEdit, QSlider, QListWidget, QListWidgetItem, QGroupBox, QMessageBox,
    QProgressBar, QButtonGroup, QFrame
)
from PyQt6.QtGui import QIcon, QFont, QColor
from audio_recorder import AudioRecorder

DARK_STYLESHEET = """
QMainWindow {
    background-color: #12141C;
}
QWidget {
    background-color: #12141C;
    color: #E1E2E6;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}
QTabWidget::pane {
    border: 1px solid #2A2E3D;
    background-color: #181B26;
    border-radius: 8px;
    top: -1px;
}
QTabBar::tab {
    background: #12141C;
    color: #8C92A4;
    padding: 10px 18px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: bold;
}
QTabBar::tab:selected {
    background: #181B26;
    color: #00E6FF;
    border-bottom: 2px solid #00E6FF;
}
QGroupBox {
    border: 1px solid #2A2E3D;
    border-radius: 8px;
    margin-top: 12px;
    font-weight: bold;
    color: #00E6FF;
    padding: 14px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
QLineEdit, QComboBox, QTextEdit {
    background-color: #202433;
    border: 1px solid #32384D;
    border-radius: 6px;
    padding: 8px;
    color: #FFFFFF;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
    border: 1px solid #00E6FF;
}
QPushButton {
    background-color: #00E6FF;
    color: #0D1117;
    font-weight: bold;
    border-radius: 6px;
    padding: 8px 16px;
    border: none;
}
QPushButton:hover {
    background-color: #33EBFF;
}
QPushButton#secondaryBtn {
    background-color: #202433;
    color: #E1E2E6;
    border: 1px solid #32384D;
}
QPushButton#secondaryBtn:hover {
    background-color: #2C3247;
    border-color: #00E6FF;
}
QCheckBox, QRadioButton {
    spacing: 8px;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
}
QSlider::groove:horizontal {
    height: 6px;
    background: #202433;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #00E6FF;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QListWidget {
    background-color: #181B26;
    border: 1px solid #2A2E3D;
    border-radius: 6px;
}
QListWidget::item {
    padding: 10px;
    border-bottom: 1px solid #202433;
}
QListWidget::item:hover {
    background-color: #202433;
}
"""

class SettingsWindow(QMainWindow):
    def __init__(self, config_manager, history_log=None, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.history_log = history_log or []
        self.test_recorder = None
        self.test_timer = None
        self.setWindowTitle("InternalWhisper - Settings & History")
        self.resize(620, 520)
        self.setStyleSheet(DARK_STYLESHEET)
        self._init_ui()

    def _init_ui(self):
        central_widget = QWidget(self)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Header Title
        header_layout = QHBoxLayout()
        title_label = QLabel("🎙️ InternalWhisper Control Center")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #FFFFFF;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Tabs
        self.tabs = QTabWidget(self)
        
        self.tab_general = QWidget()
        self.tab_api = QWidget()
        self.tab_audio = QWidget()
        self.tab_history = QWidget()

        self._setup_general_tab()
        self._setup_api_tab()
        self._setup_audio_tab()
        self._setup_history_tab()

        self.tabs.addTab(self.tab_general, "⚙️ General")
        self.tabs.addTab(self.tab_api, "🔑 AI & STT Engine")
        self.tabs.addTab(self.tab_audio, "🎤 Audio Input")
        self.tabs.addTab(self.tab_history, "📜 Dictation History")

        main_layout.addWidget(self.tabs)

        # Bottom Action Bar
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        
        save_btn = QPushButton("Save Settings", self)
        save_btn.clicked.connect(self._save_settings)
        
        close_btn = QPushButton("Close", self)
        close_btn.setObjectName("secondaryBtn")
        close_btn.clicked.connect(self.close)

        bottom_layout.addWidget(close_btn)
        bottom_layout.addWidget(save_btn)
        main_layout.addLayout(bottom_layout)

        self.setCentralWidget(central_widget)

    def _setup_general_tab(self):
        layout = QVBoxLayout(self.tab_general)
        layout.setSpacing(14)

        # Hotkey Group
        hotkey_group = QGroupBox("Global Hotkey & Activation Mode")
        hk_layout = QVBoxLayout(hotkey_group)

        hk_row = QHBoxLayout()
        hk_row.addWidget(QLabel("Shortcut Key Combination:"))
        self.hotkey_input = QLineEdit(self.config.get("hotkey", "ctrl+fn"))
        self.hotkey_input.setPlaceholderText("e.g. ctrl+fn, ctrl+alt, f8, ctrl+shift, alt+space")
        hk_row.addWidget(self.hotkey_input)
        hk_layout.addLayout(hk_row)

        hk_help = QLabel("Preset options: ctrl+fn  |  ctrl+alt  |  ctrl+shift  |  f8  |  alt+space")
        hk_help.setStyleSheet("color: #8C92A4; font-size: 11px;")
        hk_layout.addWidget(hk_help)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Recording Trigger Mode:"))
        self.ptt_radio = QRadioButton("Push-to-Talk (Hold hotkey to record, release to paste)")
        self.toggle_radio = QRadioButton("Toggle (Press once to record, press again to stop)")
        
        if self.config.get("mode", "push_to_talk") == "push_to_talk":
            self.ptt_radio.setChecked(True)
        else:
            self.toggle_radio.setChecked(True)

        mode_layout = QVBoxLayout()
        mode_layout.addWidget(self.ptt_radio)
        mode_layout.addWidget(self.toggle_radio)
        mode_row.addLayout(mode_layout)
        hk_layout.addLayout(mode_row)

        layout.addWidget(hotkey_group)

        # Automation Options Group
        auto_group = QGroupBox("Auto-Paste & Clipboard Behavior")
        auto_layout = QVBoxLayout(auto_group)

        self.auto_paste_cb = QCheckBox("Automatically paste transcribed text at current cursor position (Ctrl+V)")
        self.auto_paste_cb.setChecked(self.config.get("auto_paste", True))
        auto_layout.addWidget(self.auto_paste_cb)

        self.restore_clip_cb = QCheckBox("Restore previous clipboard content after auto-pasting")
        self.restore_clip_cb.setChecked(self.config.get("restore_clipboard", True))
        auto_layout.addWidget(self.restore_clip_cb)

        delay_row = QHBoxLayout()
        delay_row.addWidget(QLabel("Paste Delay (ms):"))
        self.delay_slider = QSlider(Qt.Orientation.Horizontal)
        self.delay_slider.setRange(20, 500)
        self.delay_slider.setValue(self.config.get("paste_delay_ms", 100))
        self.delay_label = QLabel(f"{self.delay_slider.value()} ms")
        self.delay_slider.valueChanged.connect(lambda v: self.delay_label.setText(f"{v} ms"))
        delay_row.addWidget(self.delay_slider)
        delay_row.addWidget(self.delay_label)
        auto_layout.addLayout(delay_row)

        layout.addWidget(auto_group)
        layout.addStretch()

    def _setup_api_tab(self):
        layout = QVBoxLayout(self.tab_api)

        stt_group = QGroupBox("Speech-to-Text Provider")
        stt_layout = QVBoxLayout(stt_group)

        prov_row = QHBoxLayout()
        prov_row.addWidget(QLabel("STT Backend Engine:"))
        self.backend_combo = QComboBox()
        self.backend_combo.addItems([
            "Local Whisper (FREE - No API Key, Works Offline)",
            "OpenAI Whisper API (Paid - Fastest & Most Accurate)",
            "Groq Whisper API (Free Tier Available - Ultra Fast)",
        ])

        current_backend = self.config.get("backend", "local")
        if current_backend == "openai":
            self.backend_combo.setCurrentIndex(1)
        elif current_backend == "groq":
            self.backend_combo.setCurrentIndex(2)
        else:
            self.backend_combo.setCurrentIndex(0)  # local = default free
            
        prov_row.addWidget(self.backend_combo)
        stt_layout.addLayout(prov_row)

        # OpenAI Key
        oai_row = QHBoxLayout()
        oai_row.addWidget(QLabel("OpenAI API Key:"))
        self.openai_key_input = QLineEdit(self.config.get("openai_api_key", ""))
        self.openai_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_key_input.setPlaceholderText("sk-...")
        oai_row.addWidget(self.openai_key_input)
        stt_layout.addLayout(oai_row)

        # Groq Key
        groq_row = QHBoxLayout()
        groq_row.addWidget(QLabel("Groq API Key:"))
        self.groq_key_input = QLineEdit(self.config.get("groq_api_key", ""))
        self.groq_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.groq_key_input.setPlaceholderText("gsk_...")
        groq_row.addWidget(self.groq_key_input)
        stt_layout.addLayout(groq_row)

        # Local model size selector
        local_model_row = QHBoxLayout()
        local_model_row.addWidget(QLabel("Local Model Size:"))
        self.local_model_combo = QComboBox()
        self.local_model_combo.addItems([
            "tiny   (~75 MB  - Fastest, good for short phrases)",
            "base   (~142 MB - Balanced speed & accuracy)",
            "small  (~461 MB - High accuracy, slower)",
            "medium (~1.4 GB - Best accuracy, much slower)",
        ])
        model_map = {"tiny": 0, "base": 1, "small": 2, "medium": 3}
        cur_model = self.config.get("local_model", "tiny")
        self.local_model_combo.setCurrentIndex(model_map.get(cur_model, 0))
        local_model_row.addWidget(self.local_model_combo)
        stt_layout.addLayout(local_model_row)

        free_note = QLabel("  The model downloads automatically on first use from HuggingFace (one-time).")
        free_note.setStyleSheet("color: #2ed573; font-size: 11px;")
        stt_layout.addWidget(free_note)

        layout.addWidget(stt_group)

        # AI Formatting Group
        fmt_group = QGroupBox("AI Post-Processing & Smart Formatting")
        fmt_layout = QVBoxLayout(fmt_group)

        self.ai_fmt_cb = QCheckBox("Enable AI formatting (cleans up grammar, removes filler words, formats output)")
        self.ai_fmt_cb.setChecked(self.config.get("ai_formatting", False))
        fmt_layout.addWidget(self.ai_fmt_cb)

        fmt_layout.addWidget(QLabel("Custom AI Prompt Directive:"))
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlainText(self.config.get(
            "custom_prompt", 
            "Clean up transcription, add proper punctuation and capitalization, remove filler words (um, uh, like), and output clean formatted text."
        ))
        self.prompt_edit.setMaximumHeight(80)
        fmt_layout.addWidget(self.prompt_edit)

        layout.addWidget(fmt_group)
        layout.addStretch()

    def _setup_audio_tab(self):
        layout = QVBoxLayout(self.tab_audio)

        dev_group = QGroupBox("Microphone Input Device")
        dev_layout = QVBoxLayout(dev_group)

        dev_row = QHBoxLayout()
        dev_row.addWidget(QLabel("Select Device:"))
        self.audio_combo = QComboBox()
        
        # Populate microphone devices
        self.devices = AudioRecorder.get_input_devices()
        current_dev = self.config.get("audio_device", None)
        default_idx = 0
        
        self.audio_combo.addItem("Default System Microphone", None)
        for idx, name in self.devices:
            self.audio_combo.addItem(f"{name} (Device {idx})", idx)
            if current_dev is not None and current_dev == idx:
                default_idx = self.audio_combo.count() - 1
                
        self.audio_combo.setCurrentIndex(default_idx)
        dev_row.addWidget(self.audio_combo)
        dev_layout.addLayout(dev_row)

        layout.addWidget(dev_group)

        # Test Mic Group
        test_group = QGroupBox("Microphone Audio Test & Volume Meter")
        test_layout = QVBoxLayout(test_group)

        self.meter_bar = QProgressBar()
        self.meter_bar.setRange(0, 100)
        self.meter_bar.setValue(0)
        self.meter_bar.setTextVisible(False)
        self.meter_bar.setStyleSheet("""
            QProgressBar {
                background-color: #202433;
                border: 1px solid #32384D;
                border-radius: 6px;
                height: 18px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00E6FF, stop:1 #FF0096);
                border-radius: 5px;
            }
        """)
        test_layout.addWidget(self.meter_bar)

        self.test_btn = QPushButton("Start Mic Test", self)
        self.test_btn.setObjectName("secondaryBtn")
        self.test_btn.clicked.connect(self._toggle_mic_test)
        test_layout.addWidget(self.test_btn)

        layout.addWidget(test_group)
        layout.addStretch()

    def _setup_history_tab(self):
        layout = QVBoxLayout(self.tab_history)

        header_row = QHBoxLayout()
        header_row.addWidget(QLabel("Recent Dictations:"))
        
        refresh_btn = QPushButton("Refresh List", self)
        refresh_btn.setObjectName("secondaryBtn")
        refresh_btn.clicked.connect(self.refresh_history)
        header_row.addWidget(refresh_btn)
        
        layout.addLayout(header_row)

        self.history_list = QListWidget(self)
        layout.addWidget(self.history_list)

        self.refresh_history()

    def refresh_history(self):
        self.history_list.clear()
        if not self.history_log:
            item = QListWidgetItem("No dictation history yet. Hold hotkey to speak!")
            self.history_list.addItem(item)
            return

        for entry in reversed(self.history_log[-50:]):
            timestamp = entry.get("timestamp", "")
            text = entry.get("text", "")
            item_str = f"[{timestamp}]  {text}"
            item = QListWidgetItem(item_str)
            self.history_list.addItem(item)

    def _toggle_mic_test(self):
        if self.test_recorder and self.test_recorder.is_recording:
            self.test_recorder.stop_recording()
            self.test_timer.stop()
            self.test_btn.setText("Start Mic Test")
            self.meter_bar.setValue(0)
        else:
            self.test_recorder = AudioRecorder()
            selected_dev = self.audio_combo.currentData()
            try:
                self.test_recorder.start_recording(device_index=selected_dev)
                self.test_btn.setText("Stop Mic Test")
                self.test_timer = QTimer(self)
                self.test_timer.timeout.connect(self._update_test_meter)
                self.test_timer.start(50)
            except Exception as e:
                QMessageBox.critical(self, "Mic Error", f"Could not access microphone: {e}")

    def _update_test_meter(self):
        if self.test_recorder:
            vol = self.test_recorder.get_volume_level()
            self.meter_bar.setValue(int(vol * 100))

    def _save_settings(self):
        # Hotkey
        hk = self.hotkey_input.text().strip()
        if hk:
            self.config.set("hotkey", hk)

        # Mode
        mode = "push_to_talk" if self.ptt_radio.isChecked() else "toggle"
        self.config.set("mode", mode)

        # Backend
        b_idx = self.backend_combo.currentIndex()
        backend = ["local", "openai", "groq"][b_idx]
        self.config.set("backend", backend)

        # Local model size
        local_model_names = ["tiny", "base", "small", "medium"]
        self.config.set("local_model", local_model_names[self.local_model_combo.currentIndex()])

        # Keys
        self.config.set("openai_api_key", self.openai_key_input.text().strip())
        self.config.set("groq_api_key", self.groq_key_input.text().strip())

        # Checkboxes
        self.config.set("auto_paste", self.auto_paste_cb.isChecked())
        self.config.set("restore_clipboard", self.restore_clip_cb.isChecked())
        self.config.set("paste_delay_ms", self.delay_slider.value())
        self.config.set("ai_formatting", self.ai_fmt_cb.isChecked())
        self.config.set("custom_prompt", self.prompt_edit.toPlainText().strip())

        # Audio device
        self.config.set("audio_device", self.audio_combo.currentData())

        QMessageBox.information(self, "Saved", "InternalWhisper settings saved successfully!")
        self.close()

    def closeEvent(self, event):
        if self.test_recorder and self.test_recorder.is_recording:
            self.test_recorder.stop_recording()
            if self.test_timer:
                self.test_timer.stop()
        event.accept()
