# Copyright © 2026 Nhat Viet Industrial Co., Ltd.
# All rights reserved.
#
# This software is proprietary and confidential.
# Unauthorized copying, modification, or distribution is strictly prohibited.

# app/report/measured_graph.py
"""
Module: Measured Graph Generator
Task: Generate measured-value graphs from Record data
Description: Creates line graphs from measured value data using matplotlib

Public function:
- generate_measured_graph(rec, out_path, figsize=(8,4), dpi=150, show_legend=True)
  Creates and saves a line graph visualization of measured values

Tác vụ: Tạo biểu đồ từ dữ liệu đo được
Mô tả: Tạo biểu đồ đường từ dữ liệu measured bằng matplotlib
"""

from typing import Iterable, Tuple, Dict, Any, Optional
import os

def _to_float_safe(v) -> Optional[float]:
    """
    Try converting v to float, return None on failure or if v is None/empty.
    
    Cố gắng chuyển đổi v thành float, trả về None nếu thất bại hoặc v là None/rỗng.
    """
    if v is None:
        return None
    try:
        # handle strings with commas, spaces
        if isinstance(v, str):
            vs = v.strip().replace(",", "")
            if vs == "":
                return None
            return float(vs)
        return float(v)
    except Exception:
        return None

def generate_measured_graph(rec: Any, out_path: str, figsize: Tuple[float,float]=(9,4), dpi: int=150, show_legend: bool=True) -> str:
    """
    Generate and save a measured-values plot.

    Returns the out_path on success.

    Raises:
        ValueError if there's no numeric data to plot.
        ImportError if matplotlib is not installed.
        Exception for other unexpected failures.

    Tạo và lưu biểu đồ giá trị đo được.

    Trả về out_path nếu thành công.

    Ngoại lệ:
        ValueError nếu không có dữ liệu số để vẽ biểu đồ.
        ImportError nếu matplotlib chưa được cài đặt.
        Exception cho các lỗi không mong muốn khác.
    """
    # lazy import so module import doesn't fail if matplotlib missing until needed
    try:
        import matplotlib.pyplot as plt
    except Exception as e:
        raise ImportError("matplotlib is required to generate graphs. Install with: pip install matplotlib") from e

    # collect structure
    cols = list(getattr(rec.measured, "cols", []) or [])
    rows = list(getattr(rec.measured, "rows", []) or [])

    if not cols or not rows:
        raise ValueError("No measured columns/rows available to plot.")

    # Normalize cols ordering (assume they are numeric-like)
    try:
        cols_sorted = sorted(cols, key=lambda c: float(c))
    except Exception:
        # fallback to original order
        cols_sorted = cols

    plotted_any = False

    plt.figure(figsize=figsize, dpi=dpi)
    ax = plt.gca()
    ax.set_title(f"Measured values — {getattr(rec, 'record_name', '')}")
    ax.set_xlabel("Column")
    ax.set_ylabel("Measured (mm)")

    # group rows by axis for nicer legend labels (optional)
    for (axis, row_index) in rows:
        # gather y-values in the same order as cols_sorted
        ys = []
        xs = []
        for c in cols_sorted:
            raw = rec.measured.values.get((axis, row_index, c), None)
            val = _to_float_safe(raw)
            if val is not None:
                xs.append(c)
                ys.append(val)
        if not xs:
            continue
        plotted_any = True
        label = f"{axis}[{row_index:02d}]"
        # plot as line with markers
        ax.plot(xs, ys, marker="o", linewidth=1.2, markersize=4, label=label)

    if not plotted_any:
        plt.close()
        raise ValueError("No numeric measured values were found to plot.")

    ax.grid(True, which="both", linestyle="--", linewidth=0.5, alpha=0.7)

    if show_legend:
        ax.legend(loc="best", fontsize="small")

    # tight layout and save
    plt.tight_layout()

    # ensure output directory exists
    out_dir = os.path.dirname(out_path) or "."
    os.makedirs(out_dir, exist_ok=True)

    # Save as PNG (format inferred from extension)
    try:
        plt.savefig(out_path, dpi=dpi)
    finally:
        plt.close()

    return out_path
