# Copyright © 2026 Nhat Viet Industrial Co., Ltd.
# All rights reserved.
#
# This software is proprietary and confidential.
# Unauthorized copying, modification, or distribution is strictly prohibited.

# app/ui/top_controls.py
"""
Module: Top Controls Widget
Task: Provide main control buttons for application operations
Description: Custom widget with control buttons for import, export, and other main operations

Tác vụ: Cung cấp các nút điều khiển chính
Mô tả: Widget tùy chỉnh với các nút điều khiển cho import, export và các thao tác chính khác
"""

from __future__ import annotations
import os
from typing import Callable, Optional
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QMenu

from app.config import Config

class TopControls(QWidget):
    def __init__(
        self,
        on_import: Callable,
        on_open_recent: Callable[[str], None],
        on_export_data: Callable,
        on_export_report: Callable,
        on_adjust_layout: Callable,
        on_show_flatness: Callable,
        config: Optional[Config] = None,
        parent=None
    ):
        super().__init__(parent)
        self.on_import = on_import
        self.on_open_recent = on_open_recent
        self.on_export_data = on_export_data
        self.on_export_report = on_export_report
        self.on_adjust_layout = on_adjust_layout
        self.on_show_flatness = on_show_flatness
        self.config = config

        btn_import = QPushButton("Import PDF")
        btn_recent = QPushButton("Recent Files")
        btn_export_data = QPushButton("Export to Data CSV")
        btn_export_report = QPushButton("Export to Report CSV")
        btn_adjust_layout = QPushButton("Adjust layout / Open templates")
        btn_show_flatness = QPushButton("Show Flatness")

        btn_import.clicked.connect(self.on_import)
        btn_recent.clicked.connect(self._show_recent_menu)
        btn_export_data.clicked.connect(self.on_export_data)
        btn_export_report.clicked.connect(self.on_export_report)
        btn_adjust_layout.clicked.connect(self.on_adjust_layout)
        btn_show_flatness.clicked.connect(self.on_show_flatness)

        layout = QHBoxLayout()
        layout.addWidget(btn_import)
        layout.addWidget(btn_recent)
        layout.addWidget(btn_export_data)
        layout.addWidget(btn_export_report)
        layout.addStretch()
        layout.addWidget(btn_adjust_layout)
        layout.addWidget(btn_show_flatness)
        self.setLayout(layout)

        self._btn_recent = btn_recent

    def _show_recent_menu(self):
        menu = QMenu(self)
        files = self.config.get_recent_files() if self.config else []
        if not files:
            action = menu.addAction("No recent files")
            action.setEnabled(False)
        else:
            for path in files:
                label = os.path.basename(path) or path
                action = menu.addAction(label)
                action.setToolTip(path)
                action.triggered.connect(lambda checked=False, p=path: self.on_open_recent(p))

        menu.exec(self._btn_recent.mapToGlobal(self._btn_recent.rect().bottomLeft()))
