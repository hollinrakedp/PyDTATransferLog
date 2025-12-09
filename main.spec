# -*- mode: python ; coding: utf-8 -*-
import sys

# Platform detection
IS_WINDOWS = sys.platform.startswith('win')
IS_LINUX = sys.platform.startswith('linux')
IS_MACOS = sys.platform.startswith('darwin')

# Platform-specific configurations
ICON_FILE = ['src/resources/icons/dtatransferlog.ico'] if IS_WINDOWS else None
VERSION_FILE = 'version.txt' if IS_WINDOWS else None
CONSOLE_MODE = not IS_WINDOWS  # Linux/Mac: console=True, Windows: console=False

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/config.ini', '.'),
        ('src/resources', 'resources'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

# Main executable
# On Windows: GUI version (windowed, no console)
# On Linux/Unix: Single executable with console support
exe_main = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='dtatransferlog',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=CONSOLE_MODE,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON_FILE,
    version=VERSION_FILE
)

# CLI Version (Windows only)
# On Windows, we need a separate CLI executable because the GUI version 
# cannot display output in terminal windows when console=False
if IS_WINDOWS:
    exe_cli = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name='dtatransferlog-cli',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=True,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=ICON_FILE,
        version=VERSION_FILE
    )
