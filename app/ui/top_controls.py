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
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QMenu, QLabel
from PySide6.QtCore import Qt

from app.config import Config

class TopControls(QWidget):
    def __init__(
        self,
        on_import: Callable,
        on_open_recent: Callable[[str], None],
        on_export_data: Callable,
        on_export_report: Callable,
        on_select_template: Callable,
        on_manage_templates: Callable,
        on_show_flatness: Callable,
        config: Optional[Config] = None,
        parent=None
    ):
        super().__init__(parent)
        self.on_import = on_import
        self.on_open_recent = on_open_recent
        self.on_export_data = on_export_data
        self.on_export_report = on_export_report
        self.on_select_template = on_select_template
        self.on_manage_templates = on_manage_templates
        self.on_show_flatness = on_show_flatness
        self.config = config

        # Row 1: Import, Recent, Manage Templates, Select Template, Show Flatness
        btn_import = QPushButton("Import PDF")
        btn_recent = QPushButton("Recent Files")
        btn_manage_templates = QPushButton("Manage Templates")
        btn_select_template = QPushButton("Select Template")
        btn_show_flatness = QPushButton("Show Flatness")
        
        # Template label to show selected template
        self.template_label = QLabel("No template selected")
        self.template_label.setStyleSheet("color:#888; font-size:10px; padding:5px;")
        self.template_label.setAlignment(Qt.AlignCenter)
        self.template_label.setMaximumWidth(200)

        # Row 2: Export Data, Export Report
        btn_export_data = QPushButton("Export Data CSV")
        btn_export_report = QPushButton("Export Report CSV")
        btn_export_report.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 5px 10px;
                border-radius: 3px;
                border: none;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)

        btn_import.clicked.connect(self.on_import)
        btn_recent.clicked.connect(self._show_recent_menu)
        btn_manage_templates.clicked.connect(self.on_manage_templates)
        btn_select_template.clicked.connect(self.on_select_template)
        btn_show_flatness.clicked.connect(self.on_show_flatness)
        btn_export_data.clicked.connect(self.on_export_data)
        btn_export_report.clicked.connect(self.on_export_report)

        # Row 1 layout
        row1_layout = QHBoxLayout()
        row1_layout.addWidget(btn_import)
        row1_layout.addWidget(btn_recent)
        row1_layout.addWidget(btn_manage_templates)
        row1_layout.addWidget(btn_select_template)
        row1_layout.addWidget(self.template_label, 1)
        row1_layout.addStretch()
        row1_layout.addWidget(btn_show_flatness)
        
        # Row 2 layout
        row2_layout = QHBoxLayout()
        row2_layout.addWidget(btn_export_data)
        row2_layout.addWidget(btn_export_report)
        row2_layout.addStretch()

        # Main layout (vertical)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        main_layout.addLayout(row1_layout)
        main_layout.addLayout(row2_layout)
        self.setLayout(main_layout)

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
    
    def update_template_label(self, template_name: Optional[str]):
        """Update the template label to show selected template."""
        if template_name:
            self.template_label.setText(f"Template: {template_name}")
            self.template_label.setStyleSheet("color:#080; font-size:10px; padding:5px; font-weight:bold;")
        else:
            self.template_label.setText("No template selected")
            self.template_label.setStyleSheet("color:#888; font-size:10px; padding:5px;")
