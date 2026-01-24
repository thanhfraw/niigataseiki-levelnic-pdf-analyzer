# Copyright © 2026 Nhat Viet Industrial Co., Ltd.
# All rights reserved.
#
# This software is proprietary and confidential.
# Unauthorized copying, modification, or distribution is strictly prohibited.

# app/ui/status_widget.py
"""
Module: Status Widget
Task: Display application status and progress
Description: Custom widget for displaying status messages with blinking effects and progress bar

Tác vụ: Hiển thị trạng thái và tiến trình ứng dụng
Mô tả: Widget tùy chỉnh hiển thị thông điệp trạng thái với hiệu ứng nhấp nháy và thanh tiến trình
"""

from __future__ import annotations
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QProgressBar, QMessageBox
from PySide6.QtCore import Qt, QTimer

class StatusWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.status_label = QLabel("READY!!!")
        self.status_label.setStyleSheet("color:#00ff00; font-size:30px; font-weight:bold;")
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(120)
        self.progress_bar.setMaximumHeight(20)
        self.progress_bar.setVisible(False)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 12, 0)  # left, top, right, bottom
        layout.setSpacing(10)
        layout.addWidget(self.status_label, 1)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)
        
        # Blinking animation for READY status and error messages
        self._blink_visible = True
        self._blink_mode = "ready"  # "ready" or "error"
        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._toggle_blink)
        self._start_ready_blink()

    def start_blue_blink(self, text: str | None = None):
        """Public helper: set optional text then blink blue."""
        if text:
            self.status_label.setText(text.upper())
        self._start_blue_blink()

    def start_red_blink(self, text: str | None = None):
        """Public helper: set optional text then blink red."""
        if text:
            self.status_label.setText(text.upper())
        self._start_error_blink()

    def start_green_blink(self, text: str | None = None):
        """Public helper: set optional text then blink green."""
        if text:
            self.status_label.setText(text.upper())
        self._start_green_blink()

    def set_status(self, text: str):
        display_text = text.upper()
        self.status_label.setText(display_text)
        # Check for error/warning messages
        error_keywords = ["no data", "error", "failed", "missing", "not found", "invalid"]
        is_error = any(keyword in text.lower() for keyword in error_keywords)
        
        if "READY" in text.upper():
            # Restart blinking for READY status
            self._start_ready_blink()
        elif is_error:
            # Start red blinking for error messages
            self._start_error_blink()
        else:
            # Normal status (no blink)
            self._stop_blink()
            self.status_label.setStyleSheet("color:#ffffff; font-size:15px;")

    def set_progress(self, value: int, visible: bool = True):
        self.progress_bar.setVisible(visible)
        if visible:
            self.progress_bar.setValue(value)

    def set_message_box(self, title: str, text: str):
        QMessageBox.information(self, title, text)
    
    def _start_ready_blink(self):
        """Start blinking animation for READY status"""
        self._blink_mode = "ready"
        self._blink_visible = True
        self._blink_timer.start(300)  # Blink every 300ms
    
    def _start_error_blink(self):
        """Start blinking animation for error messages"""
        self._blink_mode = "error"
        self._blink_visible = True
        self._blink_timer.start(300)  # Blink every 300ms

    def _start_blue_blink(self):
        """Start blinking animation for info/processing messages"""
        self._blink_mode = "blue"
        self._blink_visible = True
        self._blink_timer.start(300)  # Blink every 300ms

    def _start_green_blink(self):
        """Start blinking animation for success messages"""
        self._blink_mode = "green"
        self._blink_visible = True
        self._blink_timer.start(300)  # Blink every 300ms
    
    def _stop_blink(self):
        """Stop blinking animation"""
        self._blink_timer.stop()
        self._blink_visible = True
        self.status_label.setVisible(True)
    
    def _toggle_blink(self):
        """Toggle visibility for blinking effect"""
        self._blink_visible = not self._blink_visible
        if self._blink_mode == "ready":
            if self._blink_visible:
                self.status_label.setStyleSheet("color:#00ff00; font-size:15px; font-weight:bold;")
            else:
                self.status_label.setStyleSheet("color:#004400; font-size:15px; font-weight:bold;")
        elif self._blink_mode == "error":
            if self._blink_visible:
                self.status_label.setStyleSheet("color:#ff0000; font-size:15px; font-weight:bold;")
            else:
                self.status_label.setStyleSheet("color:#ffffff; font-size:15px; font-weight:bold;")
        elif self._blink_mode == "blue":
            if self._blink_visible:
                self.status_label.setStyleSheet("color:#0080ff; font-size:15px; font-weight:bold;")
            else:
                self.status_label.setStyleSheet("color:#003366; font-size:15px; font-weight:bold;")
        elif self._blink_mode == "green":
            if self._blink_visible:
                self.status_label.setStyleSheet("color:#00ff00; font-size:15px; font-weight:bold;")
            else:
                self.status_label.setStyleSheet("color:#004400; font-size:15px; font-weight:bold;")
