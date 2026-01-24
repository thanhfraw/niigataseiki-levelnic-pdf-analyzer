# Copyright © 2026 Nhat Viet Industrial Co., Ltd.
# All rights reserved.
#
# This software is proprietary and confidential.
# Unauthorized copying, modification, or distribution is strictly prohibited.

# app/splash.py
"""
Module: Splash Screen
Task: Display animated splash screen on application startup
Description: Creates an animated glass-effect splash screen with blurred background and progress bar

Tác vụ: Màn hình splash khi khởi động
Mô tả: Tạo màn hình splash hiệu ứng glass với background blur và thanh tiến trình
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, QRect
from PySide6.QtGui import (
    QIcon,
    QPixmap,
    QPainter,
    QColor,
)
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
    QGraphicsDropShadowEffect,
    QGraphicsBlurEffect,
)


class SplashScreen(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(
            Qt.Dialog
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
        )
        self.setModal(True)
        self.setFixedSize(420, 220)

        # allow transparency
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setWindowIcon(QIcon("app/image/icon.png"))

        # ========== BACKGROUND (blurred screenshot) ==========
        self._background_lbl = QLabel(self)
        self._background_lbl.setGeometry(self.rect())
        self._background_lbl.setScaledContents(True)

        # ========== OVERLAY (glass tint + border) ==========
        self._overlay = QWidget(self)
        self._overlay.setGeometry(self.rect())
        self._overlay.setAttribute(Qt.WA_TransparentForMouseEvents)

        self._overlay.setStyleSheet(
            """
            QWidget {
                background-color: rgba(255, 255, 255, 200);
                border-radius: 15px;
                border: 1px solid rgba(200, 210, 220, 200);
            }
            """
        )

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 90))
        self._overlay.setGraphicsEffect(shadow)

        # ========== CONTENT ==========
        self.content = QWidget(self)
        self.content.setGeometry(self.rect())
        self.content.setStyleSheet("background: transparent;")

        title = QLabel("FLATNESS PDF -> CSV / REPORT TOOL", self.content)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color:#333; font-size:20px; font-weight:750; " \
        "                   font-family: 'Segoe UI', 'Arial', sans-serif; bold")

        subtitle = QLabel("Loading application, please wait…", self.content)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color:#666; font-size:12px;")

        self.progress = QProgressBar(self.content)
        self.progress.setRange(0, 100)
        self.progress.setFixedHeight(10)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(
            """
            QProgressBar {
                background-color: rgba(255,255,255,120);
                border-radius: 5px;
            }
            QProgressBar::chunk {
                background-color: #4a90e2;
                border-radius: 5px;
            }
            """
        )

        icon_lbl = QLabel(self.content)
        icon_pix = QPixmap("app/image/logo.png")
        if not icon_pix.isNull():
            icon_lbl.setPixmap(icon_pix.scaledToWidth(150, Qt.SmoothTransformation))
            icon_lbl.setAlignment(Qt.AlignCenter)
            icon_lbl.setStyleSheet("margin: 0px 0px;")

        copyright_lbl = QLabel(
            "© 2026 Nhat Viet Industrial Co., Ltd. All Rights Reserved.",
            self.content,
        )
        copyright_lbl.setAlignment(Qt.AlignCenter)
        copyright_lbl.setStyleSheet("color:#888; font-size:11px; margin: 0px 0px;")

        layout = QVBoxLayout(self.content)
        layout.setContentsMargins(24, 18, 24, 0)
        layout.setSpacing(8)
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(6)
        layout.addWidget(self.progress)
        layout.addSpacing(8)
        if not icon_pix.isNull():
            layout.addWidget(icon_lbl)
        layout.addWidget(copyright_lbl)
        layout.addStretch()

        # stacking order
        self._background_lbl.lower()
        self._overlay.stackUnder(self.content)
        self.content.raise_()

        # progress animation
        self._progress_value = 0
        self._progress_timer = QTimer(self)
        self._progress_timer.timeout.connect(self._update_progress)
        self._progress_timer.start(30)

        self._did_capture = False
        self._center_on_screen()

    # -------------------------------------------------

    def _center_on_screen(self):
        screen = QApplication.primaryScreen()
        if not screen:
            return
        geom = screen.availableGeometry()
        frame = self.frameGeometry()
        frame.moveCenter(geom.center())
        self.move(frame.topLeft())

    def _update_progress(self):
        self._progress_value += 3
        if self._progress_value > 100:
            self._progress_value = 0
        self.progress.setValue(self._progress_value)

    # -------------------------------------------------
    # Events
    # -------------------------------------------------

    def showEvent(self, event):
        super().showEvent(event)
        if not self._did_capture:
            self._capture_and_blur_background()
            self._did_capture = True

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._background_lbl.setGeometry(self.rect())
        self._overlay.setGeometry(self.rect())
        self.content.setGeometry(self.rect())

    # -------------------------------------------------
    # Glass / blur logic
    # -------------------------------------------------

    def _capture_and_blur_background(self):
        """
        Capture screen under the splash window and blur it.
        If capture fails (driver / remote / permission), silently fallback.
        """
        screen = QApplication.primaryScreen()
        if not screen:
            return

        geom: QRect = self.frameGeometry()

        try:
            pix = screen.grabWindow(
                0,
                geom.x(),
                geom.y(),
                geom.width(),
                geom.height(),
            )
            if pix.isNull():
                return
        except Exception:
            return

        try:
            # apply blur via QLabel + QGraphicsBlurEffect
            temp_lbl = QLabel()
            temp_lbl.setPixmap(pix)

            blur = QGraphicsBlurEffect()
            blur.setBlurRadius(14)
            temp_lbl.setGraphicsEffect(blur)

            blurred = QPixmap(pix.size())
            blurred.fill(Qt.transparent)

            # IMPORTANT: correct render call (no crash)
            temp_lbl.render(blurred)

            # subtle white tint
            final_pix = QPixmap(blurred.size())
            final_pix.fill(Qt.transparent)
            painter = QPainter(final_pix)
            painter.drawPixmap(0, 0, blurred)
            painter.fillRect(
                final_pix.rect(),
                QColor(255, 255, 255, 24),
            )
            painter.end()

            self._background_lbl.setPixmap(final_pix)
            self._background_lbl.setScaledContents(True)

        except Exception:
            # any failure -> keep overlay only
            return
