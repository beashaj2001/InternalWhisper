import sys
import random
from PyQt6.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QFont, QPainterPath

class AudioWaveformWidget(QWidget):
    """Custom 5-bar animated audio VU wave visualizer"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(45, 24)
        self.volume_level = 0.0 # 0.0 to 1.0
        self.bar_heights = [4, 4, 4, 4, 4]
        
        # Smooth animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate_bars)
        self.timer.start(50)

    def set_volume(self, volume):
        self.volume_level = max(0.0, min(1.0, volume))

    def _animate_bars(self):
        try:
            if self.volume_level > 0.05:
                # Generate dynamic bar heights based on volume level + slight random variation
                max_h = 20
                base_h = int(self.volume_level * max_h)
                self.bar_heights = [
                    max(3, min(max_h, base_h + random.randint(-3, 3))),
                    max(3, min(max_h, int(base_h * 1.3) + random.randint(-2, 4))),
                    max(3, min(max_h, int(base_h * 1.5) + random.randint(-3, 5))),
                    max(3, min(max_h, int(base_h * 1.2) + random.randint(-2, 4))),
                    max(3, min(max_h, base_h + random.randint(-4, 2))),
                ]
            else:
                self.bar_heights = [3, 4, 3, 4, 3]
            self.update()
        except Exception:
            pass  # Silently ignore timer tick errors (e.g. during shutdown)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        bar_width = 4
        spacing = 4
        start_x = 3
        center_y = self.height() // 2

        for i, h in enumerate(self.bar_heights):
            x = start_x + i * (bar_width + spacing)
            y = center_y - (h // 2)
            
            # Gradient colors from bright cyan to neon magenta
            color = QColor(0, 230, 255) if i % 2 == 0 else QColor(255, 0, 150)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(x, y, bar_width, h, 2, 2)

class FloatingHUD(QWidget):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.drag_position = QPoint()
        self._init_ui()

    def _init_ui(self):
        # Frameless, Always on Top, Tool Window (no taskbar entry, non-focus stealing)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(220, 50)

        # Main background container frame
        self.container = QFrame(self)
        self.container.setObjectName("hudContainer")
        self.container.setStyleSheet("""
            QFrame#hudContainer {
                background-color: rgba(18, 20, 28, 0.92);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 22px;
            }
        """)

        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(10)

        # Status Dot / Icon Indicator
        self.status_dot = QLabel(self)
        self.status_dot.setFixedSize(12, 12)
        self.set_dot_color("#ff4757") # Red for recording

        # Waveform Visualizer
        self.waveform = AudioWaveformWidget(self)

        # Text Label
        self.text_label = QLabel("Listening...", self)
        self.text_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.text_label.setStyleSheet("color: #f1f2f6;")

        layout.addWidget(self.status_dot)
        layout.addWidget(self.waveform)
        layout.addWidget(self.text_label, 1)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)

        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide)

        # Position at top-center of screen
        self.center_top()

    def set_dot_color(self, hex_color):
        self.status_dot.setStyleSheet(f"""
            background-color: {hex_color};
            border-radius: 6px;
        """)

    def center_top(self):
        screen = self.screen().geometry() if self.screen() else None
        if screen:
            x = (screen.width() - self.width()) // 2
            y = 50
            self.move(x, y)

    def set_state_recording(self):
        self.hide_timer.stop()
        self.set_dot_color("#ff4757") # Bright Red
        self.text_label.setText("Listening...")
        self.text_label.setStyleSheet("color: #ff6b81; font-weight: bold;")
        self.waveform.show()
        self.show()

    def update_volume(self, volume):
        self.waveform.set_volume(volume)

    def set_state_transcribing(self):
        self.hide_timer.stop()
        self.set_dot_color("#eccc68") # Amber Gold
        self.text_label.setText("Transcribing...")
        self.text_label.setStyleSheet("color: #eccc68; font-weight: bold;")
        self.waveform.hide()
        self.show()

    def set_state_transcribing_msg(self, msg):
        """Update HUD text with dynamic progress message from transcription worker."""
        self.hide_timer.stop()
        self.set_dot_color("#eccc68")
        self.text_label.setText(msg)
        self.text_label.setStyleSheet("color: #eccc68; font-weight: bold;")
        self.waveform.hide()
        self.show()

    def set_state_success(self, msg="Pasted! ✓"):
        self.set_dot_color("#2ed573") # Neon Emerald Green
        self.text_label.setText(msg)
        self.text_label.setStyleSheet("color: #2ed573; font-weight: bold;")
        self.waveform.hide()
        self.show()
        self.hide_timer.start(1800) # Hide after 1.8 seconds

    def set_state_error(self, err_msg="Error"):
        self.set_dot_color("#ff4757")
        self.text_label.setText(f"Failed: {err_msg[:15]}..")
        self.text_label.setStyleSheet("color: #ff4757; font-weight: bold;")
        self.waveform.hide()
        self.show()
        self.hide_timer.start(3000)

    # Mouse drag window repositioning
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self.drag_position.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
