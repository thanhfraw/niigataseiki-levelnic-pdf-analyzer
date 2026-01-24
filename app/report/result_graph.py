# Copyright © 2026 Nhat Viet Industrial Co., Ltd.
# All rights reserved.
#
# This software is proprietary and confidential.
# Unauthorized copying, modification, or distribution is strictly prohibited.

# app/report/result_graph.py
"""
Module: Result Heatmap Graph Generator
Task: Generate result-value heatmap visualization from Record data
Description: Generates a result-value heatmap image (matplotlib) from Record data

Public function:
- generate_result_graph(rec, out_path, figsize=(8,6), dpi=150, cmap='coolwarm', annotate=True)
  Creates and saves a heatmap visualization of result values

Tác vụ: Tạo bản đồ nhiệt từ dữ liệu kết quả đo
Mô tả: Tạo hình ảnh bản đồ nhiệt từ dữ liệu result bằng matplotlib
"""

from typing import Any, Tuple, Optional
import os
import math
from pathlib import Path

def _to_float_safe(v) -> Optional[float]:
    """
    Try converting v to float, return None on failure or if v is None/empty.
    
    Cố gắng chuyển đổi v thành float, trả về None nếu thất bại hoặc v là None/rỗng.
    """
    try:
        if isinstance(v, str):
            vs = v.strip().replace(",", "")
            if vs == "":
                return None
            return float(vs)
        return float(v)
    except Exception:
        return None

def generate_result_graph(
    rec: Any,
    out_path: str,
    figsize: Tuple[float,float]=(8,6),
    dpi: int = 150,
    cmap: str = "coolwarm",
    annotate: bool = True,
    nan_color: str = "#dcdcdc"
) -> str:
    """
    Create and save a heatmap of rec.result.

    Returns out_path on success.
    Raises ValueError if no numeric data, ImportError if matplotlib/numpy missing.
    """
    try:
        import numpy as np
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import pandas as pd
    except Exception as e:
        raise ImportError("numpy, pandas and matplotlib are required: pip install numpy pandas matplotlib") from e

    cols = list(getattr(rec.result, "cols", []) or [])
    rows = list(getattr(rec.result, "rows", []) or [])

    if not cols or not rows:
        raise ValueError("No result rows/cols available to plot.")

    # keep order as provided
    n_rows = len(rows)
    n_cols = len(cols)

    # build matrix with NaN for missing
    mat = np.full((n_rows, n_cols), np.nan, dtype=float)
    for i, y in enumerate(rows):
        for j, x in enumerate(cols):
            raw = rec.result.values.get((y, x), None)
            f = _to_float_safe(raw)
            if f is not None and (not (isinstance(f, float) and (math.isnan(f) or math.isinf(f)))):
                mat[i, j] = f

    # check if any numeric
    if np.all(np.isnan(mat)):
        raise ValueError("No numeric result values found to plot.")

    # --- Read step sizes from header (database) ---
    try:
        project_root = Path(__file__).parent.parent.parent
        header_path = project_root / "output_data" / "data_header.csv"
        header_df = pd.read_csv(header_path)
        header = {str(k).strip(): v for k, v in zip(header_df['key'], header_df['value'])}
        cross_segment_mm = float(header.get("crosswise_segment_mm", 0))
        length_segment_mm = float(header.get("lengthwise_segment_mm", 0))
    except Exception:
        cross_segment_mm = 0.0
        length_segment_mm = 0.0

    # prepare 2D grid plot (no heatmap)
    fig = plt.figure(figsize=figsize, dpi=dpi)
    ax = fig.add_subplot(111)
    # Build cells from points: with n_cols x n_rows points, cells are (n_cols-1) x (n_rows-1)
    grid_w = max(n_cols - 1, 1)
    grid_h = max(n_rows - 1, 1)
    right_margin = 0.5
    bottom_margin = 0.5
    ax.set_xlim(0, grid_w + right_margin)
    ax.set_ylim(0, grid_h + bottom_margin)
    ax.invert_yaxis()  # make row 0 at top
    ax.set_xticks([])
    ax.set_yticks([])
    # hide default axes frame so no outer border is drawn
    for spine in ax.spines.values():
        spine.set_visible(False)

    # draw cells: light green fill with full outer border; internal grid lines green
    cell_face = "#d8f0d8"
    outer_color = "#3366cc"
    inner_color = "#2e7d32"

    # fill background for the cell area only
    ax.add_patch(mpatches.Rectangle((0, 0), grid_w, grid_h, fill=True, facecolor=cell_face, edgecolor='none'))
    # outer border (all four sides around the cell area)
    ax.plot([0, grid_w], [0, 0], color=outer_color, linewidth=2.0)           # top
    ax.plot([0, grid_w], [grid_h, grid_h], color=outer_color, linewidth=2.0) # bottom
    ax.plot([0, 0], [0, grid_h], color=outer_color, linewidth=2.0)           # left
    ax.plot([grid_w, grid_w], [0, grid_h], color=outer_color, linewidth=2.0) # right

    # internal vertical lines (exclude rightmost border)
    for j in range(1, grid_w):
        ax.plot([j, j], [0, grid_h], color=inner_color, linewidth=2.0)
    # internal horizontal lines (exclude bottom border)
    for i in range(1, grid_h):
        ax.plot([0, grid_w], [i, i], color=inner_color, linewidth=2.0)

    # annotate values at grid points (n_rows x n_cols), top-left aligned with small padding
    mask = np.isnan(mat)
    valid_vals = mat[~mask]
    vmin = float(np.min(valid_vals)) if valid_vals.size else None
    vmax = float(np.max(valid_vals)) if valid_vals.size else None

    tags = getattr(rec.result, "tags", {}) or {}
    for i in range(n_rows):
        for j in range(n_cols):
            if mask[i, j]:
                continue
            val = mat[i, j]
            tag = tags.get((rows[i], cols[j]), "")
            s = f"{val:.1f}" if abs(val) >= 1 else f"{val:.2f}"
            color = "red" if (vmin is not None and (val == vmin or val == vmax)) else "black"
            # place near the node point with small padding
            x_pos = min(j, grid_w) + 0.05 if j <= grid_w else grid_w + 0.05
            y_pos = min(i, grid_h) + 0.05 if i <= grid_h else grid_h + 0.05
            ax.text(x_pos, y_pos, s, ha="left", va="top", fontsize=9, color=color)
            if tag:
                ax.text(x_pos, y_pos + 0.5, f"({tag})", ha="left", va="top", fontsize=8, color="#FF0000")

    # axis labels and step sizes
        ax.text(-0.1, grid_h/2, f"Y(mm)\nStep Size = {length_segment_mm:.0f}" if length_segment_mm else "Y(mm)",
            ha="right", va="center", fontsize=9)
        ax.text(grid_w/2, grid_h + 1, f"X(mm)\nStep Size = {cross_segment_mm:.0f}" if cross_segment_mm else "X(mm)",
            ha="center", va="bottom", fontsize=9)
        ax.text(-0.6, grid_h + 0.6, "Z(µm)", ha="left", va="bottom", fontsize=9)

    fig.tight_layout()

    # ensure output dir exists
    out_dir = os.path.dirname(out_path) or "."
    os.makedirs(out_dir, exist_ok=True)

    try:
        plt.savefig(out_path, dpi=dpi)
    finally:
        plt.close()

    return out_path
