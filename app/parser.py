# Copyright © 2026 Nhat Viet Industrial Co., Ltd.
# All rights reserved.
#
# This software is proprietary and confidential.
# Unauthorized copying, modification, or distribution is strictly prohibited.

# app/parser.py
"""
Module: PDF Data Parser
Task: Parse PDF text and convert to structured Record objects
Description: Parses PDF text lines and converts them to Record objects with structured data

Tác vụ: Phân tích và trích xuất dữ liệu từ text PDF
Mô tả: Đọc các dòng text và chuyển thành object Record có cấu trúc
"""

import os
import re
import uuid
from typing import Optional, Dict, List

from .models import Record

# -------------------------
# Helper nhỏ, dễ hiểu
# -------------------------
def to_int(s: str) -> Optional[int]:
    try:
        return int(s)
    except Exception:
        return None

def to_float(s: str) -> Optional[float]:
    try:
        return float(s)
    except Exception:
        return None

def normalize_key(key: str) -> str:
    return key.strip().lower().replace(" ", "_")

def first_number_in_text(s: str) -> Optional[float]:
    m = re.search(r"[-+]?\d+(\.\d+)?", s)
    if not m:
        return None
    return to_float(m.group(0))


# -------------------------
# Hàm parse total length line
# -------------------------
def parse_total_length_line_value(text: str) -> Optional[Dict[str, object]]:
    """
    Nhận một dòng như:
      "Total crosswise measurement length = 450[mm] ( 150[mm] * 3 )"
    Trả về dict với:
      - raw: phần raw sau '=' (toàn bộ chuỗi)
      - total_mm: 450 (int) nếu tìm được
      - segment_mm: 150 (int) nếu tìm được trong ngoặc
      - segments_count: 3 (int) nếu tìm được trong ngoặc
    Nếu không hợp lệ vẫn trả raw với các giá trị số là None.
    """
    if text is None:
        return None

    # Lấy phần sau dấu '=' nếu có
    rhs = text.split("=", 1)[1].strip() if "=" in text else text.strip()
    raw = rhs

    # tìm total trước [mm]
    total_mm = None
    m_total = re.search(r"(\d+)\s*\[?mm\]?", rhs, flags=re.IGNORECASE)
    if m_total:
        total_mm = to_int(m_total.group(1))

    # tìm phần trong ngoặc (nếu có)
    segment_mm = None
    segments_count = None
    m_par = re.search(r"\(([^)]+)\)", rhs)
    if m_par:
        inside = m_par.group(1)
        # tìm số mm trong ngoặc, có thể '150[mm]' hoặc '150 mm'
        m_seg = re.search(r"(\d+)\s*\[?mm\]?", inside, flags=re.IGNORECASE)
        if m_seg:
            segment_mm = to_int(m_seg.group(1))
        # tìm số sau dấu * (ví dụ "* 3")
        m_count = re.search(r"\*\s*(\d+)", inside)
        if m_count:
            segments_count = to_int(m_count.group(1))
        # nếu có segment_mm nhưng không có *count, mặc định count = 1
        if segment_mm is not None and segments_count is None:
            segments_count = 1

    return {
        "raw": raw,
        "total_mm": total_mm,
        "segment_mm": segment_mm,
        "segments_count": segments_count,
    }


# -------------------------
# Các hàm parse row bảng
# -------------------------
def find_all_column_indexes(line: str) -> List[int]:
    # Only match lines that are pure column headers, not Y[...] rows
    if line.strip().startswith('Y['):
        return []
    found = re.findall(r"\[(\d+)\]", line)
    if len(found) < 1:
        return []
    cols = []
    for x in found:
        n = to_int(x)
        if n is None:
            return []
        cols.append(n)
    return cols

def parse_measured_row(line: str):
    m = re.match(r"^(X|Y)\[(\d+)\]\s+(.+)$", line)
    if not m:
        return None
    axis = m.group(1)
    row_index = to_int(m.group(2))
    rest = m.group(3).strip()
    tokens = rest.split()
    values = []
    for t in tokens:
        v = to_float(t)
        if v is None:
            return None
        values.append(v)
    return axis, row_index, values

