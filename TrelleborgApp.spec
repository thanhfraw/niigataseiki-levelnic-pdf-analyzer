# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

# Find PySide6 package path
try:
    import PySide6
    pyside6_path = os.path.dirname(PySide6.__file__)
except ImportError:
    pyside6_path = None

# Collect PySide6 data and binaries manually if available
pyside6_datas = []
pyside6_binaries = []

if pyside6_path:
    # Add PySide6 and its plugins/translations
    pyside6_datas.append((pyside6_path, 'PySide6'))

# Include templates folder with sample template files
templates_data = [('templates', 'templates')]
# Include app/image folder with GUI images
images_data = [('app/image', 'app/image')]

a = Analysis(
    ['app\\gui.py'],
    pathex=[],
    binaries=pyside6_binaries,
    datas=pyside6_datas + templates_data + images_data,
    hiddenimports=[
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtSvg',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],  # Move binaries and datas to COLLECT
    exclude_binaries=True,  # Add this line
    name='TrelleborgApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['app\\image\\icon.ico'],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TrelleborgApp',
)
