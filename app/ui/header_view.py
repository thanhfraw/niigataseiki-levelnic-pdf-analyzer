# Copyright © 2026 Nhat Viet Industrial Co., Ltd.
# All rights reserved.
#
# This software is proprietary and confidential.
# Unauthorized copying, modification, or distribution is strictly prohibited.

# app/ui/header_view.py
"""
Module: Header View Widget
Task: Display record header and metadata information
Description: Custom widget for displaying header/metadata information in a read-only text view

Tác vụ: Hiển thị thông tin header và metadata
Mô tả: Widget tùy chỉnh để hiển thị thông tin header/metadata trong chế độ chỉ đọc
"""

from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit

class HeaderView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<b>Header / Metadata</b>"))
        self.header_text = QTextEdit()
        self.header_text.setReadOnly(True)
        layout.addWidget(self.header_text)
        self.setLayout(layout)

    def show_header(self, rec):
        pieces = []
        pieces.append(f"Record ID: {rec.record_id}")
        pieces.append(f"Record Name: {rec.record_name}")
        pieces.append(f"Source PDF: {rec.source_pdf}")
        pieces.append("")
        for k in sorted(rec.header.keys()):
            pieces.append(f"{k}: {rec.header[k]}")
        pieces.append("")
        pieces.append(f"Flatness [um]: {rec.flatness_um}")
        pieces.append("")
        dims = rec.dims()
        pieces.append("Dimensions (measured/result):")
        pieces.append(str(dims))
        self.header_text.setPlainText("\n".join(pieces))

    def clear(self):
        """Clear header display."""
        self.header_text.clear()
