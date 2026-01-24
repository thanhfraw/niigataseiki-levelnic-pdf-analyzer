# Copyright © 2026 Nhat Viet Industrial Co., Ltd.
# All rights reserved.
#
# This software is proprietary and confidential.
# Unauthorized copying, modification, or distribution is strictly prohibited.

# app/utils.py
"""
Module: Utility Functions
Task: Common utility functions for file and folder operations
Description: Provides helper functions for opening folders and ensuring directories exist

Tác vụ: Các hàm tiện ích chung
Mô tả: Cung cấp hàm hỗ trợ mở folder và đảm bảo thư mục tồn tại
"""

import os
import sys
import subprocess

def open_folder(path: str):
    """
    Open folder in system file explorer.
    
    Mở folder trong file explorer của hệ thống.
    """
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])
    except Exception:
        pass

def ensure_dir(path: str):
    """
    Ensure directory exists, create if not exists.
    
    Đảm bảo thư mục tồn tại, tạo nếu chưa có.
    """
    os.makedirs(path, exist_ok=True)
    return path
