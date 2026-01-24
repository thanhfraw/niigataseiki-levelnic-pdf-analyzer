# Copyright © 2026 Nhat Viet Industrial Co., Ltd.
# All rights reserved.
#
# This software is proprietary and confidential.
# Unauthorized copying, modification, or distribution is strictly prohibited.

# app/report/button_show_flatness.py
"""
Module: Flatness Graph Viewer
Task: Handle and display interactive 3D flatness graph
Description: Handles "Show Flatness" button functionality; displays interactive 3D graph

Tác vụ: Hiển thị biểu đồ 3D độ phẳng
Mô tả: Xử lý nút "Show Flatness" và hiển thị biểu đồ 3D tương tác
"""

from pathlib import Path
from PySide6.QtWidgets import QMessageBox


def compute_z_floor(nx: int, ny: int, base: float = 50.0, step: float = 10.0, base_dim: int = 5) -> float:
    """
    Return a Z floor that grows with grid size; 5x5 stays at base.
    
    Trả về Z floor tăng theo kích thước lưới; 5x5 giữ ở base.
    """
    max_dim = max(nx, ny)
    if max_dim <= base_dim:
        return base
    return base + step * (max_dim - base_dim)


def show_flatness_graph(current_record):
    """
    Generate and display interactive 3D flatness graph.
    
    Args:
        current_record: The current parsed record object
        
    Returns:
        None (displays graph via matplotlib)
    
    Tạo và hiển thị biểu đồ 3D độ phẳng tương tác.
    
    Tham số:
        current_record: Đối tượng record đã parse
        
    Trả về:
        None (hiển thị biểu đồ qua matplotlib)
    """
    if not current_record:
        QMessageBox.warning(None, "No data", "Import a PDF first.")
        return

    try:
        # Generate interactive 3D visualization directly
        import pandas as pd
        import numpy as np
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D
        
        # Get data files
        project_root = Path(__file__).parent.parent.parent
        data_dir = project_root / "output_data"
        header_path = data_dir / "data_header.csv"
        result_path = data_dir / "data_result.csv"
        
        if not header_path.exists() or not result_path.exists():
            QMessageBox.warning(None, "No data", "Please export data first before viewing 3D flatness graph.")
            return
        
        # --- Read header data ---
        header_df = pd.read_csv(header_path)
        header = {str(k).strip(): v for k, v in zip(header_df['key'], header_df['value'])}
        
        cross_total = float(header.get("crosswise_total_mm", 1))
        length_total = float(header.get("lengthwise_total_mm", 1))
        cross_count = int(float(header.get("crosswise_segments_count", 1)))
        length_count = int(float(header.get("lengthwise_segments_count", 1)))
        cross_segment_mm = float(header.get("crosswise_segment_mm", cross_total / cross_count if cross_count > 0 else 1))
        length_segment_mm = float(header.get("lengthwise_segment_mm", length_total / length_count if length_count > 0 else 1))
        
        # Calculate grid dimensions
        nx = cross_count + 1
        ny = length_count + 1
        
        # --- Read result data ---
        res_df = pd.read_csv(result_path)
        
        # Reshape result data into grid
        if 'y' in res_df.columns and 'x' in res_df.columns and 'value_um' in res_df.columns:
            Z = res_df.pivot_table(
                index='y',
                columns='x',
                values='value_um',
                aggfunc='first'
            ).to_numpy(dtype=float)
        else:
            flat = res_df.select_dtypes(include=[np.number]).to_numpy().ravel()
            Z = flat[:ny * nx].reshape((ny, nx))
        
        # Validate grid dimensions
        if Z.shape != (ny, nx):
            QMessageBox.warning(None, "Data error", f"Grid dimension mismatch. Expected ({ny}, {nx}), got {Z.shape}")
            return
        
        # --- Build coordinate grids ---
        x = np.linspace(0, cross_total, nx)
        y = np.linspace(length_total, 0, ny)  # Reversed Y-axis
        X, Y = np.meshgrid(x, y)
        
        # --- Create interactive 3D plot ---
        fig = plt.figure(figsize=(10, 6))
        ax = fig.add_subplot(111, projection="3d")
        # Maximize the window (Qt backends) and remove margins
        try:
            plt.get_current_fig_manager().window.showMaximized()
        except Exception:
            pass
        fig.patch.set_visible(False)
        fig.subplots_adjust(left=0, right=1, top=1, bottom=0, wspace=0, hspace=0)
        ax.set_position([0, 0, 1, 1])
        
        # Plot reference plane at Z = 0 FIRST (so it doesn't cover other elements)
        Z_plane = np.zeros_like(X)
        plane = ax.plot_surface(X, Y, Z_plane, alpha=0.18, color="#f3f3f3")
        
        # Plot surface and wireframe
        ax.plot_surface(X, Y, Z, alpha=0, color='steelblue')
        ax.plot_wireframe(X, Y, Z, linewidth=1, alpha=0, color='gray')
        
        # Draw connecting lines between adjacent points
        # Horizontal lines (along X-axis / crosswise)
        for j in range(ny):
            ax.plot(x, np.full_like(x, y[j]), Z[j, :], color='black', linewidth=1.3, alpha=1.0)
        
        # Vertical lines (along Y-axis / lengthwise)
        for i in range(nx):
            ax.plot(np.full_like(y, x[i]), y, Z[:, i], color='black', linewidth=1.2, alpha=1.0)
        
        # Draw 16 scatter points
        ax.scatter(X.ravel(), Y.ravel(), Z.ravel(), color='black', s=5, alpha=1.0)
        
        # Draw projection lines from each point to Z=0 plane
        for i in range(nx):
            for j in range(ny):
                ax.plot([X[j, i], X[j, i]], [Y[j, i], Y[j, i]], [Z[j, i], 0], 
                        color='red', linewidth=0.5, alpha=0.7)

        # Draw dashed border lines on Z = 0 plane (4 edges)
        # Bottom edge (y = length_total)
        ax.plot([0, cross_total], [0, 0], [0, 0], color='black', linewidth=0.5, alpha=0.5, linestyle='--')
        # Top edge (y = 0)
        ax.plot([0, cross_total], [length_total, length_total], [0, 0], color='black', linewidth=0.5, alpha=0.5, linestyle='--')
        # Left edge (x = 0)
        ax.plot([0, 0], [0, length_total], [0, 0], color='black', linewidth=0.5, alpha=0.5, linestyle='--')
        # Right edge (x = cross_total)
        ax.plot([cross_total, cross_total], [0, length_total], [0, 0], color='black', linewidth=0.5, alpha=0.5, linestyle='--')
        
        # Draw dashed grid lines on Z = 0 plane based on segment sizes
        # Vertical lines (along lengthwise, spaced by crosswise_segment_mm)
        for i in range(1, cross_count):
            x_pos = i * cross_segment_mm
            ax.plot([x_pos, x_pos], [0, length_total], [0, 0], color='black', linewidth=0.5, alpha=0.5, linestyle='--')
        
        # Horizontal lines (along crosswise, spaced by lengthwise_segment_mm)
        for j in range(1, length_count):
            y_pos = j * length_segment_mm
            ax.plot([0, cross_total], [y_pos, y_pos], [0, 0], color='black', linewidth=0.5, alpha=0.5, linestyle='--')

        # Toggle Z=0 plane visibility with a key (p)
        def on_key(event):
            if event.key and event.key.lower() == 'p':
                plane.set_visible(not plane.get_visible())
                fig.canvas.draw_idle()

        fig.canvas.mpl_connect('key_press_event', on_key)
        # On-figure hint for the toggle
        fig.text(0.02, 0.02, "Press 'P' to toggle Z=0 plane", fontsize=9, color='gray')

        # peak-to-peak (max - min)
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
        
        # Show interactive 3D viewer
        plt.show()
        
    except ImportError as e:
        QMessageBox.critical(None, "Missing library", f"Required library missing:\n{e}")
    except Exception as e:
        QMessageBox.critical(None, "Graph error", f"Failed to generate 3D flatness graph:\n{e}")
