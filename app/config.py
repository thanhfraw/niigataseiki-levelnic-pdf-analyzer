# Copyright © 2026 Nhat Viet Industrial Co., Ltd.
# All rights reserved.
#
# This software is proprietary and confidential.
# Unauthorized copying, modification, or distribution is strictly prohibited.

# app/config.py
"""
Module: Application Configuration Manager
Task: Manage application settings and persistent configuration
Description: Handles config file storage and retrieval for user preferences

Tác vụ: Quản lý cài đặt ứng dụng
Mô tả: Xử lý lưu trữ và đọc file config cho preferences của người dùng
"""

import os
import json
from pathlib import Path
from typing import Optional

def get_config_dir(app_name: str = "pdf_to_csv") -> Path:
    """
    Get application config directory.
    Creates ~/.config/pdf_to_csv/ on Unix-like systems
    Creates %APPDATA%\\pdf_to_csv\\ on Windows
    Falls back to ~/.pdf_to_csv/ if needed
    
    Args:
        app_name: Name of the application for config directory
    
    Returns:
        Path object pointing to config directory
    
    Lấy thư mục config của ứng dụng.
    Tạo ~/.config/pdf_to_csv/ trên Unix-like systems
    Tạo %APPDATA%\\pdf_to_csv\\ trên Windows
    Fallback về ~/.pdf_to_csv/ nếu cần
    
    Tham số:
        app_name: Tên ứng dụng cho thư mục config
    
    Trả về:
        Đối tượng Path trỏ đến thư mục config
    """
    # Try using ~/.config/app_name/ (Unix-like convention, works on Windows too)
    if os.name == 'nt':  # Windows
        # Use %APPDATA%\app_name\ if available
        appdata = os.getenv('APPDATA')
        if appdata:
            config_dir = Path(appdata) / app_name
        else:
            config_dir = Path.home() / ".config" / app_name
    else:  # Unix-like (Linux, macOS)
        config_dir = Path.home() / ".config" / app_name
    
    # Create directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

class Config:
    def __init__(self, filename: str = "app_config.json", app_name: str = "pdf_to_csv"):
        self.path = get_config_dir(app_name) / filename

    def _read(self):
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write(self, data):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    def get_last_open_dir(self) -> Optional[str]:
        d = self._read()
        v = d.get("last_open_dir")
        if v and os.path.isdir(v):
            return v
        return None

    def set_last_open_dir(self, path: str):
        d = self._read()
        d["last_open_dir"] = path
        self._write(d)

    def get_last_report_dir(self) -> Optional[str]:
        d = self._read()
        v = d.get("last_report_dir")
        if v and os.path.isdir(v):
            return v
        return None

    def set_last_report_dir(self, path: str):
        d = self._read()
        d["last_report_dir"] = path
        self._write(d)

    def get_last_template(self) -> Optional[str]:
        d = self._read()
        v = d.get("last_template")
        if v and os.path.exists(v):
            return v
        return None

    def set_last_template(self, path: str):
        d = self._read()
        d["last_template"] = path
        self._write(d)

    def clear_last_template(self):
        """Clear the saved template from config."""
        d = self._read()
        if "last_template" in d:
            del d["last_template"]
        self._write(d)

    # Recent files helpers
    def get_recent_files(self, limit: int = 10):
        d = self._read()
        files = d.get("recent_files", [])
        # keep only existing paths
        cleaned = [p for p in files if os.path.exists(p)]
        return cleaned[:limit]

    def add_recent_file(self, path: str, max_items: int = 10):
        if not path:
            return
        d = self._read()
        files = d.get("recent_files", [])
        # move to front and drop duplicates
        files = [p for p in files if p != path]
        files.insert(0, path)
        d["recent_files"] = files[:max_items]
        self._write(d)