def parse_result_row(line: str):
    m = re.match(r"^Y\[(\d+)\]\s+(.+)$", line)
    if not m:
        return None
    y_index = to_int(m.group(1))
    rest = m.group(2).strip()
    tokens = rest.split()
    values = []
    tags = []
    for tok in tokens:
        tag = ""
        num_text = tok
        if tok.startswith("*"):
            tag = "MAX"
            num_text = tok[1:]
        elif tok.startswith("@"):
            tag = "MIN"
            num_text = tok[1:]
        v = to_float(num_text)
        if v is None:
            return None
        values.append(v)
        tags.append(tag)
    return y_index, values, tags

def parse_value_tokens(line: str):
    """
    Parse a line that contains only value tokens (optionally tagged with '*' MAX or '@' MIN),
    without a leading Y[...] header. Returns (values, tags) or None if the line doesn't match.
    """
    tokens = line.strip().split()
    if not tokens:
        return None
    values = []
    tags = []
    for tok in tokens:
        tag = ""
        num_text = tok
        if tok.startswith("*"):
            tag = "MAX"
            num_text = tok[1:]
        elif tok.startswith("@"):
            tag = "MIN"
            num_text = tok[1:]
        v = to_float(num_text)
        if v is None:
            return None
        values.append(v)
        tags.append(tag)
    return values, tags


# -------------------------
# Section detection helpers
# -------------------------
def is_section_header(line: str) -> bool:
    return "Flatness Measurement" in line

def is_section_measured(line: str) -> bool:
    return ("Measured Value" in line) and ("[mm/M]" in line)

def is_section_result(line: str) -> bool:
    """
    Detect the start of any Result section.
    Examples: 'Result (Minimal Region)', 'Result (3 Corner Zero)', etc.
    """
    low = line.lower()
    return ("result" in low) and ("[um]" in low)


