# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[('opticlab_ui.ui', '.'),('msedgedriver.exe', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['jellyfish', 'pysimmian', 'ollama', 'openai', 'alabaster', 'astroid', 'ipykernel', 'ipython', 'jupyter_client', 'huggingface-hub', 'spyder', 'spyder-kernels', 'tokenizers', 'torch', 'jupyter_core', 'jupyterlab_pygments', 'jupyterlab_widgets', 'clipboard', 'flask', 'ipython', 'conda', 'setuptools', 'transformers', 'Sphinx', 'tornado', 'sentence-transformers', 'netwrokx', 'safetensors', 'ruamel.yaml', 'Rtree', 'rich', 'zstandard', 'yapf', 'trio', 'jedi', 'isort', 'httpx', 'Jinja2', 'cv2', 'skimage'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='OpticLab_SW',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='module_icon.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='OpticLab_SW',
)
