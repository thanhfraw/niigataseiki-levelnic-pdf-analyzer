# Copyright © 2026 Nhat Viet Industrial Co., Ltd.
# All rights reserved.
#
# This software is proprietary and confidential.
# Unauthorized copying, modification, or distribution is strictly prohibited.

# app/report/reporting.py
"""
Module: Report Workflow
Task: Orchestrate PDF import, data export, and report generation
Description: Central hub for all report-related operations (import, parse, export data, export reports)

Features:
- Import and parse PDF files
- Export parsed data to CSV
- Generate reports from templates
- Handle graph generation and insertion

Tác vụ: Điều phối quy trình báo cáo
Mô tả: Trung tâm cho các hoạt động liên quan đến báo cáo (import, parse, export data, export reports)

Tính năng:
- Import và parse file PDF
- Export dữ liệu đã parse ra CSV
- Tạo báo cáo từ template
- Xử lý tạo và chèn biểu đồ
"""
from __future__ import annotations
import os
from PySide6.QtWidgets import QFileDialog, QMessageBox

from app.utils import ensure_dir, open_folder
from app.config import Config

# core functions from parent app
from ..extractor import extract_lines
from ..parser import parse_record
from ..storage import save_to_database_csv
from .copy_paste import process_template

def import_pdf_flow(parent, start_dir: str | None, status_widget, config: Config | None = None, file_path: str | None = None):
    """
    Import PDF, parse, auto-save data. Returns (rec, pdf_path) or None.
    
    Import PDF, parse, tự động lưu dữ liệu. Trả về (rec, pdf_path) hoặc None.
    """
    start = start_dir or os.getcwd()
    if file_path:
        path = file_path
    else:
        path, _ = QFileDialog.getOpenFileName(parent, "Open PDF", start, "PDF files (*.pdf)")
    if not path:
        return None

    folder = os.path.dirname(path)
    cfg = config or Config()
    cfg.set_last_open_dir(folder)
    cfg.add_recent_file(path)

    status_widget.set_progress(0, visible=True)
    status_widget.set_status(f"Importing: {os.path.basename(path)}...")
    try:
        status_widget.set_progress(25)
        lines = extract_lines(path)
        status_widget.set_progress(50)
    except Exception as e:
        status_widget.set_progress(0, visible=False)
        QMessageBox.critical(parent, "Error", f"Failed to read PDF: {e}")
        return None

    base = os.path.basename(path)
    record_name = os.path.splitext(base)[0]
    status_widget.set_progress(60)
    rec = parse_record(lines, pdf_path=path, record_name=record_name)
    status_widget.set_progress(75)

    if rec.warnings:
        QMessageBox.information(parent, "Warnings", "\n".join(rec.warnings[:10]))
    if rec.errors:
        status_widget.set_progress(0, visible=False)
        status_widget.set_status("Error: Parse errors found")
        QMessageBox.critical(parent, "Errors", "Parse errors found:\n" + "\n".join(rec.errors[:20]))
        return None

    # auto-save to output_data
    out_dir = ensure_dir(os.path.join(os.getcwd(), "output_data"))
    try:
        save_to_database_csv(rec, out_dir)
        status_widget.set_progress(100)
    except Exception as e:
        print(f"[WARNING] Auto-save failed: {e}")
    status_widget.set_progress(0, visible=False)
    status_widget.start_green_blink(f"✓ Successfully imported: {record_name}")
    return rec, path

def export_data_csv(rec, parent=None, status_widget=None):
    """
    Export parsed record to CSV in output_data folder.
    
    Export record đã parse ra CSV trong thư mục output_data.
    """
    out_dir = ensure_dir(os.path.join(os.getcwd(), "output_data"))
    if status_widget:
        status_widget.set_status("Exporting data...")
    try:
        save_to_database_csv(rec, out_dir)
        if status_widget:
            status_widget.start_green_blink("✓ Data exported successfully")
            
    except Exception as e:
        if status_widget:
            status_widget.set_status("Error: Failed to export data")
        QMessageBox.critical(parent or None, "Error", f"Failed to save CSV: {e}")
        return
    try:
        open_folder(out_dir)
    except Exception:
        print(f"[INFO] Data saved to folder: {out_dir}")

