# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['compiler.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'antlr4',
        'antlr4.atn',
        'antlr4.error',
        'antlr_generated',
        'antlr_generated.MiniRLexer',
        'antlr_generated.MiniRParser',
        'antlr_generated.MiniRVisitor',
        'antlr_generated.MiniRListener',
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
    a.binaries,
    a.datas,
    [],
    name='compiler',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
