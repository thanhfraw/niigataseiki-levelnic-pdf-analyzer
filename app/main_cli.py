# Copyright © 2026 Nhat Viet Industrial Co., Ltd.
# All rights reserved.
#
# This software is proprietary and confidential.
# Unauthorized copying, modification, or distribution is strictly prohibited.

# app/main_cli.py
"""
Module: Command-Line Interface
Task: Process PDFs from command-line with arguments
Description: CLI entry point for processing PDFs with arguments

Tác vụ: Xử lý PDF từ dòng lệnh
Mô tả: Điểm vào CLI để xử lý PDF với các tham số đầu vào
"""

import argparse
import os
import sys

from .extractor import extract_lines
from .parser import parse_record
from .storage import save_to_database_csv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--out", required=True)

    args = parser.parse_args()

    if not os.path.exists(args.pdf):
        print("PDF not found:", args.pdf)
        return 1

    lines = extract_lines(args.pdf)
    rec = parse_record(lines, pdf_path=args.pdf, record_name=args.name)

    # In kết quả để kiểm tra
    print("Record ID:", rec.record_id)
    print("Flatness (um):", rec.flatness_um)
    print("Measured cols:", len(rec.measured.cols), "rows:", len(rec.measured.rows))
    print("Result cols:", len(rec.result.cols), "rows:", len(rec.result.rows))

    if rec.warnings:
        print("\nWarnings:")
        for w in rec.warnings:
            print("-", w)

    if rec.errors:
        print("\nErrors:")
        for e in rec.errors:
            print("-", e)
        print("\nKhông export CSV vì có lỗi parse.")
        return 1

    save_to_database_csv(rec, args.out)
    print("\nExport xong 3 CSV vào:", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
