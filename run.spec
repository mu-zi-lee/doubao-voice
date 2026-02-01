# PyInstaller spec：单 exe，内嵌 web 静态。
# 用法: pyinstaller run.spec
# 需先安装: uv add --dev pyinstaller 或 pip install pyinstaller
a = Analysis(
    ["run.py"],
    pathex=[],
    datas=[("web", "web")],
    hiddenimports=["uvicorn.logging", "uvicorn.loops", "uvicorn.loops.auto", "uvicorn.protocols", "uvicorn.protocols.http", "uvicorn.protocols.http.auto", "uvicorn.protocols.websockets", "uvicorn.protocols.websockets.auto", "uvicorn.lifespan", "uvicorn.lifespan.on"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="doubao-voice", debug=False, bootloader_ignore_signals=False, strip=False, upx=True, console=True)
