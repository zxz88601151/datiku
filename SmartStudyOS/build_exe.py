# © 中哥  All Rights Reserved
# 版权标识: FP_UUID_31adb5871aea40b8b0c288773f094ab2|FP_AUTHOR_中哥_SN_20260531|FP_HASH_20260531B9F3|FP_ORIGIN_2026_AUTHOR_中哥
# 仅限项目内部使用，未经授权禁止转载、商用。

"""SmartStudy OS PyInstaller 构建脚本。

用法：
    python build_exe.py

生成：
    dist/SmartStudyOS/SmartStudyOS.exe
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# 构建命令
# 使用系统 Python（预装了 PyInstaller + PySide6）
_PY = r"C:\Users\zxz\AppData\Local\Microsoft\WindowsApps\python.exe"

cmd = [
    _PY, "-m", "PyInstaller",
    "--windowed",                          # GUI 模式，不显示控制台
    "--name", "SmartStudyOS",
    "--add-data", f"resource{';'}resource",  # 知识树 + 种子数据 + 盐城数据
    "--add-data", f"config{';'}config",      # 配置文件
    "--hidden-import", "PySide6.QtCore",
    "--hidden-import", "PySide6.QtWidgets",
    "--hidden-import", "PySide6.QtGui",
    "--hidden-import", "PySide6.QtSvg",
    "--collect-submodules", "core",
    "--collect-submodules", "ui",
    "--collect-submodules", "services",
    "--collect-submodules", "database",
    "--collect-submodules", "utils",
    "--noconfirm",                          # 覆盖已有输出
    "--clean",
    str(ROOT / "main.py"),
]

print("=" * 60)
print("SmartStudy OS — EXE 构建")
print("=" * 60)
print(f"Python: {sys.executable}")
print(f"工作目录: {ROOT}")
print(f"命令行:")
print("  " + " ".join(str(c) for c in cmd))
print()

ret = subprocess.run(cmd, cwd=ROOT)
if ret.returncode == 0:
    print("\n✅ 构建成功！")
    exe_path = ROOT / "dist" / "SmartStudyOS"
    print(f"  输出目录: {exe_path}")
    print(f"  启动:双击 {exe_path / 'SmartStudyOS.exe'}")
else:
    print(f"\n❌ 构建失败 (code={ret.returncode})")
    sys.exit(ret.returncode)
