# Copyright © 2026 Nhat Viet Industrial Co., Ltd.
# All rights reserved.
#
# This software is proprietary and confidential.
# Unauthorized copying, modification, or distribution is strictly prohibited.

# app/models.py
"""
Module: Data Models
Task: Define core data structures for record storage
Description: Defines core data structures (Record, MeasuredGrid, ResultGrid)

Tác vụ: Định nghĩa các lớp dữ liệu chính
Mô tả: Chứa các class model cho Record, MeasuredGrid, ResultGrid
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional


@dataclass
class MeasuredGrid:
    cols: List[int] = field(default_factory=list)
    rows: List[Tuple[str, int]] = field(default_factory=list)  # ("X",1), ("Y",2)...
    values: Dict[Tuple[str, int, int], float] = field(default_factory=dict)  # (axis,row,col)->value


@dataclass
class ResultGrid:
    cols: List[int] = field(default_factory=list)
    rows: List[int] = field(default_factory=list)  # y indices
    values: Dict[Tuple[int, int], float] = field(default_factory=dict)  # (y,x)->value
    tags: Dict[Tuple[int, int], str] = field(default_factory=dict)  # (y,x)->"MAX"/"MIN"/""


@dataclass
class Record:
    record_id: str
    record_name: str
    source_pdf: str

    header: Dict[str, str] = field(default_factory=dict)

    # parsed/normalized fields (best-effort)
    saved_date: Optional[str] = None
    work_name: Optional[str] = None
    work_number: Optional[str] = None
    operator: Optional[str] = None
    comments: Optional[str] = None

    crosswise_total_mm: Optional[float] = None
    lengthwise_total_mm: Optional[float] = None
    flatness_um: Optional[float] = None

    measured: MeasuredGrid = field(default_factory=MeasuredGrid)
    result: ResultGrid = field(default_factory=ResultGrid)

    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def dims(self) -> Dict[str, int]:
        mx = sum(1 for axis, _ in self.measured.rows if axis == "X")
        my = sum(1 for axis, _ in self.measured.rows if axis == "Y")
        return {
            "meas_col_count": len(self.measured.cols),
            "meas_row_count": len(self.measured.rows),
            "meas_x_row_count": mx,
            "meas_y_row_count": my,
            "res_col_count": len(self.result.cols),
            "res_row_count": len(self.result.rows),
        }
