# Copyright © 2026 Nhat Viet Industrial Co., Ltd.
# All rights reserved.
#
# This software is proprietary and confidential.
# Unauthorized copying, modification, or distribution is strictly prohibited.

# app/report/flatness_graph.py
"""
Module: 3D Flatness Graph Generator
Task: Create 3D surface plot from flatness measurement data
Description: Creates 3D surface plot from flatness measurement data using matplotlib

Tác vụ: Tạo biểu đồ 3D từ dữ liệu độ phẳng
Mô tả: Tạo biểu đồ surface 3D từ dữ liệu đo độ phẳng bằng matplotlib
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pathlib import Path
from PIL import Image


def compute_z_floor(nx: int, ny: int, base: float = 50.0, step: float = 10.0, base_dim: int = 5) -> float:
    """
    Compute a minimum Z range that scales up with grid size.

    Keeps 5x5 at ``base`` and grows linearly by ``step`` per extra cell on
    the larger dimension so dense grids do not look too flat.
    
    Tính toán phạm vi Z tối thiểu tăng theo kích thước lưới.

    Giữ 5x5 ở ``base`` và tăng tuyến tính ``step`` cho mỗi ô thêm trên
    chiều lớn hơn để lưới dày không trông quá phẳng.
    """
    max_dim = max(nx, ny)
    if max_dim <= base_dim:
        return base
    return base + step * (max_dim - base_dim)

def generate_flatness_graph(rec, out_path: str):
    """
    Generate a 3D surface plot of flatness measurements.
    
    Args:
        rec: Record object containing file paths
        out_path: Output path for saving the graph
    
    Raises:
        FileNotFoundError: If data files are not found
        ValueError: If data structure is invalid
    
    Tạo biểu đồ bề mặt 3D của các phép đo độ phẳng.
    
    Tham số:
        rec: Đối tượng Record chứa đường dẫn file
        out_path: Đường dẫn đầu ra để lưu biểu đồ
    
    Ngoại lệ:
        FileNotFoundError: Nếu không tìm thấy file dữ liệu
        ValueError: Nếu cấu trúc dữ liệu không hợp lệ
    """
    # Get the base directory for data files (output_data)
    # Use os.getcwd() to match the same path used by storage.py and reporting.py
    import os
    data_dir = os.path.join(os.getcwd(), "output_data")
    header_path = os.path.join(data_dir, "data_header.csv")
    result_path = os.path.join(data_dir, "data_result.csv")
    
    if not os.path.exists(header_path):
        raise FileNotFoundError(f"Header file not found: {header_path}")
    if not os.path.exists(result_path):
        raise FileNotFoundError(f"Result file not found: {result_path}")
    
    # --- Read header data ---
    header_df = pd.read_csv(header_path)
    header = {str(k).strip(): v for k, v in zip(header_df['key'], header_df['value'])}
    
    try:
        cross_total = float(header["crosswise_total_mm"])
        length_total = float(header["lengthwise_total_mm"])
        cross_count = int(float(header["crosswise_segments_count"]))
        length_count = int(float(header["lengthwise_segments_count"]))
        cross_segment_mm = float(header.get("crosswise_segment_mm", cross_total / cross_count if cross_count > 0 else 1))
        length_segment_mm = float(header.get("lengthwise_segment_mm", length_total / length_count if length_count > 0 else 1))
    except (KeyError, ValueError) as e:
        raise ValueError(f"Missing or invalid header data: {e}")
    
    # --- Read result data ---
    res_df = pd.read_csv(result_path)
    
    # Auto-detect grid dimensions from actual data
    if 'y' in res_df.columns and 'x' in res_df.columns:
        ny = res_df['y'].max() + 1  # max index + 1 = count
        nx = res_df['x'].max() + 1
    else:
        # Fallback to header if columns not found
        nx = cross_count + 1
        ny = length_count + 1
    
    # Reshape result data into grid
    # The data_result.csv has columns: record_id, y, x, value_um, tag
    # We need to create a grid where Z[y, x] = value_um
    
    if 'y' in res_df.columns and 'x' in res_df.columns and 'value_um' in res_df.columns:
        # Pivot table to create grid
        Z = res_df.pivot_table(
            index='y', 
            columns='x', 
            values='value_um',
            aggfunc='first'
        ).to_numpy(dtype=float)
    else:
        # Fallback: try to reshape as flat array
        flat = res_df.select_dtypes(include=[np.number]).to_numpy().ravel()
        Z = flat[:ny * nx].reshape((ny, nx))
    
    # Validate grid dimensions
    if Z.shape != (ny, nx):
        raise ValueError(
            f"Grid dimension mismatch. Expected ({ny}, {nx}), got {Z.shape}"
        )
    
    # --- Build coordinate grids ---
    x = np.linspace(0, cross_total, nx)
    y = np.linspace(length_total, 0, ny)  # Reversed Y-axis
    X, Y = np.meshgrid(x, y)
    
    # --- Create 3D plot (static image) ---
    fig = plt.figure(figsize=(14, 6))
    ax = fig.add_subplot(111, projection="3d")

    # --- Remove all whitespace ---
    fig.patch.set_visible(False)
    fig.subplots_adjust(left=0.5, right=2.5, top=1.5, bottom=0.5, wspace=0.5, hspace=0.5)
    ax.set_position([0, 0, 1, 1])

    # Transparent surfaces (no heatmap)
    ax.plot_surface(X, Y, Z, alpha=0, color='steelblue')
    ax.plot_wireframe(X, Y, Z, linewidth=1, alpha=0, color='gray')

    # Draw connecting lines between adjacent points
    # Horizontal lines (along X-axis / crosswise)
    for j in range(ny):
        ax.plot(x, np.full_like(x, y[j]), Z[j, :], color='black', linewidth=1.3, alpha=1.0)

    # Vertical lines (along Y-axis / lengthwise)
    for i in range(nx):
        ax.plot(np.full_like(y, x[i]), y, Z[:, i], color='black', linewidth=1.2, alpha=1.0)

    # Projection lines from each point to Z=0 plane (red)
    for i in range(nx):
        for j in range(ny):
            ax.plot([X[j, i], X[j, i]], [Y[j, i], Y[j, i]], [Z[j, i], 0],
                    color='red', linewidth=0.5, alpha=0.7)

    # Reference plane at Z = 0 (soft gray)
    Z_plane = np.zeros_like(X)
    ax.plot_surface(X, Y, Z_plane, alpha=0.18, color='#d3d3d3')

    # Dashed border lines on Z = 0 plane (4 edges)
    ax.plot([0, cross_total], [0, 0], [0, 0], color='black', linewidth=0.5, alpha=0.5, linestyle='--')
    ax.plot([0, cross_total], [length_total, length_total], [0, 0], color='black', linewidth=0.5, alpha=0.5, linestyle='--')
    ax.plot([0, 0], [0, length_total], [0, 0], color='black', linewidth=0.5, alpha=0.5, linestyle='--')
    ax.plot([cross_total, cross_total], [0, length_total], [0, 0], color='black', linewidth=0.5, alpha=0.5, linestyle='--')

    # Dashed grid lines on Z = 0 plane based on segment sizes
    for i in range(1, cross_count):
        x_pos = i * cross_segment_mm
        ax.plot([x_pos, x_pos], [0, length_total], [0, 0], color='black', linewidth=0.5, alpha=0.5, linestyle='--')
    for j in range(1, length_count):
        y_pos = j * length_segment_mm
        ax.plot([0, cross_total], [y_pos, y_pos], [0, 0], color='black', linewidth=0.5, alpha=0.5, linestyle='--')

    # Z visual scale (aligned with interactive viewer)
    z_range = np.ptp(Z)
    z_scale_factor = 0.2
    z_min_floor = compute_z_floor(nx, ny)
    ax.set_box_aspect((
        cross_total,
        length_total,
        max(z_min_floor, z_range * z_scale_factor)
    ))

    # Hide axes/ruler
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    ax.xaxis.pane.set_visible(False)
    ax.yaxis.pane.set_visible(False)
    ax.zaxis.pane.set_visible(False)
    ax.grid(False)

    # Customize axes
    ax.set_xlabel("Crosswise (mm)", fontsize=10)
    ax.set_ylabel("Lengthwise (mm)", fontsize=10)
    ax.set_zlabel("Flatness (µm)", fontsize=10)

    # Set viewing angle
    ax.view_init(elev=25, azim=-60)

    # Save figure
    plt.savefig(out_path, dpi=150, bbox_inches=None, pad_inches=0, facecolor='white')
    plt.close()
    
    # Post-process: crop white borders from the saved image
    try:
        img = Image.open(out_path)
        # Convert to RGB if needed
        if img.mode == 'RGBA':
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3])
            img = rgb_img
        
        # Find the bounding box that excludes white pixels (255, 255, 255)
        # Use a slight threshold (250+) to catch near-white pixels
        pixels = np.array(img)
        # Find rows and columns that have non-white pixels
        white_threshold = 250
        non_white = np.any(pixels < white_threshold, axis=2)
        
        rows = np.any(non_white, axis=1)
        cols = np.any(non_white, axis=0)
        
        if rows.any() and cols.any():
            ymin, ymax = np.where(rows)[0][[0, -1]]
            xmin, xmax = np.where(cols)[0][[0, -1]]
            # Add margin around content (in pixels)
            margin = 30
            ymin = max(0, ymin - margin)
            xmin = max(0, xmin - margin)
            ymax = min(img.height - 1, ymax + margin)
            xmax = min(img.width - 1, xmax + margin)
            # Crop and save
            cropped = img.crop((xmin, ymin, xmax + 1, ymax + 1))
            cropped.save(out_path)
    except Exception as e:
        print(f"Warning: Could not crop image: {e}")
    
    print(f"Flatness graph saved to: {out_path}")
