# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for JARVIS AI Assistant

import os
import sys
from pathlib import Path

block_cipher = None

# Get the project root directory
project_root = Path(__file__).parent

# Data files to include
added_files = [
    ('Data', 'Data'),
    ('Frontend/Graphics', 'Frontend/Graphics'),
    ('Frontend/Files', 'Frontend/Files'),
    ('Backend', 'Backend'),
]

# Hidden imports (PyInstaller may not detect these automatically)
hiddenimports = [
    'pyaudio',
    'vosk',
    'pvporcupine',
    'pygame',
    'edge_tts',
    'pyttsx3',
    'PyQt5',
    'selenium',
    'groq',
    'dotenv',
    'snowboydecoder',
    'snowboydetect',
]

a = Analysis(
    ['Main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=added_files,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='JARVIS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path if you have one: 'icon.ico'
)

