# Copyright © 2026 Nhat Viet Industrial Co., Ltd.
# All rights reserved.
#
# This software is proprietary and confidential.
# Unauthorized copying, modification, or distribution is strictly prohibited.

# app/storage.py
"""
Module: Data Storage
Task: Save parsed Record data to CSV files
Description: Saves parsed Record data to CSV files (header, measured, result)

Tác vụ: Lưu dữ liệu vào file CSV
Mô tả: Lưu dữ liệu Record đã xử lý vào các file CSV (header, measured, result)
"""

import csv
import os

from .models import Record

# ========== Các header cột cho data_header.csv đã mở rộng ==========
HEADER_FIELDS = [
    "record_id",
    "record_name",
    "source_pdf",
    "saved_date",
    "work_name",
    "work_number",
    "operator",
    "comments",

    # raw + parsed tổng/segment/count cho crosswise
    "total_crosswise_length_raw",
    "total_crosswise_full",
    "crosswise_total_mm",
    "crosswise_segment_mm",
    "crosswise_segments_count",

    # raw + parsed tổng/segment/count cho lengthwise
    "total_lengthwise_length_raw",
    "total_lengthwise_full",
    "lengthwise_total_mm",
    "lengthwise_segment_mm",
    "lengthwise_segments_count",

    "flatness_um",

    # kích thước bảng
    "meas_col_count",
    "meas_row_count",
    "meas_x_row_count",
    "meas_y_row_count",
    "res_col_count",
    "res_row_count",
]

MEASURED_FIELDS = ["record_id", "axis", "row", "col", "value_mm_per_m"]
RESULT_FIELDS = ["record_id", "y", "x", "value_um", "tag"]


def _ensure_dir(path: str) -> None:
    """Tạo folder nếu chưa tồn tại."""
    os.makedirs(path, exist_ok=True)


def _write_csv_overwrite(path: str, fieldnames: list[str], rows: list[dict]) -> None:
    """
    Ghi đè (reset) file CSV: mở bằng mode 'w', ghi header rồi ghi rows.
    """
    abspath = os.path.abspath(path)
    print(f"[storage] Writing (overwrite) CSV: {abspath}  (rows={len(rows)})")
    with open(abspath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def save_to_database_csv(rec: Record, out_dir: str) -> None:
    """
    RESET CSV mỗi lần chạy (snapshot).
    - data_header.csv: dạng key-value (HÀNG DỌC)
    - data_measured.csv: bảng cell
    - data_result.csv: bảng cell
    """

    _ensure_dir(out_dir)

    header_path = os.path.join(out_dir, "data_header.csv")
    measured_path = os.path.join(out_dir, "data_measured.csv")
    result_path = os.path.join(out_dir, "data_result.csv")

    # ==================================================
    # 1) data_header.csv — KEY / VALUE (vertical)
    # ==================================================
    header_rows = []

    def add(k, v):
        header_rows.append({
            "key": k,
            "value": "" if v is None else v
        })

    # basic info
    add("record_id", rec.record_id)
    add("record_name", rec.record_name)
    add("source_pdf", rec.source_pdf)
    add("saved_date", rec.saved_date or rec.header.get("saved_date"))

    add("work_name", rec.work_name or rec.header.get("work_name"))
    add("work_number", rec.work_number or rec.header.get("work_number"))
    add("operator", rec.operator or rec.header.get("operator"))
    add("comments", rec.comments or rec.header.get("comments"))

    # crosswise
    add("total_crosswise_length_raw", rec.header.get("total_crosswise_length_raw"))
    add("crosswise_total_mm", rec.crosswise_total_mm)
    add("crosswise_segment_mm", rec.header.get("crosswise_segment_mm"))
    add("crosswise_segments_count", rec.header.get("crosswise_segments_count"))

    # lengthwise
    add("total_lengthwise_length_raw", rec.header.get("total_lengthwise_length_raw"))
    add("lengthwise_total_mm", rec.lengthwise_total_mm)
    add("lengthwise_segment_mm", rec.header.get("lengthwise_segment_mm"))
    add("lengthwise_segments_count", rec.header.get("lengthwise_segments_count"))

    # flatness
    add("flatness_um", rec.flatness_um)

    # dimensions (optional but useful)
    dims = rec.dims()
    for k, v in dims.items():
        add(k, v)

    # ghi đè file header
    _write_csv_overwrite(
        header_path,
        fieldnames=["key", "value"],
        rows=header_rows
    )

    # ==================================================
    # 2) data_measured.csv — DISABLED (pause measured parsing)
    # ==================================================
    # Skipping measured CSV writing as measured parsing is disabled
    # measured_rows = []
    # for (axis, row, col), value in rec.measured.values.items():
    #     measured_rows.append({...})
    # _write_csv_overwrite(measured_path, MEASURED_FIELDS, measured_rows)

    # ==================================================
    # 3) data_result.csv — giữ nguyên (cell-based)
    # ==================================================
    result_rows = []
    for (y, x), value in rec.result.values.items():
        result_rows.append({
            "record_id": rec.record_id,
            "y": y,
            "x": x,
            "value_um": value,
            "tag": rec.result.tags.get((y, x), "")
        })

    _write_csv_overwrite(
        result_path,
        RESULT_FIELDS,
        result_rows
    )

    print(f"[storage] Exported snapshot (vertical header) to: {os.path.abspath(out_dir)}")
