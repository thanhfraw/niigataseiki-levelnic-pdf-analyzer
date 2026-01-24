# Copyright © 2026 Nhat Viet Industrial Co., Ltd.
# All rights reserved.
#
# This software is proprietary and confidential.
# Unauthorized copying, modification, or distribution is strictly prohibited.

# app/ui/result_view.py
"""
Module: Result View Widget
Task: Display result data in table format
Description: Custom widget for displaying result values and tags in an interactive table

Tác vụ: Hiển thị dữ liệu kết quả dạng bảng
Mô tả: Widget tùy chỉnh để hiển thị giá trị kết quả và tags trong bảng tương tác
"""

from __future__ import annotations
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt

class ResultView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<b>Result Value [um]</b>"))
        self.result_table = QTableWidget()
        layout.addWidget(self.result_table, 1)
        self.setLayout(layout)

    def show_result(self, rec):
        cols = rec.result.cols
        rows = rec.result.rows
        if not cols or not rows:
            self.result_table.clear()
            self.result_table.setRowCount(0)
            self.result_table.setColumnCount(0)
            return
        self.result_table.setColumnCount(len(cols) + 1)
        headers = ["Y\\X"] + [f"[{c:02d}]" for c in cols]
        self.result_table.setHorizontalHeaderLabels(headers)
        self.result_table.setRowCount(len(rows))
        for r_idx, y in enumerate(rows):
            self.result_table.setItem(r_idx, 0, QTableWidgetItem(f"Y[{y:02d}]"))
            for c_idx, x in enumerate(cols):
                val = rec.result.values.get((y, x), "")
                tag = rec.result.tags.get((y, x), "")
                s = str(val)
                if tag:
                    s = f"{s} ({tag})"
                item = QTableWidgetItem(s)
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                self.result_table.setItem(r_idx, c_idx + 1, item)
        self.result_table.resizeColumnsToContents()

    def clear(self):
        """Clear result table."""
        self.result_table.clear()
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(0)