def export_report_flow(rec, current_pdf_path: str | None, selected_template: str | None = None, parent=None):
    """
    Complete report export workflow:
    1. Use pre-selected template or auto-detect from templates folder
    2. Choose output folder
    3. Generate graph images
    4. Process template and save report
    5. Insert graphs into XLSX if applicable
    
    Logic: 
    - If selected_template is provided, use it directly
    - If no template selected, auto-detect from templates folder
    - If only 1 template file in templates/, use it automatically
    - If multiple templates, ask user to choose
    - User can modify templates or add new ones anytime
    """
    cfg = Config()
    templates_dir = os.path.join(os.getcwd(), "templates")
    os.makedirs(templates_dir, exist_ok=True)
    
    # If template is pre-selected, use it
    if selected_template and os.path.exists(selected_template):
        print(f"[DEBUG] Using pre-selected template: {selected_template}")
        tpl_path = selected_template
    else:
        # Try to load from config (for remembered template)
        saved_template = cfg.get_last_template()
        if saved_template and os.path.exists(saved_template):
            print(f"[DEBUG] Using saved template from config: {saved_template}")
            tpl_path = saved_template
        else:
            print(f"[DEBUG] No template saved, auto-detecting...")
            # Auto-detect templates in folder
            import glob
            template_files = []
            for ext in ['*.xlsx', '*.csv', '*.xlsm', '*.xltx']:
                template_files.extend(glob.glob(os.path.join(templates_dir, ext)))
            
            if len(template_files) == 0:
                # No templates found, ask user to select
                QMessageBox.information(parent, "No template found", 
                    f"No template files found in '{templates_dir}' folder.\\n"
                    "Please add a template file (.xlsx or .csv) to the templates folder.")
                return
            elif len(template_files) == 1:
                # Only 1 template, use it automatically
                tpl_path = template_files[0]
            else:
                # Multiple templates, ask user to choose
                tpl_path, _ = QFileDialog.getOpenFileName(
                    parent, 
                    f"Choose template file ({len(template_files)} templates found)",
                    templates_dir,
                    "Templates (*.csv *.xlsx *.xlsm *.xltx);;All Files (*)"
                )
                if not tpl_path:
                    QMessageBox.information(parent, "No template", "No template selected. Export cancelled.")
                    return

    tpl_fname = os.path.basename(tpl_path)
    ext = os.path.splitext(tpl_fname)[1].lower()
    safe_name = (rec.record_name or "report").replace(" ", "_")
    suggested_filename = f"{safe_name}_from_{os.path.splitext(tpl_fname)[0]}{ext}"

    default_dir = (os.path.dirname(current_pdf_path) if current_pdf_path else None) \
                  or cfg.get_last_report_dir() or os.path.join(os.getcwd(), "output_data")

    out_dir = QFileDialog.getExistingDirectory(parent, "Select folder to save report", default_dir)
    if not out_dir:
        return
    cfg.set_last_report_dir(out_dir)
    save_path = os.path.join(out_dir, suggested_filename)

    graph_dir = ensure_dir(os.path.join(os.getcwd(), "graph"))
    measured_img = os.path.join(graph_dir, f"{safe_name}_measured.png")
    result_img = os.path.join(graph_dir, f"{safe_name}_result.png")
    flatness_img = os.path.join(graph_dir, f"{safe_name}_flatness.png")

    # generate graphs (best-effort)
    try:
        from .result_graph import generate_result_graph
        try:
            generate_result_graph(rec, out_path=result_img)
        except Exception as ge:
            QMessageBox.information(parent, "Graph", f"Result graph generation failed (image not created):\n{ge}")
            result_img = None
    except Exception:
        result_img = None

    try:
        from .flatness_graph import generate_flatness_graph
        try:
            generate_flatness_graph(rec, out_path=flatness_img)
        except Exception as ge:
            QMessageBox.information(parent, "Graph", f"Flatness graph generation failed (image not created):\n{ge}")
            flatness_img = None
    except Exception:
        flatness_img = None

    # process template
    try:
        res = process_template(tpl_path, save_path, rec)
    except ImportError as e:
        QMessageBox.critical(parent, "Missing library", f"A required library is missing:\n{e}")
        return
    except Exception as e:
        QMessageBox.critical(parent, "Error", f"Failed to generate report:\n{e}")
        return

    # optional insert images if xlsx
    if res.get("ext") in (".xlsx", ".xlsm", ".xltx", ".xltm"):
        try:
            from .insert import insert_multiple_images_into_xlsx
        except Exception:
            insert_multiple_images_into_xlsx = None

        if insert_multiple_images_into_xlsx:
            images_to_insert = []
            for img_path, placeholder in [
                (flatness_img, "[FLATNESS_GRAPH]"),
                (measured_img, "[MEASURED_GRAPH]"),
                (result_img, "[RESULT_GRAPH]"),
            ]:
                if img_path and os.path.exists(img_path):
                    images_to_insert.append((img_path, placeholder))
            if images_to_insert:
                try:
                    insert_multiple_images_into_xlsx(
                        save_path,
                        images_to_insert,
                        copy_outputs_to_graph=True,
                        graph_dir=graph_dir,
                        target_width_cm=15.0
                    )
                except Exception as ie:
                    QMessageBox.warning(parent, "Graph insert failed", f"Failed to insert graphs:\n{ie}")

    try:
        open_folder(out_dir)
    except Exception:
        pass

    created_imgs = []
    for p in (measured_img, result_img, flatness_img):
        if p and os.path.exists(p):
            created_imgs.append(os.path.relpath(p, os.getcwd()))
    txt = f"Report created from template:\n{save_path}"
    if created_imgs:
        txt += "\n\nGenerated graph images:\n" + "\n".join(created_imgs)
    print(f"[INFO] {txt}")
