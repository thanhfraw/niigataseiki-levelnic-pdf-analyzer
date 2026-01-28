# Copyright © 2026 Nhat Viet Industrial Co., Ltd.
# All rights reserved.
#
# This software is proprietary and confidential.
# Unauthorized copying, modification, or distribution is strictly prohibited.

# app/gui.py
"""
Module: Main GUI Application
Task: Main window and GUI application entry point
Description: Implements the main application window with PDF import, export, and visualization features

Tác vụ: Cửa sổ chính và điểm vào GUI
Mô tả: Triển khai cửa sổ ứng dụng chính với tính năng import PDF, export và visualization
"""

from __future__ import annotations
import os
import sys
import platform
from typing import Optional

# PyInstaller support: get the base path for bundled resources
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    # Running as compiled executable
    BASE_PATH = sys._MEIPASS
else:
    # Running as script
    BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QLabel,
    QMenu,
    QMessageBox,
    QDialog,
    QTextBrowser,
    QPushButton,
    QFileDialog,
)

from app.ui.top_controls import TopControls
from app.ui.header_view import HeaderView
from app.ui.result_view import ResultView
from app.ui.status_widget import StatusWidget
from app.config import Config
from app.splash import SplashScreen

CONFIG_FILENAME = "app_config.json"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flatness PDF -> CSV / Report")
        self.resize(900, 700)

        icon_path = os.path.join(BASE_PATH, "app/image/icon.png")
        icon = QIcon(icon_path)
        self.setWindowIcon(icon)

        self.current_record = None
        self.current_pdf_path: Optional[str] = None
        self.selected_template: Optional[str] = None  # Store selected template path

        self.config = Config(CONFIG_FILENAME)
        self.last_open_dir = self.config.get_last_open_dir()
        
        # Load previously selected template if it exists
        self.selected_template = self.config.get_last_template()

        # Menubar
        self._build_menubar()

        # UI widgets
        self.status_widget = StatusWidget()
        self.header_view = HeaderView()
        self.result_view = ResultView()
        self.top_controls = TopControls(
            on_import=self.on_import_pdf,
            on_open_recent=self.on_open_recent,
            on_export_data=self.on_export_data,
            on_export_report=self.on_export_report,
            on_select_template=self.on_select_template,
            on_manage_templates=self.on_manage_templates,
            on_show_flatness=self.on_show_flatness,
            config=self.config
        )
        
        # Update template label with saved template if exists
        if self.selected_template and os.path.exists(self.selected_template):
            tpl_name = os.path.basename(self.selected_template)
            self.top_controls.update_template_label(tpl_name)

        # layout
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.header_view)
        splitter.addWidget(self.result_view)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        # Footer layout: Copyright (left) + Status (right)
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 5, 0, 5)
        footer_layout.setSpacing(10)
        
        footer_label = QLabel("© 2026 Nhat Viet Industrial Co., Ltd. All Rights Reserved.")
        footer_label.setStyleSheet("color:#888; font-size:12px; padding-left:10px;")
        footer_label.setAlignment(Qt.AlignLeft)
        
        footer_layout.addWidget(footer_label)
        footer_layout.addStretch()  # Push status to the right
        footer_layout.addWidget(self.status_widget, 0, Qt.AlignRight)
        

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.top_controls)
        main_layout.addWidget(splitter, 1)
        main_layout.addLayout(footer_layout)

        central = QWidget()
        central.setLayout(main_layout)
        self.setCentralWidget(central)
        self.setAcceptDrops(True)

    # ---------- Handlers (logic largely moved to helpers) ----------
    def on_import_pdf(self):
        from app.report.reporting import import_pdf_flow  # local import to avoid circular
        res = import_pdf_flow(parent=self, start_dir=self.last_open_dir, status_widget=self.status_widget, config=self.config)
        if not res:
            return
        rec, pdf_path = res
        self._load_record(rec, pdf_path)

    def on_open_recent(self, path: str):
        """Open a recent PDF without file picker."""
        from app.report.reporting import import_pdf_flow
        if not os.path.exists(path):
            self.status_widget.set_status("Recent file missing")
            return
        res = import_pdf_flow(
            parent=self,
            start_dir=os.path.dirname(path),
            status_widget=self.status_widget,
            config=self.config,
            file_path=path,
        )
        if not res:
            return
        rec, pdf_path = res
        self._load_record(rec, pdf_path)

    def on_clear_all(self):
        """Clear current record and views."""
        self.current_record = None
        self.current_pdf_path = None
        self.selected_template = None
        self.config.clear_last_template()  # Remove template from config too
        self.header_view.clear()
        self.result_view.clear()
        self.top_controls.update_template_label(None)
        self.status_widget.set_status("CLEARED")

    def on_export_data(self):
        from app.report.reporting import export_data_csv
        if not self.current_record:
            self.status_widget.start_red_blink("PLEASE IMPORT DATA FIRST")
            return
        export_data_csv(self.current_record, parent=self, status_widget=self.status_widget)

    def on_export_report(self):
        from app.report.reporting import export_report_flow
        if not self.current_record:
            self.status_widget.start_red_blink("PLEASE IMPORT DATA FIRST")
            return
        
        # Check if template is selected
        if not self.selected_template:
            self.status_widget.start_red_blink("PLEASE SELECT TEMPLATE FIRST")
            return
        
        export_report_flow(self.current_record, current_pdf_path=self.current_pdf_path, 
                          selected_template=self.selected_template, parent=self)

    def on_select_template(self):
        """Select a template file for report export."""
        import glob
        templates_dir = os.path.join(os.getcwd(), "templates")
        os.makedirs(templates_dir, exist_ok=True)
        
        # Find all template files
        template_files = []
        for ext in ['*.xlsx', '*.csv', '*.xlsm', '*.xltx']:
            template_files.extend(glob.glob(os.path.join(templates_dir, ext)))
        
        if not template_files:
            QMessageBox.information(self, "No templates",
                f"No template files found in '{templates_dir}'.\\n"
                "Please add template files (.xlsx, .csv, .xlsm, .xltx) to the templates folder.")
            return
        
        # Show file dialog to select template
        tpl_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Select Report Template ({len(template_files)} found)",
            templates_dir,
            "Templates (*.xlsx *.csv *.xlsm *.xltx);;All Files (*)"
        )
        
        if tpl_path:
            self.selected_template = tpl_path
            self.config.set_last_template(tpl_path)  # Save to config
            tpl_name = os.path.basename(tpl_path)
            self.status_widget.set_status(f"✓ Template selected: {tpl_name}")
            self.top_controls.update_template_label(tpl_name)
        else:
            self.status_widget.set_status("No template selected")

    def on_manage_templates(self):
        """Open templates folder for managing templates."""
        from app.utils import open_folder
        templates_dir = os.path.join(os.getcwd(), "templates")
        os.makedirs(templates_dir, exist_ok=True)
        try:
            open_folder(templates_dir)
            self.status_widget.set_status("Opened templates folder")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open templates folder:\n{e}")

    def on_adjust_layout(self):
        from app.utils import open_folder
        templates_dir = os.path.join(os.getcwd(), "templates")
        os.makedirs(templates_dir, exist_ok=True)
        open_folder(templates_dir)

    def on_show_flatness(self):
        if not self.current_record:
            self.status_widget.set_message_box("No data", "Import a PDF first.")
            return
        # delegate to graph/flatness module
        from app.ui.graph_dialog import show_flatness_graph_interactive
        try:
            show_flatness_graph_interactive(self.current_record, parent=self)
        except Exception as e:
            self.status_widget.set_message_box("Graph error", f"Failed to generate 3D flatness graph:\n{e}")

    def _load_record(self, rec, pdf_path: str):
        self.current_record = rec
        self.current_pdf_path = pdf_path
        self.header_view.show_header(rec)
        self.result_view.show_result(rec)
        self.last_open_dir = os.path.dirname(pdf_path)
        self.config.set_last_open_dir(self.last_open_dir)
        self._refresh_recent_menu()

    def _import_pdf_path(self, path: str):
        from app.report.reporting import import_pdf_flow
        if not os.path.exists(path):
            self.status_widget.start_red_blink("FILE NOT FOUND")
            return
        res = import_pdf_flow(
            parent=self,
            start_dir=os.path.dirname(path),
            status_widget=self.status_widget,
            config=self.config,
            file_path=path,
        )
        if not res:
            return
        rec, pdf_path = res
        self._load_record(rec, pdf_path)

    # ---------- UI helpers ----------
    def _build_menubar(self):
        menubar = self.menuBar()
        menubar.clear()

        file_menu = menubar.addMenu("File")
        act_import = file_menu.addAction("Import PDF…")
        act_import.triggered.connect(self.on_import_pdf)

        self.recent_menu = QMenu("Recent Files", self)
        file_menu.addMenu(self.recent_menu)
        self._refresh_recent_menu()

        act_clear = file_menu.addAction("Clear / Reset")
        act_clear.triggered.connect(self.on_clear_all)

        file_menu.addSeparator()
        act_exit = file_menu.addAction("Exit")
        act_exit.triggered.connect(self.close)

        help_menu = menubar.addMenu("Help")
        act_help = help_menu.addAction("Usage Guide")
        act_help.triggered.connect(self._show_help)
        act_about = help_menu.addAction("About")
        act_about.triggered.connect(self._show_about)

    def _refresh_recent_menu(self):
        if not hasattr(self, "recent_menu"):
            return
        self.recent_menu.clear()
        files = self.config.get_recent_files() if self.config else []
        if not files:
            act = self.recent_menu.addAction("No recent files")
            act.setEnabled(False)
            return
        for path in files:
            label = os.path.basename(path) or path
            action = self.recent_menu.addAction(label)
            action.setToolTip(path)
            action.triggered.connect(lambda checked=False, p=path: self.on_open_recent(p))

    # ---------- Drag & Drop PDF ----------
    def dragEnterEvent(self, event):  # noqa: N802 (Qt naming)
        md = event.mimeData()
        if md.hasUrls() and any(url.toLocalFile().lower().endswith(".pdf") for url in md.urls()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):  # noqa: N802 (Qt naming)
        md = event.mimeData()
        if not md.hasUrls():
            event.ignore()
            return
        pdf_paths = [u.toLocalFile() for u in md.urls() if u.toLocalFile().lower().endswith(".pdf")]
        if not pdf_paths:
            event.ignore()
            return
        event.acceptProposedAction()
        self._import_pdf_path(pdf_paths[0])  # take the first PDF

    def _show_about(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("About")

        arch, _ = platform.architecture()
        is_64 = "Yes" if arch.startswith("64") else "No"
        version = "1.0"
        program_block = (
            f"<b>Program version</b><br>"
            f"Flatness PDF -> CSV / Report<br>"
            f"Version: {version}<br>"
            f"Architecture: {platform.machine()}<br>"
            f"Is 64bit: {is_64}"
        )

        dev_block = (
            "<b>Developer info</b><br>"
            "Nhat Viet Industrial Co., Ltd.<br>"
            "© 2026<Br>"
            "Official webpage: <a href=\"https://nhatvietindustry.com.vn\">nhatvietindustry.com.vn</a><br>"
            "Email: <a href=\"mailto:office@nhatvietindustry.com.vn\">office@nhatvietindustry.com.vn</a>"
        )

        assets_block = (
            "<b>Assets used</b><br>"
            "PySide6 (Qt for Python)<br>"
            "Matplotlib / NumPy (graphs)<br>"
            "Pandas (CSV handling)<br>"
            "OpenPyXL (report images)"
        )

        body = QTextBrowser(dlg)
        body.setOpenExternalLinks(True)
        body.setHtml(
            f"<div style='font-size:12px;'>"
            f"{program_block}<br><br>"
            f"{dev_block}<br><br>"
            f"{assets_block}"
            f"</div>"
        )
        body.setMinimumWidth(360)
        body.setMinimumHeight(260)

        btn_close = QPushButton("Close", dlg)
        btn_close.clicked.connect(dlg.accept)

        layout = QVBoxLayout()
        layout.addWidget(body)
        layout.addWidget(btn_close, alignment=Qt.AlignRight)
        dlg.setLayout(layout)
        dlg.exec()

    def _show_help(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Usage Guide")

        steps = (
            "<b>Import & Parse</b><br>"
            "1. File -> Import PDF… (hoặc Recent Files).<br>"
            "2. Ứng dụng đọc PDF, trích dữ liệu và hiển thị Header/Result.<br><br>"
            "<b>Export</b><br>"
            "3. Export to Data CSV: lưu dữ liệu đã parse vào output_data.<br>"
            "4. Export to Report CSV: chọn template, sinh báo cáo và chèn hình (nếu là XLSX).<br><br>"
            "<b>Layout & Graph</b><br>"
            "5. Adjust layout / Open templates: mở thư mục templates để chỉnh mẫu.<br>"
            "6. Show Flatness: xem biểu đồ 3D.<br><br>"
            "<b>Reset</b><br>"
            "7. File -> Clear / Reset để xoá dữ liệu đang hiển thị."
        )

        body = QTextBrowser(dlg)
        body.setOpenExternalLinks(True)
        body.setHtml(f"<div style='font-size:12px;'>{steps}</div>")
        body.setMinimumWidth(420)
        body.setMinimumHeight(260)

        btn_close = QPushButton("Close", dlg)
        btn_close.clicked.connect(dlg.accept)

        layout = QVBoxLayout()
        layout.addWidget(body)
        layout.addWidget(btn_close, alignment=Qt.AlignRight)
        dlg.setLayout(layout)
        dlg.exec()

def main():
    app = QApplication(sys.argv)

    splash = SplashScreen()
    splash.show()

    def start_main_window():
        splash.accept()
        app.main_window = MainWindow()  # keep reference on app to avoid GC
        app.main_window.show()

    QTimer.singleShot(3000, start_main_window)
    app.exec()

if __name__ == "__main__":
    main()
