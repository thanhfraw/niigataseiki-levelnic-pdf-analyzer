# Copyright © 2026 Nhat Viet Industrial Co., Ltd.
# All rights reserved.
#
# This software is proprietary and confidential.
# Unauthorized copying, modification, or distribution is strictly prohibited.

# app/ui/graph_dialog.py
"""
Module: Graph Dialog
Task: Display graph images in dialog windows
Description: Provides dialog windows for displaying graph images with zoom and scroll functionality

Tác vụ: Hiển thị biểu đồ trong cửa sổ dialog
Mô tả: Cung cấp cửa sổ dialog để hiển thị ảnh biểu đồ với chức năng zoom và scroll
"""

from __future__ import annotations
import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QScrollArea, QLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

def show_image_dialog(parent, image_path: str, title: str = "Graph"):
    if not image_path or not os.path.exists(image_path):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(parent, "No image", f"Image not found:\n{image_path}")
        return
    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    dlg.resize(900, 600)
    v = QVBoxLayout(dlg)
    scroll = QScrollArea(dlg)
    scroll.setWidgetResizable(True)
    v.addWidget(scroll)
    lbl = QLabel()
    lbl.setAlignment(Qt.AlignCenter)
    pix = QPixmap(image_path)
    lbl.setPixmap(pix)
    lbl.setScaledContents(False)
    scroll.setWidget(lbl)

    # simple initial scale
    def _scale():
        vp_w = scroll.viewport().width()
        vp_h = scroll.viewport().height()
        orig_w = pix.width()
        orig_h = pix.height()
        if orig_w <= 0 or orig_h <= 0:
            return
        target_w = int(vp_w * 0.90)
        target_h = int(vp_h * 0.90)
        scale_w = target_w / orig_w
        scale_h = target_h / orig_h
        scale = min(scale_w, scale_h)
        if scale <= 0:
            scale = 1.0
        new_w = max(1, int(orig_w * scale))
        new_h = max(1, int(orig_h * scale))
        scaled = pix.scaled(new_w, new_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        lbl.setPixmap(scaled)

    scroll.viewport().resizeEvent = lambda ev: _scale()
    _scale()
    dlg.exec()

def show_flatness_graph_interactive(rec, parent=None):
    # delegate to your existing show_flatness_graph (app.report.button_show_flatness)
    try:
        from app.report.button_show_flatness import show_flatness_graph
        show_flatness_graph(rec)
    except Exception as e:
        raise
