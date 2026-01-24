# Copyright © 2026 Nhat Viet Industrial Co., Ltd.
# All rights reserved.
#
# This software is proprietary and confidential.
# Unauthorized copying, modification, or distribution is strictly prohibited.

# app/extractor.py
"""
Module: PDF Text Extractor
Task: Extract and clean text lines from PDF files
Description: Extracts and cleans text lines from PDF files using pdfplumber

Tác vụ: Đọc PDF và trích xuất text
Mô tả: Đọc file PDF, trích xuất text, và loại bỏ khoảng trắng thừa
"""

import re
import pdfplumber


def clean_line(s: str) -> str:
    """
    Remove extra whitespace, normalize multiple spaces to single space.
    
    Xoá khoảng trắng thừa, gom nhiều space thành 1 space.
    """
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s


def extract_lines(pdf_path: str) -> list[str]:
    """
    Read PDF and return a list of cleaned text lines.
    
    Đọc PDF và trả về danh sách dòng text đã clean.
    """
    all_lines: list[str] = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            for raw_line in text.splitlines():
                line = clean_line(raw_line)
                if line != "":
                    all_lines.append(line)

    return all_lines
