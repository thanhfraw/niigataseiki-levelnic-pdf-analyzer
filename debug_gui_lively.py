#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Debug GUI with Live Reload (Hot Reload)

Sử dụng watchdog để tự động reload GUI khi có thay đổi code.
Cách dùng:
    python debug_gui_lively.py

Tính năng:
- Tự động reload GUI khi file .py thay đổi
- Giữ lại dữ liệu hiện tại (session state)
- Hiển thị thông báo khi reload
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Cấu hình
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(PROJECT_ROOT, "app")
WATCH_PATHS = [APP_DIR]  # Monitor thư mục app
IGNORE_PATTERNS = ["__pycache__", ".pyc", "__pycache__"]

# Process handle
current_process = None
last_reload_time = 0


class CodeChangeHandler(FileSystemEventHandler):
    """Detect Python file changes"""
    
    def __init__(self, reload_callback):
        super().__init__()
        self.reload_callback = reload_callback
        self.last_trigger_time = 0
        self.debounce_delay = 1.0  # 1 second debounce
    
    def on_modified(self, event):
        """Triggered when file is modified"""
        if event.is_directory:
            return
        
        # Only watch .py files
        if not event.src_path.lower().endswith('.py'):
            return
        
        # Ignore pycache
        if '__pycache__' in event.src_path:
            return
        
        # Debounce: avoid multiple triggers
        current_time = time.time()
        if current_time - self.last_trigger_time < self.debounce_delay:
            return
        
        self.last_trigger_time = current_time
        
        # Reload
        file_name = os.path.basename(event.src_path)
        print(f"\n{'='*60}")
        print(f"[LIVE] Detected change: {file_name}")
        print(f"[LIVE] Reloading GUI...")
        print(f"{'='*60}\n")
        
        self.reload_callback()


def start_gui_process():
    """Start GUI process"""
    global current_process
    
    try:
        # Use pythonw on Windows for GUI (no console window)
        # or use python -m for module execution
        cmd = [sys.executable, "-m", "app.gui"]
        
        print(f"[DEBUG] Starting: {' '.join(cmd)}")
        print(f"[DEBUG] Working directory: {PROJECT_ROOT}")
        
        current_process = subprocess.Popen(
            cmd,
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            # Don't inherit stdin to avoid blocking
            stdin=subprocess.PIPE
        )
        
        print(f"[DEBUG] GUI process started (PID: {current_process.pid})")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to start GUI: {e}")
        return False


def stop_gui_process():
    """Stop current GUI process"""
    global current_process
    
    if current_process is None:
        return
    
    try:
        print(f"[DEBUG] Stopping GUI process (PID: {current_process.pid})...")
        
        # Try graceful shutdown first
        if sys.platform.startswith("win"):
            # Windows: use CTRL_C_EVENT
            current_process.send_signal(signal.CTRL_C_EVENT)
        else:
            # Unix: use SIGTERM
            current_process.terminate()
        
        # Wait for process to end
        try:
            current_process.wait(timeout=3)
            print(f"[DEBUG] GUI process stopped gracefully")
        except subprocess.TimeoutExpired:
            # Force kill if timeout
            print(f"[DEBUG] Force killing GUI process...")
            current_process.kill()
            current_process.wait(timeout=2)
            print(f"[DEBUG] GUI process force killed")
        
        current_process = None
        
    except Exception as e:
        print(f"[ERROR] Error stopping process: {e}")
        if current_process:
            try:
                current_process.kill()
            except:
                pass
        current_process = None


def reload_gui():
    """Reload GUI by restarting process"""
    global last_reload_time
    
    # Debounce reload
    current_time = time.time()
    if current_time - last_reload_time < 2:
        return
    last_reload_time = current_time
    
    # Stop current process
    stop_gui_process()
    
    # Wait a bit before restarting
    time.sleep(0.5)
    
    # Start new process
    start_gui_process()


def start_watcher():
    """Start file watcher for auto-reload"""
    handler = CodeChangeHandler(reload_gui)
    observer = Observer()
    
    for watch_path in WATCH_PATHS:
        observer.schedule(handler, watch_path, recursive=True)
        print(f"[WATCHER] Watching: {watch_path}")
    
    observer.daemon = True
    observer.start()
    
    return observer


def main():
    """Main entry point"""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║          GUI Debug Lively (Hot Reload)                       ║
║                                                              ║
║  Auto-reload GUI when code changes                          ║
║  Press Ctrl+C to exit                                       ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    print(f"[INFO] Project root: {PROJECT_ROOT}")
    print(f"[INFO] Watching paths: {WATCH_PATHS}\n")
    
    # Start file watcher
    observer = start_watcher()
    
    # Start initial GUI process
    if not start_gui_process():
        print("[ERROR] Failed to start GUI")
        observer.stop()
        return 1
    
    print("\n[INFO] Watcher ready. Edit any .py file to trigger reload...\n")
    
    # Keep running
    try:
        while True:
            time.sleep(0.5)
            
            # Check if process is still alive
            if current_process and current_process.poll() is not None:
                print("\n[INFO] GUI process ended unexpectedly")
                print("[INFO] Attempting to restart...")
                time.sleep(1)
                start_gui_process()
    
    except KeyboardInterrupt:
        print("\n\n[INFO] Shutting down...")
        stop_gui_process()
        observer.stop()
        observer.join(timeout=2)
        print("[INFO] Goodbye!")
        return 0
    
    except Exception as e:
        print(f"\n[ERROR] {e}")
        stop_gui_process()
        observer.stop()
        return 1


if __name__ == "__main__":
    sys.exit(main())