# -------------------------
# Hàm parse chính
# -------------------------
def parse_record(lines: list[str], pdf_path: str, record_name: str) -> Record:
    """
    Parse toàn bộ file (danh sách lines) và trả về Record.
    Lưu ý: hàm cố gắng parse best-effort, gom warnings/errors vào rec.warnings / rec.errors.
    """
    rec = Record(
        record_id = str(uuid.uuid4()),
        record_name = record_name,
        source_pdf = os.path.basename(pdf_path)
    )

    STATE_NONE = "NONE"
    STATE_HEADER = "HEADER"
    STATE_MEASURED = "MEASURED"
    STATE_RESULT = "RESULT"
    state = STATE_NONE

    # Pending accumulation for RESULT rows that are split across multiple lines
    pending_result_y: Optional[int] = None
    pending_result_vals: List[float] = []
    pending_result_tags: List[str] = []
    # Track which column group we're currently reading (for multi-section columns)
    current_col_offset: int = 0

    for i, line in enumerate(lines):
        # chuyển state dựa trên tiêu đề
        if is_section_header(line):
            state = STATE_HEADER
            continue
        if is_section_measured(line):
            state = STATE_MEASURED
            # reset measured cols (an toàn nếu phần measured xuất hiện nhiều lần)
            rec.measured.cols = []
            continue
        if is_section_result(line):
            state = STATE_RESULT
            # Reset the entire result grid when entering Minimal Region section
            # to avoid mixing with other result sections.
            rec.result.cols = []
            rec.result.rows = []
            rec.result.values.clear()
            rec.result.tags.clear()
            # also clear any pending accumulation state
            pending_result_y = None
            pending_result_vals = []
            pending_result_tags = []
            current_col_offset = 0
            continue

        # xử lý theo state
        if state == STATE_HEADER:
            # ----- 1) Nếu dòng dạng "Key : Value" -----
            if ":" in line:
                key_part, val_part = line.split(":", 1)
                k = normalize_key(key_part)
                v = val_part.strip()
                rec.header[k] = v

                # Map các field chuẩn
                if k == "saved_date":
                    rec.saved_date = v
                elif k == "work_name":
                    rec.work_name = v
                elif k == "work_number":
                    rec.work_number = v
                elif k == "operator":
                    rec.operator = v
                elif k == "comments":
                    rec.comments = v
                elif k in ("total_crosswise_measurement_length", "total_crosswise_length", "total_crosswise_measurement_length ="):
                    # giữ raw
                    rec.header["total_crosswise_length_raw"] = v
                    parsed = parse_total_length_line_value(v)
                    if parsed:
                        rec.header["total_crosswise_full"] = parsed["raw"]
                        rec.crosswise_total_mm = parsed["total_mm"]
                        rec.header["crosswise_segment_mm"] = parsed["segment_mm"]
                        rec.header["crosswise_segments_count"] = parsed["segments_count"]
                elif k in ("total_lengthwise_measurement_length", "total_lengthwise_length", "total_lengthwise_measurement_length ="):
                    rec.header["total_lengthwise_length_raw"] = v
                    parsed = parse_total_length_line_value(v)
                    if parsed:
                        rec.header["total_lengthwise_full"] = parsed["raw"]
                        rec.lengthwise_total_mm = parsed["total_mm"]
                        rec.header["lengthwise_segment_mm"] = parsed["segment_mm"]
                        rec.header["lengthwise_segments_count"] = parsed["segments_count"]
                # đã xử lý dòng có ':' xong, chuyển sang dòng tiếp theo
                continue
            # ----- 2) Nếu dòng KHÔNG có ':' nhưng chứa text Total crosswise/lengthwise -----
            # Ví dụ: "Total crosswise measurement length = 450[mm] ( 150[mm] * 3 )"
            low = line.lower()
            if "total crosswise" in low or "total lengthwise" in low:
                parsed = parse_total_length_line_value(line)
                if parsed:
                    if "total crosswise" in low:
                        rec.header["total_crosswise_length_raw"] = parsed["raw"]
                        rec.header["total_crosswise_full"] = parsed["raw"]
                        rec.crosswise_total_mm = parsed["total_mm"]
                        rec.header["crosswise_segment_mm"] = parsed["segment_mm"]
                        rec.header["crosswise_segments_count"] = parsed["segments_count"]
                    if "total lengthwise" in low:
                        rec.header["total_lengthwise_length_raw"] = parsed["raw"]
                        rec.header["total_lengthwise_full"] = parsed["raw"]
                        rec.lengthwise_total_mm = parsed["total_mm"]
                        rec.header["lengthwise_segment_mm"] = parsed["segment_mm"]
                        rec.header["lengthwise_segments_count"] = parsed["segments_count"]
                # dù có parse được hay không, bỏ qua dòng này
                continue

            # một số file ghi Flatness/Maximum Offset như một dòng không có ":" -> parse số
            if ("[um]" in line) and ("Flatness" in line or "Maximum Offset" in line or "maximum offset" in line.lower()):
                f = first_number_in_text(line)
                if f is not None:
                    rec.flatness_um = f
                continue

        elif state == STATE_MEASURED:
            # MEASURED parsing is disabled - only extract header info if needed
            # Skip all measured rows for now
            continue

        elif state == STATE_RESULT:
            # Tìm header cột: có thể xuất hiện nhiều nhóm như [00]..[09], rồi [10]..[19], v.v.
            cols = find_all_column_indexes(line)
            if cols:
                # Append any new column indices (keep order, ensure uniqueness)
                for c in cols:
                    if c not in rec.result.cols:
                        rec.result.cols.append(c)
                # Update current column offset to the first column in this group
                current_col_offset = cols[0]
                continue

            # First, try to parse a normal Y[...] line
            parsed = parse_result_row(line)
            if parsed is not None:
                y_index, values, tags = parsed
                # If first column is not [00] but we have extra values, prepend [00]
                if len(values) == len(rec.result.cols) + 1 and rec.result.cols and rec.result.cols[0] != 0:
                    rec.result.cols.insert(0, 0)
                    current_col_offset = 0
                # Add Y to rows list if not already there
                if y_index not in rec.result.rows:
                    rec.result.rows.append(y_index)
                # Store values using current column offset
                for j, val in enumerate(values):
                    x_col = current_col_offset + j
                    if x_col in rec.result.cols:
                        rec.result.values[(y_index, x_col)] = val
                        rec.result.tags[(y_index, x_col)] = tags[j] if j < len(tags) else ""
                continue

    # cuối cùng: kiểm tra cơ bản
    if not rec.result.cols:
        rec.errors.append("RESULT: missing column header.")
    if len(rec.result.rows) == 0:
        rec.errors.append("RESULT: no rows parsed.")

    return rec
